#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
publish_from_dmp.py
-------------------
Publish a dataset using metadata extracted from an RDA maDMP (v1.2 JSON)
to either **Zenodo** or **Dataverse** (e.g., DeiC Dataverse).

Behavior:
- If dataset has personal_data=="yes" or sensitive_data=="yes":
  * Do NOT upload files (metadata-only record).
  * Append a note to the description listing skipped filenames.
  * Zenodo access_right is tightened to at least "restricted".
  * Results include "sensitive_or_personal" and "skipped_files".

Mapping highlights (Zenodo):
- creators     = DMP contact (primary author), ORCID, affiliation (+ ROR best-effort)
- contributors = DMP contributors (+ dataset.contributor) → role-mapped with ORCID & affiliation (+ ROR best-effort)
- keywords, license, access_right, embargo_date, related_identifiers, language
- dataset_id.type == "doi" -> related_identifiers isAlternateIdentifier

Dataverse:
- authors = DMP contact + contributors (best-effort)
- contacts, title, description, subjects

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
from datetime import date
import tempfile

import requests

# Streamlit is optional at CLI time, but imported for the editor wrappers.
try:
    import streamlit as st  # type: ignore
except Exception:
    st = None  # type: ignore

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

# --- sensitivity/personal-data flag ---

def _has_personal_or_sensitive(ds: dict) -> bool:
    def _yes(x):
        return isinstance(x, str) and x.strip().lower() == "yes"
    return _yes(ds.get("personal_data")) or _yes(ds.get("sensitive_data"))

# --- license mapping (Zenodo short ids) ---

def _license_from_madmp(ds: dict) -> Optional[str]:
    """
    Map maDMP license info to a Zenodo license identifier.
    If personal/sensitive data is present, prefer a closed placeholder unless an explicit closed license is provided.
    """
    if _has_personal_or_sensitive(ds):
        mapped = _license_from_madmp_nosensitive(ds)
        return mapped or "other-closed"
    return _license_from_madmp_nosensitive(ds)

def _license_from_madmp_nosensitive(ds: dict) -> Optional[str]:
    def _map_text_to_zenodo_id(txt: str) -> Optional[str]:
        if not txt:
            return None
        t = txt.strip().lower()

        # CC URLs → cc-... ids
        if "creativecommons.org" in t:
            if "/publicdomain/zero/" in t or "/cc0/" in t:
                return "cc0-1.0"
            parts = [p for p in t.split("/") if p]
            try:
                kind = parts[-2]   # e.g. by, by-nc-sa
                ver  = parts[-1]   # e.g. 4.0
                if all(ch.isdigit() or ch == "." for ch in ver):
                    return f"cc-{kind}-{ver}"
            except Exception:
                pass

        s = t.replace("_", "-").replace("license", "").strip().replace(" ", "-")
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
        if s in {"cc-by", "cc-by-sa", "cc-by-nd", "cc-by-nc", "cc-by-nc-sa", "cc-by-nc-nd"}:
            return f"{s}-4.0"

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
        if "gpl" in s and "3" in s:
            return "gpl-3.0"
        if "gpl" in s and "2" in s:
            return "gpl-2.0"
        if "apache" in s and ("2" in s or "2.0" in s):
            return "apache-2.0"
        if s == "cc-by-4":
            return "cc-by-4.0"
        return None

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

    return cand

# --- access_right mapping (Zenodo) ---

def _has_downloadable_files(ds: dict) -> bool:
    """Check if dataset has any real downloadable file references."""
    for dist in _norm_list(ds.get("distribution", [])):
        if any(
            (dist.get(k) or "").strip()
            for k in ("access_url", "download_url", "downloadURL", "path", "uri", "url")
        ):
            return True
    return False

