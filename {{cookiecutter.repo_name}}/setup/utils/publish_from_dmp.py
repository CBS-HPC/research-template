#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
publish_from_dmp.py
-------------------
Publish a dataset using metadata extracted from an RDA maDMP (v1.2 JSON)
to either **Zenodo** or **Dataverse** (e.g., DeiC Dataverse).

- Improved Zenodo mapping:
  * creators  = DMP contact (primary author), with ORCID & affiliation (+ ROR best-effort)
  * contributors = DMP contributors (+ optional dataset.contributor), role-mapped, with ORCID & affiliation (+ ROR best-effort)
  * preserves keywords, license, access_right, embargo_date, related_identifiers
  * if dataset_id.type == "doi", it is added as isAlternateIdentifier

- Dataverse builder remains compatible with your earlier code, with authors
  coming from DMP contact + contributors as before.

CLI examples:
  # Zenodo (sandbox, draft by default)
  python publish_from_dmp.py zenodo \
    --dmp dmp.json --token $ZENODO_TOKEN \
    --files data/file1.csv data/file2.parquet \
    --sandbox --no-publish

  # Dataverse (DeiC, tmpdemo collection by default, draft by default)
  python publish_from_dmp.py dataverse \
    --dmp dmp.json --token $DATAVERSE_TOKEN \
    --alias tmpdemo --base-url https://dataverse.deic.dk \
    --files data/file1.csv data/file2.parquet