def _access_right_from_madmp(ds: dict) -> Tuple[str, Optional[str]]:
    """
    Decide Zenodo access_right and (optional) embargo_date.
    Rules:
      - If no raw data is uploaded OR data contains personal/sensitive info → closed
      - If embargo_date is strictly in the future → embargoed
      - Else → open/restricted according to access setting
    """
    access: Optional[str] = None
    embargo_date: Optional[str] = None

    # Extract access and embargo date (only keep future dates)
    for dist in _norm_list(ds.get("distribution", [])):
        acc = (dist.get("data_access") or "").strip().lower() or None
        if acc:
            access = acc
        for lic in _norm_list(dist.get("license", [])):
            if isinstance(lic, dict):
                sd = (lic.get("start_date") or "").strip()
                if sd:
                    try:
                        if date.fromisoformat(sd) > date.today():
                            embargo_date = sd
                    except Exception:
                        pass

    ds_access = (ds.get("access") or ds.get("access_right") or "").strip().lower()
    if not access and ds_access:
        access = ds_access

    files_available = _has_downloadable_files(ds)
    has_sensitive = _has_personal_or_sensitive(ds)

    # ✅ Core rule: if no files or sensitive → closed
    if not files_available or has_sensitive:
        return "closed", embargo_date

    # Otherwise map declared access
    if access in {"open"}:
        base = "open"
    elif access in {"shared", "restricted"}:
        base = "restricted"
    elif access and "embargo" in access:
        base = "embargoed"
    elif access in {"closed", "closedaccess"}:
        base = "closed"
    else:
        base = "open"

    # Only embargo if embargo_date is in the future
    if embargo_date and base not in {"closed"}:
        base = "embargoed"
    elif base == "embargoed" and not embargo_date:
        base = "open"

    return base, embargo_date

def _description_from_madmp(dmp: dict, ds: dict) -> str:
    desc = ds.get("description") or _get(ds, ["description", "text"])
    if not desc:
        desc = _get(dmp, ["dmp", "description"]) or dmp.get("description") or ""
    return desc or "No description provided."