"""

from __future__ import annotations

import argparse
import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

# =========================
# Exceptions / constants
# =========================

class PublishError(RuntimeError):
    pass

RETRY_STATUS = {429, 500, 502, 503, 504}
DEFAULT_TIMEOUT = 60

# =========================
# maDMP utilities
# =========================

def _get(d: dict, path: List[str], default=None):
    cur = d
    for p in path:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return default
    return cur

def _norm_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]

def _guess_dataset(dmp: dict, dataset_id: Optional[str]) -> dict:
    datasets = _get(dmp, ["dmp", "dataset"], []) or dmp.get("dataset", [])
    if not datasets:
        raise PublishError("No datasets found in the DMP (expected 'dmp.dataset' or top-level 'dataset').")
    if dataset_id:
        for ds in datasets:
            if ds.get("dataset_id") == dataset_id or ds.get("title") == dataset_id:
                return ds
            for ident in _norm_list(ds.get("identifier")) + _norm_list(ds.get("dataset_id")):
                if isinstance(ident, dict) and ident.get("identifier") == dataset_id:
                    return ds
                if ident == dataset_id:
                    return ds
    return datasets[0]

def _keywords_from_madmp(ds: dict) -> List[str]:
    kws = []
    kws += [kw for kw in _norm_list(ds.get("keyword", [])) if isinstance(kw, str)]
    for subj in _norm_list(ds.get("subject", [])):
        term = subj.get("term") or subj.get("value") if isinstance(subj, dict) else None
        if term:
            kws.append(term)
    seen = set(); out = []
    for k in (k.strip() for k in kws if isinstance(k, str)):
        if k and k.lower() not in seen:
            seen.add(k.lower()); out.append(k)
    return out[:50]



def _license_from_madmp(ds: dict) -> Optional[str]:
    """
    Map maDMP license info to a Zenodo license identifier.
    Acceptable values include (examples): cc-by-4.0, cc-by-sa-4.0, cc0-1.0, mit, gpl-3.0, apache-2.0, bsd-3-clause...
    If we can't confidently map, return None (better to omit than 400).
    """

    def _map_text_to_zenodo_id(txt: str) -> Optional[str]:
        if not txt:
            return None
        t = txt.strip().lower()

        # --- Common Creative Commons URL patterns ---
        # Any of these map to Zenodo's "cc-..." short ids
        if "creativecommons.org" in t:
            # normalize CC URLs
            # examples:
            #  https://creativecommons.org/licenses/by/4.0/           -> cc-by-4.0
            #  https://creativecommons.org/licenses/by-sa/4.0/         -> cc-by-sa-4.0
            #  https://creativecommons.org/licenses/by-nc/4.0/         -> cc-by-nc-4.0
            #  https://creativecommons.org/licenses/by-nd/4.0/         -> cc-by-nd-4.0
            #  https://creativecommons.org/licenses/by-nc-sa/4.0/      -> cc-by-nc-sa-4.0
            #  https://creativecommons.org/licenses/by-nc-nd/4.0/      -> cc-by-nc-nd-4.0
            #  https://creativecommons.org/publicdomain/zero/1.0/      -> cc0-1.0
            if "/publicdomain/zero/" in t or "/cc0/" in t:
                return "cc0-1.0"
            # licenses/by/.... capture the tail "by", "by-sa", etc, and version
            # Try to pick last two segments: e.g. ".../by/4.0/" or ".../by-nc-sa/4.0/"
            parts = [p for p in t.split("/") if p]
            try:
                kind = parts[-2]   # e.g. "by", "by-nc-sa"
                ver  = parts[-1]   # e.g. "4.0"
                if all(ch.isdigit() or ch == "." for ch in ver):
                    return f"cc-{kind}-{ver}"
            except Exception:
                pass

        # --- SPDX-like names or free text ---
        # normalize separators to dashes, strip "license"
        # examples: "CC-BY 4.0", "cc by 4.0", "CC BY-SA 4.0", "MIT", "Apache 2.0", "GPLv3"...
        s = t.replace("_", "-").replace("license", "").strip()
        s = s.replace(" ", "-")

        # CC shorthands
        cc_map = {
            "cc-by-4.0": "cc-by-4.0",
            "cc-by-sa-4.0": "cc-by-sa-4.0",
            "cc-by-nd-4.0": "cc-by-nd-4.0",
            "cc-by-nc-4.0": "cc-by-nc-4.0",
            "cc-by-nc-sa-4.0": "cc-by-nc-sa-4.0",
            "cc-by-nc-nd-4.0": "cc-by-nc-nd-4.0",
            "cc0-1.0": "cc0-1.0",
            "cc-0-1.0": "cc0-1.0",
            "cc-zero-1.0": "cc0-1.0",
            "cc-zero": "cc0-1.0",
        }
        if s in cc_map:
            return cc_map[s]

        # Handle loose forms like "cc-by", "cc-by-sa" without version (assume 4.0)
        if s in {"cc-by", "cc-by-sa", "cc-by-nd", "cc-by-nc", "cc-by-nc-sa", "cc-by-nc-nd"}:
            return f"{s}-4.0"

        # SPDX-ish common software licenses
        spdx_map = {
            "mit": "mit",
            "apache-2.0": "apache-2.0",
            "apache2.0": "apache-2.0",
            "apache-2": "apache-2.0",
            "gpl-3.0": "gpl-3.0",
            "gpl3.0": "gpl-3.0",
            "gpl-v3": "gpl-3.0",
            "gplv3": "gpl-3.0",
            "gpl-2.0": "gpl-2.0",
            "bsd-3-clause": "bsd-3-clause",
            "bsd-2-clause": "bsd-2-clause",
            "lgpl-3.0": "lgpl-3.0",
            "mpl-2.0": "mpl-2.0",
            "epl-2.0": "epl-2.0",
            "artistic-2.0": "artistic-2.0",
        }
        if s in spdx_map:
            return spdx_map[s]

        # Detect "gplv3" etc inside text
        if "gpl" in s and "3" in s:
            return "gpl-3.0"
        if "gpl" in s and "2" in s:
            return "gpl-2.0"
        if "apache" in s and ("2" in s or "2.0" in s):
            return "apache-2.0"
        if s == "cc-by-4":  # sloppy variant
            return "cc-by-4.0"

        return None

    # Try distribution licenses first
    cand: Optional[str] = None
    for dist in _norm_list(ds.get("distribution", [])):
        for r in _norm_list(dist.get("license", [])):
            if isinstance(r, dict):
                for k in ("license_ref", "rightsUri", "spdx", "title"):
                    v = r.get(k)
                    cand = _map_text_to_zenodo_id(v) or cand
            elif isinstance(r, str):
                cand = _map_text_to_zenodo_id(r) or cand
        if cand:
            break

    # Legacy places (rare)
    if not cand:
        for r in _norm_list(ds.get("rights", [])):
            if isinstance(r, dict):
                for k in ("license", "rightsUri", "spdx", "title"):
                    v = r.get(k)
                    cand = _map_text_to_zenodo_id(v) or cand
            elif isinstance(r, str):
                cand = _map_text_to_zenodo_id(r) or cand
            if cand:
                break

    return cand  # may be None; caller should omit 'license' if None


def _access_right_from_madmp(ds: dict) -> Tuple[str, Optional[str]]:
    """
    Inspect ds.distribution[*].data_access + license start_date for embargo cues.
    Returns ("open" | "restricted" | "embargoed" | "closed", embargo_date?)
    """
    # prefer distribution-level access setting if available
    access = None
    embargo_date = None
    for dist in _norm_list(ds.get("distribution", [])):
        acc = (dist.get("data_access") or "").lower().strip() or None
        if acc:
            access = acc
        # If a license start_date is in the future, some communities infer embargo.
        for r in _norm_list(dist.get("license", [])):
            if isinstance(r, dict):
                sd = r.get("start_date")
                if sd:
                    embargo_date = sd
    ds_access = (ds.get("access") or ds.get("access_right") or "").lower().strip()
    if not access and ds_access:
        access = ds_access

    if access in {"open"}:
        return "open", None
    if access in {"shared", "restricted"}:
        return "restricted", None
    if "embargo" in (access or ""):
        return "embargoed", embargo_date
    if access in {"closed", "closedaccess"}:
        return "closed", None
    # default: open if unspecified
    return "open", None

def _description_from_madmp(dmp: dict, ds: dict) -> str:
    desc = ds.get("description") or _get(ds, ["description", "text"])
    if not desc:
        desc = _get(dmp, ["dmp", "description"]) or dmp.get("description") or ""
    return desc or "No description provided."

def _related_identifiers(ds: dict) -> List[Dict[str, str]]:
    rels = []
    # dataset-level related or reference
    for ref in _norm_list(ds.get("related_identifier", [])) + _norm_list(ds.get("reference", [])):
        if isinstance(ref, dict):
            idv = ref.get("identifier") or ref.get("id")
            scheme = (ref.get("type") or ref.get("scheme") or "").upper() or None
            relation = (ref.get("relation_type") or ref.get("relation") or "isReferencedBy")
        else:
            idv = str(ref); scheme = None; relation = "isReferencedBy"
        if idv:
            r = {"identifier": idv, "relation": relation}
            if scheme: r["scheme"] = scheme
            rels.append(r)
    return rels[:100]

# =========================
# People & affiliation helpers (improved mapping)
# =========================

def _normalize_orcid(raw: Optional[str]) -> Optional[str]:
    """Return a clean ORCID '0000-0000-0000-0000' or with X checksum (or None)."""
    if not raw:
        return None
    s = str(raw).strip()
    s = s.replace("https://orcid.org/", "").replace("http://orcid.org/", "").strip()
    s = s.replace(" ", "").replace("-", "")
    # allow final X
    core, last = s[:-1], s[-1:] if s else ("", "")
    if len(s) == 16 and (core.isdigit() and (last.isdigit() or last.upper() == "X")):
        return f"{s[0:4]}-{s[4:8]}-{s[8:12]}-{s[12:16]}"
    # already dashed?
    if len(s) == 19 and s.count("-") == 3:
        return s
    return None

def _affiliation_from_node(node: Optional[dict]) -> Tuple[Optional[str], Optional[str]]:
    """
    Returns (affiliation_name, ror_identifier) from a DMP node like:
      {"name": "...", "affiliation_id": {"type":"ror","identifier":"https://ror.org/..."}}
    """
    if not isinstance(node, dict):
        return (None, None)
    name = node.get("name")
    ror = None
    aff_id = node.get("affiliation_id") or node.get("organization_id") or {}
    if isinstance(aff_id, dict) and (aff_id.get("type") or "").lower() == "ror":
        rid = aff_id.get("identifier")
        if isinstance(rid, str) and rid:
            ror = rid.strip()
    return (name, ror)

def _primary_creator_from_contact(dmp: dict) -> Dict[str, Any]:
    """
    Build the *primary* Zenodo creator from dmp.contact.
    Zenodo creators accept: name, affiliation, orcid (plus extra identifiers ignored if unknown).
    """
    c = _get(dmp, ["dmp", "contact"]) or dmp.get("contact") or {}
    name = c.get("name") or c.get("mbox") or "Unknown, Unknown"
    orcid = None
    cid = c.get("contact_id") or {}
    if (cid.get("type") or "").lower() == "orcid":
        orcid = _normalize_orcid(cid.get("identifier"))

    # affiliation: prefer contact.affiliation, else contact.organization
    aff_name, aff_ror = _affiliation_from_node(c.get("affiliation") or c.get("organization"))

    creator = {"name": name}
    if aff_name:
        creator["affiliation"] = aff_name
    if orcid:
        creator["orcid"] = orcid
    # best-effort ROR (Zenodo may ignore if not supported)
    if aff_name and aff_ror:
        creator["affiliation_identifiers"] = [{"scheme": "ror", "identifier": aff_ror}]
    return creator

# Free-text role to Zenodo contributor.type map (best-effort)
_ZENODO_ROLE_MAP = {
    "creator": "Researcher",
    "author": "Researcher",
    "rights_holder": "RightsHolder",
    "data_manager": "DataManager",
    "data curator": "DataCurator",
    "curator": "DataCurator",
    "editor": "Editor",
    "contact person": "ContactPerson",
    "supervisor": "Supervisor",
    "project manager": "ProjectManager",
    "sponsor": "Sponsor",
    "workpackage leader": "WorkPackageLeader",
}

def _role_to_zenodo_type(role_texts: List[str]) -> str:
    if not role_texts:
        return "Researcher"
    for r in role_texts:
        key = (r or "").strip().lower()
        if key in _ZENODO_ROLE_MAP:
            return _ZENODO_ROLE_MAP[key]
    return "Researcher"

def _contributors_for_zenodo_from_madmp(dmp: dict, ds: dict) -> List[Dict[str, Any]]:
    """
    Build Zenodo 'contributors' from DMP's dmp.contributor (project-level) and dataset.contributor (if present).
    Each entry: {name, type, affiliation?, orcid?, affiliation_identifiers?}
    """
    out: List[Dict[str, Any]] = []

    def _iter_contrib_blocks():
        yield from _norm_list(_get(dmp, ["dmp", "contributor"]) or dmp.get("contributor"))
        yield from _norm_list(ds.get("contributor"))

    for c in _iter_contrib_blocks():
        if not isinstance(c, dict):
            continue
        name = c.get("name") or c.get("fullname")
        if not name:
            continue
        roles = [x for x in _norm_list(c.get("role")) if isinstance(x, str)]
        ztype = _role_to_zenodo_type(roles)

        # ORCID
        orcid = None
        cid = c.get("contributor_id") or c.get("contact_id") or {}
        if (cid.get("type") or "").lower() == "orcid":
            orcid = _normalize_orcid(cid.get("identifier"))

        # affiliation
        aff_name, aff_ror = _affiliation_from_node(c.get("affiliation") or c.get("organization"))

        item: Dict[str, Any] = {"name": name, "type": ztype}
        if aff_name:
            item["affiliation"] = aff_name
        if orcid:
            item["orcid"] = orcid
        if aff_name and aff_ror:
            item["affiliation_identifiers"] = [{"scheme": "ror", "identifier": aff_ror}]

        out.append(item)

    # de-duplicate by (name, type, affiliation)
    seen = set()
    deduped = []
    for x in out:
        k = (x.get("name"), x.get("type"), x.get("affiliation"))
        if k not in seen:
            seen.add(k); deduped.append(x)
    return deduped

# =========================
# Zenodo API
# =========================

def _zenodo_base_url(sandbox: bool) -> str:
    return "https://sandbox.zenodo.org/api" if sandbox else "https://zenodo.org/api"

def _zenodo_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def _z_request(method: str, url: str, headers: dict, json_payload=None, timeout=DEFAULT_TIMEOUT):
    backoff = 1.5
    for attempt in range(6):
        r = requests.request(method, url, headers=headers, json=json_payload, timeout=timeout)
        if r.status_code in RETRY_STATUS:
            time.sleep(min(30, (attempt + 1) * backoff))
            continue
        if r.ok:
            return r
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise PublishError(f"Zenodo API error {r.status_code} on {url}: {detail}")
    raise PublishError(f"Zenodo request failed after retries: {url}")

def _z_create_deposit(token: str, sandbox: bool) -> dict:
    url = f"{_zenodo_base_url(sandbox)}/deposit/depositions"
    return _z_request("POST", url, _zenodo_headers(token), {}).json()

def _z_update_metadata(token: str, sandbox: bool, deposition_id: int, metadata: dict) -> dict:
    url = f"{_zenodo_base_url(sandbox)}/deposit/depositions/{deposition_id}"
    return _z_request("PUT", url, _zenodo_headers(token), {"metadata": metadata}).json()

def _z_publish(token: str, sandbox: bool, deposition_id: int) -> dict:
    url = f"{_zenodo_base_url(sandbox)}/deposit/depositions/{deposition_id}/actions/publish"
    return _z_request("POST", url, _zenodo_headers(token), None).json()

def _z_upload_file_to_bucket(token: str, bucket_url: str, filepath: str) -> None:
    headers = {"Authorization": f"Bearer {token}"}
    with open(filepath, "rb") as f:
        r = requests.put(f"{bucket_url}/{os.path.basename(filepath)}", data=f, headers=headers)
    if not r.ok:
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise PublishError(f"Zenodo upload failed for {filepath}: {detail}")

# =========================
# Zenodo metadata builder (improved)
# =========================

def build_zenodo_metadata_from_madmp(dmp: dict, dataset_id: Optional[str] = None) -> Tuple[dict, dict]:
    """
    Build a richer Zenodo metadata dict from RDA-DMP 1.2:

      creators:
        - ONLY the DMP contact (primary author) with:
          * name
          * affiliation (string)
          * orcid (normalized)
          * affiliation_identifiers (ROR URL; best-effort)

      contributors:
        - All DMP contributors (+ dataset-level contributors if present):
          * name
          * type (mapped from free-text role; fallback "Researcher")
          * affiliation (string)
          * orcid (normalized)
          * affiliation_identifiers (ROR URL; best-effort)

      Also passes:
        keywords, license, access_right, embargo_date, related_identifiers, language

      If dataset_id.type == 'doi', adds it as an isAlternateIdentifier related_identifier.
    """
    ds = _guess_dataset(dmp, dataset_id)

    title = ds.get("title") or _get(dmp, ["dmp", "title"]) or "Untitled dataset"
    description = _description_from_madmp(dmp, ds)

    # --- creators: ONLY the primary contact (as requested) ---
    creators = [_primary_creator_from_contact(dmp)]

    # --- contributors: from DMP contributors (+ any dataset.contributor) ---
    contributors = _contributors_for_zenodo_from_madmp(dmp, ds)

    # --- keywords, license, access, language ---
    keywords = _keywords_from_madmp(ds)
    license_id = _license_from_madmp(ds)
    access_right, embargo_date = _access_right_from_madmp(ds)
    related_identifiers = _related_identifiers(ds)

    # Existing DOI on the dataset_id
    dsid = ds.get("dataset_id") or {}
    if isinstance(dsid, dict) and (dsid.get("type") or "").lower() == "doi":
        doi_val = dsid.get("identifier")
        if isinstance(doi_val, str) and doi_val.strip():
            related_identifiers = related_identifiers or []
            related_identifiers.append({
                "identifier": doi_val.strip(),
                "relation": "isAlternateIdentifier",
                "scheme": "doi",
            })

    lang = ds.get("language") or _get(dmp, ["dmp", "language"])
    language = lang.strip() if isinstance(lang, str) and lang.strip() else None

    metadata: Dict[str, Any] = {
        "title": title,
        "upload_type": "dataset",
        "description": description,
        "creators": creators,
    }
    if contributors:
        metadata["contributors"] = contributors
    if keywords:
        metadata["keywords"] = keywords
    if license_id:
        metadata["license"] = license_id
    if access_right:
        metadata["access_right"] = access_right
    if embargo_date and access_right == "embargoed":
        metadata["embargo_date"] = embargo_date
    if related_identifiers:
        metadata["related_identifiers"] = related_identifiers
    if language:
        metadata["language"] = language

    # Optional: communities via various extension blocks
    communities = []
    for ext_name in ("extension", "extensions", "x_dcas", "x_project", "x_ui"):
        for ext in _norm_list(ds.get(ext_name, [])):
            if isinstance(ext, dict):
                comm = ext.get("community") or ext.get("zenodo_community")
                if comm:
                    communities.append({"identifier": comm})
    if communities:
        metadata["communities"] = communities[:5]

    return metadata, {
        "dataset_title": title,
        "license": license_id,
        "access_right": access_right,
    }

# =========================
# Zenodo publish flow
# =========================

def publish_dataset_from_madmp_zenodo(
    dmp_path: str,
    token: str,
    dataset_id: Optional[str] = None,
    file_paths: Optional[List[str]] = None,
    sandbox: bool = True,
    publish: bool = False
) -> Dict[str, Any]:
    """
    Create a Zenodo deposition, upload files, attach metadata from maDMP, and optionally publish.

    Returns dict with deposition_id, doi (if published), links, metadata, etc.
    """
    with open(dmp_path, "r", encoding="utf-8") as fh:
        dmp = json.load(fh)

    metadata, extra = build_zenodo_metadata_from_madmp(dmp, dataset_id)

    uploads = list(file_paths) if file_paths else []
    if not uploads:
        ds = _guess_dataset(dmp, dataset_id)
        for dist in _norm_list(ds.get("distribution", [])):
            path = dist.get("path") or dist.get("access_url") or dist.get("file_path")
            if path and os.path.exists(path):
                uploads.append(path)

    dep = _z_create_deposit(token, sandbox)
    deposition_id = dep.get("id")
    bucket_url = dep.get("links", {}).get("bucket")
    if not bucket_url:
        raise PublishError("Could not obtain Zenodo bucket URL from response.")

    uploaded = []
    for p in uploads:
        _z_upload_file_to_bucket(token, bucket_url, p)
        uploaded.append(os.path.basename(p))

    dep2 = _z_update_metadata(token, sandbox, deposition_id, metadata)
    final = _z_publish(token, sandbox, deposition_id) if publish else dep2

    return {
        "deposition_id": deposition_id,
        "conceptdoi": final.get("conceptdoi"),
        "doi": final.get("doi"),
        "links": final.get("links", {}),
        "metadata": metadata,
        "uploaded_files": uploaded,
        "sandbox": sandbox,
        "dataset_title": extra.get("dataset_title"),
        "access_right": extra.get("access_right"),
        "license": extra.get("license"),
        "published": publish,
    }

# =========================
# Dataverse API & mapping
# =========================

def _dv_headers(token: str) -> dict:
    return {"X-Dataverse-key": token}

def _dv_create_dataset(base_url: str, token: str, dataverse_alias: str, dataset_version_json: dict) -> dict:
    url = f"{base_url}/api/dataverses/{dataverse_alias}/datasets"
    r = requests.post(url, headers=_dv_headers(token), json=dataset_version_json)
    if not r.ok:
        try: detail = r.json()
        except Exception: detail = r.text
        raise PublishError(f"Dataverse create dataset failed: {r.status_code} {detail}")
    return r.json()

def _dv_upload_file(base_url: str, token: str, dataset_id: int, filepath: str,
                    description: Optional[str] = None, directory_label: Optional[str] = None,
                    restrict: bool = False) -> dict:
    url = f"{base_url}/api/datasets/{dataset_id}/add"
    files = {"file": (os.path.basename(filepath), open(filepath, "rb"))}
    json_data = {"description": description or ""}
    if directory_label: json_data["directoryLabel"] = directory_label
    if restrict: json_data["restrict"] = True
    data = {"jsonData": json.dumps(json_data)}
    r = requests.post(url, headers=_dv_headers(token), files=files, data=data)
    if not r.ok:
        try: detail = r.json()
        except Exception: detail = r.text
        raise PublishError(f"Dataverse upload failed ({filepath}): {r.status_code} {detail}")
    return r.json()

def _dv_publish_dataset(base_url: str, token: str, dataset_id: int, release_type: str = "major") -> dict:
    assert release_type in {"major", "minor"}
    url = f"{base_url}/api/datasets/{dataset_id}/actions/:publish?type={release_type}"
    r = requests.post(url, headers=_dv_headers(token))
    if not r.ok:
        try: detail = r.json()
        except Exception: detail = r.text
        raise PublishError(f"Dataverse publish failed: {r.status_code} {detail}")
    return r.json()

def _dv_authors_from_madmp(ds: dict, dmp: dict) -> List[dict]:
    """
    Dataverse 'author' compound from DMP contact + contributors (best-effort).
    """
    def _field(name, value, tclass="primitive", multiple=False):
        return {"typeName": name, "typeClass": tclass, "multiple": multiple, "value": value}

    authors = []

    # Primary: DMP contact
    c = _get(dmp, ["dmp", "contact"]) or dmp.get("contact") or {}
    cname = c.get("name") or c.get("mbox") or "Unknown, Unknown"
    aff_name, _ = _affiliation_from_node(c.get("affiliation") or c.get("organization"))
    comp = {"authorName": _field("authorName", cname)}
    if aff_name:
        comp["authorAffiliation"] = _field("authorAffiliation", aff_name)
    authors.append(_field("author", comp, tclass="compound"))

    # Additional: DMP contributors
    for cont in _norm_list(_get(dmp, ["dmp", "contributor"]) or dmp.get("contributor")):
        if not isinstance(cont, dict):
            continue
        nm = cont.get("name") or cont.get("fullname")
        if not nm:
            continue
        aff, _ = _affiliation_from_node(cont.get("affiliation") or cont.get("organization"))
        comp = {"authorName": _field("authorName", nm)}
        if aff:
            comp["authorAffiliation"] = _field("authorAffiliation", aff)
        authors.append(_field("author", comp, tclass="compound"))

    return authors

def _dv_contacts_from_madmp(ds: dict, dmp: dict) -> List[dict]:
    def _field(name, value, tclass="primitive", multiple=False):
        return {"typeName": name, "typeClass": tclass, "multiple": multiple, "value": value}
    contacts = []
    # dataset-level contacts if present
    for c in _norm_list(ds.get("contact", [])):
        email = c.get("mbox") or c.get("email") or c.get("contactEmail")
        name = c.get("name") or c.get("fullname") or email or "Unknown"
        if email:
            comp = {"datasetContactEmail": _field("datasetContactEmail", email),
                    "datasetContactName": _field("datasetContactName", name)}
            contacts.append({"typeName": "datasetContact", "typeClass": "compound", "multiple": False, "value": comp})
    if contacts:
        return contacts
    # fallback to DMP contact
    c = _get(dmp, ["dmp", "contact"]) or dmp.get("contact") or {}
    email = c.get("mbox") or c.get("email")
    name = c.get("name") or email or "Unknown"
    if email:
        comp = {"datasetContactEmail": _field("datasetContactEmail", email),
                "datasetContactName": _field("datasetContactName", name)}
        contacts.append({"typeName": "datasetContact", "typeClass": "compound", "multiple": False, "value": comp})
    return contacts

def _dv_subjects_from_madmp(ds: dict) -> List[dict]:
    subs = []
    for s in _norm_list(ds.get("subject")):
        term = s.get("term") if isinstance(s, dict) else s
        if isinstance(term, str) and term.strip():
            subs.append({"typeName": "subject", "typeClass": "controlledVocabulary", "multiple": True, "value": term})
    if not subs:
        subs.append({"typeName": "subject", "typeClass": "controlledVocabulary", "multiple": True, "value": "Other"})
    return subs

def _dv_description_field(ds: dict, dmp: dict) -> dict:
    desc = ds.get("description") or _get(ds, ["description", "text"]) or _get(dmp, ["dmp", "description"]) or "No description provided."
    return {"typeName": "dsDescription", "typeClass": "compound", "multiple": True,
            "value": {"dsDescriptionValue": {"typeName": "dsDescriptionValue", "typeClass": "primitive", "multiple": False, "value": desc}}}

def build_dataverse_dataset_version_from_madmp(dmp: dict, dataset_id: Optional[str] = None) -> Tuple[dict, dict]:
    ds = _guess_dataset(dmp, dataset_id)
    title = ds.get("title") or _get(dmp, ["dmp", "title"]) or "Untitled dataset"
    fields: List[dict] = []
    fields.append({"typeName": "title", "typeClass": "primitive", "multiple": False, "value": title})
    fields.extend(_dv_authors_from_madmp(ds, dmp))
    fields.extend(_dv_contacts_from_madmp(ds, dmp))
    fields.append(_dv_description_field(ds, dmp))
    fields.extend(_dv_subjects_from_madmp(ds))
    return {
        "datasetVersion": {"metadataBlocks": {"citation": {"displayName": "Citation Metadata", "fields": fields}}}
    }, {"dataset_title": title}

def publish_dataset_to_dataverse(
    dmp_path: str,
    token: str,
    dataverse_alias: str = "tmpdemo",
    base_url: str = "https://dataverse.deic.dk",
    dataset_id_selector: Optional[str] = None,
    file_paths: Optional[List[str]] = None,
    publish: bool = False,
    release_type: str = "major"
) -> Dict[str, Any]:
    """
    Create a Dataverse dataset from an maDMP JSON and optionally publish it.
    Returns dict with dataset id, persistentId, landing page, etc.
    """
    with open(dmp_path, "r", encoding="utf-8") as fh:
        dmp = json.load(fh)

    dataset_version, extra = build_dataverse_dataset_version_from_madmp(dmp, dataset_id_selector)

    resp = _dv_create_dataset(base_url, token, dataverse_alias, dataset_version)
    data = resp.get("data") or {}
    ds_id = data.get("id")
    pid = data.get("persistentId") or data.get("identifier")
    if not ds_id:
        raise PublishError(f"Dataverse: missing dataset id in response: {resp}")

    uploaded = []
    uploads = list(file_paths) if file_paths else []
    if not uploads:
        ds = _guess_dataset(dmp, dataset_id_selector)
        for dist in _norm_list(ds.get("distribution", [])):
            path = dist.get("path") or dist.get("access_url") or dist.get("file_path")
            if path and os.path.exists(path):
                uploads.append(path)
    for p in uploads:
        _dv_upload_file(base_url, token, ds_id, p)
        uploaded.append(os.path.basename(p))

    publish_result = None
    if publish:
        publish_result = _dv_publish_dataset(base_url, token, ds_id, release_type=release_type)

    landing = f"{base_url}/dataset.xhtml?persistentId={pid}" if pid else None
    return {
        "dataset_id": ds_id,
        "persistentId": pid,
        "landing_page": landing,
        "uploaded_files": uploaded,
        "published": bool(publish_result),
        "dataset_title": extra.get("dataset_title"),
    }

# =========================
# Streamlit convenience wrappers (used by the editor)
# =========================


def streamlit_publish_to_zenodo(
    *,
    dataset: dict,
    dmp: dict,
    token: str,
    sandbox: bool = True,
    publish: bool = False,
    file_paths: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Streamlit-friendly call: takes in-memory dmp + dataset, writes a temp DMP and publishes.
    """
    import tempfile, json as _json, streamlit as st
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as tf:
        _json.dump(dmp, tf, ensure_ascii=False, indent=2)
        dmp_path = tf.name
    try:
        result = publish_dataset_from_madmp_zenodo(
            dmp_path=dmp_path,
            token=token,
            dataset_id=dataset.get("title") or None,
            file_paths=file_paths,
            sandbox=sandbox,
            publish=publish,
        )
        # --- show link in Streamlit UI ---
        links = result.get("links") or {}
        url = links.get("html") or links.get("latest_html")
        if url:
            st.success(f"✅ Zenodo deposition created. [Open in Zenodo]({url})")
        else:
            st.info("Zenodo deposition created, but no link was returned.")
        return result
    finally:
        try:
            os.unlink(dmp_path)
        except Exception:
            pass

def streamlit_publish_to_dataverse(
    *,
    dataset: dict,
    dmp: dict,
    token: str,
    base_url: str = "https://dataverse.deic.dk",
    alias: str = "tmpdemo",
    publish: bool = False,
    release_type: str = "major",
    file_paths: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Streamlit-friendly call: takes in-memory dmp + dataset, writes a temp DMP and publishes to Dataverse.
    Renders a clickable landing-page link upon success.
    """
    import tempfile, json as _json, streamlit as st

    # Write DMP to a temp file
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as tf:
        _json.dump(dmp, tf, ensure_ascii=False, indent=2)
        dmp_path = tf.name

    try:
        result = publish_dataset_to_dataverse(
            dmp_path=dmp_path,
            token=token,
            dataverse_alias=alias,
            base_url=base_url,
            dataset_id_selector=dataset.get("title") or None,
            file_paths=file_paths,
            publish=publish,
            release_type=release_type,
        )

        # --- Render link(s) in UI ---
        landing = result.get("landing_page")
        pid = result.get("persistentId")
        if not landing and pid:
            # Fallback construction (matches what publish_dataset_to_dataverse does)
            landing = f"{base_url.rstrip('/')}/dataset.xhtml?persistentId={pid}"

        if landing:
            if result.get("published"):
                st.success(f"✅ Dataverse {'published' if publish else 'dataset created'} — [Open dataset]({landing})")
            else:
                st.success(f"✅ Dataverse draft created — [Open dataset]({landing})")
        else:
            st.info("Dataverse dataset created, but no landing page link was returned.")

        return result

    finally:
        try:
            os.unlink(dmp_path)
        except Exception:
            pass


# =========================
# CLI
# =========================

def _parse_args():
    p = argparse.ArgumentParser(description="Publish from maDMP to Zenodo or Dataverse")
    sub = p.add_subparsers(dest="target", required=True)

    # Zenodo subcommand
    z = sub.add_parser("zenodo", help="Publish to Zenodo")
    z.add_argument("--dmp", required=True, help="Path to maDMP JSON")
    z.add_argument("--token", required=True, help="Zenodo API token")
    z.add_argument("--dataset-id", help="Dataset selector in maDMP (id or title)")
    z.add_argument("--files", nargs="*", help="Files to upload; if omitted, tries ds.distribution[*].path/access_url")
    z.add_argument("--sandbox", action="store_true", help="Use sandbox.zenodo.org")
    z.add_argument("--publish", action="store_true", help="Publish after creating (default: draft only)")

    # Dataverse subcommand
    d = sub.add_parser("dataverse", help="Publish to Dataverse (e.g., DeiC)")
    d.add_argument("--dmp", required=True, help="Path to maDMP JSON")
    d.add_argument("--token", required=True, help="Dataverse API token")
    d.add_argument("--alias", default="tmpdemo", help="Target Dataverse collection alias (default: tmpdemo)")
    d.add_argument("--base-url", default="https://dataverse.deic.dk", help="Dataverse base URL")
    d.add_argument("--dataset-id", help="Dataset selector in maDMP (id or title)")
    d.add_argument("--files", nargs="*", help="Files to upload; if omitted, tries ds.distribution[*].path/access_url")
    d.add_argument("--publish", action="store_true", help="Publish after creating (default: draft only)")
    d.add_argument("--release-type", choices=["major", "minor"], default="major", help="Dataverse release type")

    return p.parse_args()

def main():
    args = _parse_args()
    if args.target == "zenodo":
        result = publish_dataset_from_madmp_zenodo(
            dmp_path=args.dmp,
            token=args.token,
            dataset_id=args.dataset_id,
            file_paths=args.files,
            sandbox=args.sandbox,
            publish=args.publish,
        )
    else:
        result = publish_dataset_to_dataverse(
            dmp_path=args.dmp,
            token=args.token,
            dataverse_alias=args.alias,
            base_url=args.base_url,
            dataset_id_selector=args.dataset_id,
            file_paths=args.files,
            publish=args.publish,
            release_type=getattr(args, "release_type", "major"),
        )
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