def _related_identifiers(ds: dict) -> List[Dict[str, str]]:
    rels = []
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
    """Return a clean ORCID '0000-0000-0000-0000' (last digit may be X) or None."""
    if not raw:
        return None
    s = str(raw).strip()
    s = s.replace("https://orcid.org/", "").replace("http://orcid.org/", "").strip()
    s = s.replace(" ", "").replace("-", "")
    if len(s) != 16:
        if len(s) == 19 and s.count("-") == 3:
            return s
        return None
    core, last = s[:-1], s[-1:]
    if core.isdigit() and (last.isdigit() or last.upper() == "X"):
        return f"{s[0:4]}-{s[4:8]}-{s[8:12]}-{s[12:16]}"
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
    """
    c = _get(dmp, ["dmp", "contact"]) or dmp.get("contact") or {}
    name = c.get("name") or c.get("mbox") or "Unknown, Unknown"
    orcid = None
    cid = c.get("contact_id") or {}
    if (cid.get("type") or "").lower() == "orcid":
        orcid = _normalize_orcid(cid.get("identifier"))
    aff_name, aff_ror = _affiliation_from_node(c.get("affiliation") or c.get("organization"))

    creator = {"name": name}
    if aff_name:
        creator["affiliation"] = aff_name
    if orcid:
        creator["orcid"] = orcid
    if aff_name and aff_ror:
        creator["affiliation_identifiers"] = [{"scheme": "ror", "identifier": aff_ror}]
    return creator

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
    Build Zenodo 'contributors' from DMP's dmp.contributor and dataset.contributor.
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
        orcid = None
        cid = c.get("contributor_id") or c.get("contact_id") or {}
        if (cid.get("type") or "").lower() == "orcid":
            orcid = _normalize_orcid(cid.get("identifier"))
        aff_name, aff_ror = _affiliation_from_node(c.get("affiliation") or c.get("organization"))

        item: Dict[str, Any] = {"name": name, "type": ztype}
        if aff_name:
            item["affiliation"] = aff_name
        if orcid:
            item["orcid"] = orcid
        if aff_name and aff_ror:
            item["affiliation_identifiers"] = [{"scheme": "ror", "identifier": aff_ror}]
        out.append(item)

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

def build_zenodo_metadata_from_madmp(
    dmp: dict,
    dataset_id: Optional[str] = None,
    *,
    sensitive_flag: Optional[bool] = None,
    skipped_files: Optional[List[str]] = None,
) -> Tuple[dict, dict]:
    """
    Build a richer Zenodo metadata dict from RDA-DMP 1.2.
    If sensitive_flag is True, appends a note to description listing skipped_files.
    """
    ds = _guess_dataset(dmp, dataset_id)

    title = ds.get("title") or _get(dmp, ["dmp", "title"]) or "Untitled dataset"
    description = _description_from_madmp(dmp, ds)

    # creators: ONLY the primary contact
    creators = [_primary_creator_from_contact(dmp)]

    # contributors
    contributors = _contributors_for_zenodo_from_madmp(dmp, ds)

    # keywords, license, access, language
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

    # sensitive note with skipped files
    if sensitive_flag:
        skipped = skipped_files or []
        if skipped:
            bullet = "\n".join(f"  - {os.path.basename(x)}" for x in skipped)
            note = (
                "\n\n[NOTICE] Files withheld due to personal/sensitive data. "
                "A metadata-only record has been created. Skipped files:\n"
                f"{bullet}"
            )
        else:
            note = (
                "\n\n[NOTICE] Files withheld due to personal/sensitive data. "
                "A metadata-only record has been created."
            )
        description = (description or "No description provided.") + note

    metadata: Dict[str, Any] = {
        "title": title,
        "upload_type": "dataset",
        "description": description or "No description provided.",
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

    # Optional: communities via extension blocks
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

def _candidate_files_from_ds(ds: dict, file_paths: Optional[List[str]]) -> List[str]:
    uploads = list(file_paths) if file_paths else []
    if not uploads:
        for dist in _norm_list(ds.get("distribution", [])):
            path = dist.get("path") or dist.get("access_url") or dist.get("file_path")
            if path and os.path.exists(path):
                uploads.append(path)
    # unique, keep order
    seen = set(); out = []
    for p in uploads:
        if p not in seen:
            seen.add(p); out.append(p)
    return out

def publish_dataset_from_madmp_zenodo(
    dmp_path: str,
    token: str,
    dataset_id: Optional[str] = None,
    file_paths: Optional[List[str]] = None,
    sandbox: bool = True,
    publish: bool = False
) -> Dict[str, Any]:
    """
    Create a Zenodo deposition, upload files (unless sensitive/personal), attach metadata from maDMP, and optionally publish.
    """
    with open(dmp_path, "r", encoding="utf-8") as fh:
        dmp = json.load(fh)

    ds = _guess_dataset(dmp, dataset_id)
    sensitive_or_personal = _has_personal_or_sensitive(ds)

    # Decide which files to upload
    intended_uploads = _candidate_files_from_ds(ds, file_paths)
    uploads = [] if sensitive_or_personal else intended_uploads
    skipped_files = intended_uploads if sensitive_or_personal else []

    # Build metadata (include sensitive note + skipped list if applicable)
    metadata, extra = build_zenodo_metadata_from_madmp(
        dmp,
        dataset_id,
        sensitive_flag=sensitive_or_personal,
        skipped_files=skipped_files,
    )

    # Create deposition
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
        "skipped_files": [os.path.basename(x) for x in skipped_files],
        "sensitive_or_personal": sensitive_or_personal,
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
    url = f"{base_url.rstrip('/')}/api/dataverses/{dataverse_alias}/datasets"
    r = requests.post(url, headers=_dv_headers(token), json=dataset_version_json)
    if not r.ok:
        try: detail = r.json()
        except Exception: detail = r.text
        raise PublishError(f"Dataverse create dataset failed: {r.status_code} {detail}")
    return r.json()

def _dv_upload_file(base_url: str, token: str, dataset_id: int, filepath: str,
                    description: Optional[str] = None, directory_label: Optional[str] = None,
                    restrict: bool = False) -> dict:
    url = f"{base_url.rstrip('/')}/api/datasets/{dataset_id}/add"
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
    url = f"{base_url.rstrip('/')}/api/datasets/{dataset_id}/actions/:publish?type={release_type}"
    r = requests.post(url, headers=_dv_headers(token))
    if not r.ok:
        try: detail = r.json()
        except Exception: detail = r.text
        raise PublishError(f"Dataverse publish failed: {r.status_code} {detail}")
    return r.json()

# ---- Dataverse field builders ----

def _dv_field(name, value, tclass="primitive", multiple=False):
    return {"typeName": name, "typeClass": tclass, "multiple": multiple, "value": value}

def _dv_authors_from_madmp(ds: dict, dmp: dict) -> List[dict]:
    """
    Dataverse 'author' compound from DMP contact + contributors (best-effort).
    """
    authors = []

    # Primary: DMP contact
    c = _get(dmp, ["dmp", "contact"]) or dmp.get("contact") or {}
    cname = c.get("name") or c.get("mbox") or "Unknown, Unknown"
    aff_name, _ = _affiliation_from_node(c.get("affiliation") or c.get("organization"))
    comp = {"authorName": _dv_field("authorName", cname)}
    if aff_name:
        comp["authorAffiliation"] = _dv_field("authorAffiliation", aff_name)
    authors.append(_dv_field("author", comp, tclass="compound"))

    # Additional: DMP contributors
    for cont in _norm_list(_get(dmp, ["dmp", "contributor"]) or dmp.get("contributor")):
        if not isinstance(cont, dict):
            continue
        nm = cont.get("name") or cont.get("fullname")
        if not nm:
            continue
        aff, _ = _affiliation_from_node(cont.get("affiliation") or cont.get("organization"))
        comp = {"authorName": _dv_field("authorName", nm)}
        if aff:
            comp["authorAffiliation"] = _dv_field("authorAffiliation", aff)
        authors.append(_dv_field("author", comp, tclass="compound"))

    return authors

def _dv_contacts_from_madmp(ds: dict, dmp: dict) -> List[dict]:
    contacts = []
    # dataset-level contacts if present
    for c in _norm_list(ds.get("contact", [])):
        email = c.get("mbox") or c.get("email") or c.get("contactEmail")
        name = c.get("name") or c.get("fullname") or email or "Unknown"
        if email:
            comp = {"datasetContactEmail": _dv_field("datasetContactEmail", email),
                    "datasetContactName": _dv_field("datasetContactName", name)}
            contacts.append({"typeName": "datasetContact", "typeClass": "compound", "multiple": False, "value": comp})
    if contacts:
        return contacts
    # fallback to DMP contact
    c = _get(dmp, ["dmp", "contact"]) or dmp.get("contact") or {}
    email = c.get("mbox") or c.get("email")
    name = c.get("name") or email or "Unknown"
    if email:
        comp = {"datasetContactEmail": _dv_field("datasetContactEmail", email),
                "datasetContactName": _dv_field("datasetContactName", name)}
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

def _dv_description_value(ds: dict, dmp: dict, sensitive_flag: bool, skipped_files: List[str]) -> str:
    base = ds.get("description") or _get(ds, ["description", "text"]) or _get(dmp, ["dmp", "description"]) or "No description provided."
    if sensitive_flag:
        if skipped_files:
            bullet = "\n".join(f"  - {os.path.basename(x)}" for x in skipped_files)
            note = (
                "\n\n[NOTICE] Files withheld due to personal/sensitive data. "
                "A metadata-only record has been created. Skipped files:\n"
                f"{bullet}"
            )
        else:
            note = "\n\n[NOTICE] Files withheld due to personal/sensitive data. A metadata-only record has been created."
        return base + note
    return base

def build_dataverse_dataset_version_from_madmp(
    dmp: dict,
    dataset_id: Optional[str] = None,
    *,
    sensitive_flag: bool = False,
    skipped_files: Optional[List[str]] = None,
) -> Tuple[dict, dict]:
    ds = _guess_dataset(dmp, dataset_id)
    title = ds.get("title") or _get(dmp, ["dmp", "title"]) or "Untitled dataset"

    fields: List[dict] = []
    fields.append({"typeName": "title", "typeClass": "primitive", "multiple": False, "value": title})
    fields.extend(_dv_authors_from_madmp(ds, dmp))
    fields.extend(_dv_contacts_from_madmp(ds, dmp))

    desc_val = _dv_description_value(ds, dmp, sensitive_flag, skipped_files or [])
    fields.append({
        "typeName": "dsDescription",
        "typeClass": "compound",
        "multiple": True,
        "value": {"dsDescriptionValue": _dv_field("dsDescriptionValue", desc_val)}
    })
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
    """
    with open(dmp_path, "r", encoding="utf-8") as fh:
        dmp = json.load(fh)

    ds = _guess_dataset(dmp, dataset_id_selector)
    sensitive_or_personal = _has_personal_or_sensitive(ds)

    intended_uploads = _candidate_files_from_ds(ds, file_paths)
    uploads = [] if sensitive_or_personal else intended_uploads
    skipped_files = intended_uploads if sensitive_or_personal else []

    dataset_version, extra = build_dataverse_dataset_version_from_madmp(
        dmp, dataset_id_selector, sensitive_flag=sensitive_or_personal, skipped_files=skipped_files
    )

    resp = _dv_create_dataset(base_url, token, dataverse_alias, dataset_version)
    data = resp.get("data") or {}
    ds_id = data.get("id")
    pid = data.get("persistentId") or data.get("identifier")
    if not ds_id:
        raise PublishError(f"Dataverse: missing dataset id in response: {resp}")

    uploaded = []
    for p in uploads:
        _dv_upload_file(base_url, token, ds_id, p)
        uploaded.append(os.path.basename(p))

    publish_result = None
    if publish:
        publish_result = _dv_publish_dataset(base_url, token, ds_id, release_type=release_type)

    landing = f"{base_url.rstrip('/')}/dataset.xhtml?persistentId={pid}" if pid else None
    return {
        "dataset_id": ds_id,
        "persistentId": pid,
        "landing_page": landing,
        "uploaded_files": uploaded,
        "skipped_files": [os.path.basename(x) for x in skipped_files],
        "sensitive_or_personal": sensitive_or_personal,
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
    allow_reused: bool = False,
    file_paths: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Streamlit-friendly call: takes in-memory dmp + dataset, writes a temp DMP and publishes.
    """
    if str(dataset.get("is_reused", "")).strip().lower() in {"true", "1", "yes"} and not allow_reused:
        raise PublishError("Blocked: dataset is marked re-used (is_reused=true) in the DMP.")

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as tf:
        json.dump(dmp, tf, ensure_ascii=False, indent=2)
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
        # Show link in Streamlit UI
        if st is not None:
            links = result.get("links") or {}
            url = links.get("html") or links.get("latest_html")
            if url:
                msg = "published" if publish else "deposition created"
                st.success(f"✅ Zenodo {msg}. [Open in Zenodo]({url})")
            else:
                st.info("Zenodo deposition created, but no link was returned.")
            if result.get("sensitive_or_personal"):
                skipped = result.get("skipped_files") or []
                if skipped:
                    st.warning(f"Files not uploaded due to personal/sensitive data: {', '.join(skipped)}")
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
    allow_reused: bool = False,
    release_type: str = "major",
    file_paths: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Streamlit-friendly call: takes in-memory dmp + dataset, writes a temp DMP and publishes to Dataverse.
    Renders a clickable landing-page link upon success.
    """
    if str(dataset.get("is_reused", "")).strip().lower() in {"true", "1", "yes"} and not allow_reused:
        raise PublishError("Blocked: dataset is marked re-used (is_reused=true) in the DMP.")

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as tf:
        json.dump(dmp, tf, ensure_ascii=False, indent=2)
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

        if st is not None:
            landing = result.get("landing_page")
            pid = result.get("persistentId")
            if not landing and pid:
                landing = f"{base_url.rstrip('/')}/dataset.xhtml?persistentId={pid}"

            if landing:
                msg = "published" if result.get("published") else "draft created"
                st.success(f"✅ Dataverse {msg} — [Open dataset]({landing})")
            else:
                st.info("Dataverse dataset created, but no landing page link was returned.")

            if result.get("sensitive_or_personal"):
                skipped = result.get("skipped_files") or []
                if skipped:
                    st.warning(f"Files not uploaded due to personal/sensitive data: {', '.join(skipped)}")

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
