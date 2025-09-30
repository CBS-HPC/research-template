#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import json
import os
import time
import tempfile
from typing import Any, Dict, List, Optional, Tuple
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Thread

from ..general_tools import package_installer
from .publish import (
    PublishError, RETRY_STATUS, DEFAULT_TIMEOUT,
    ZENODO_MAX_FILES, ZENODO_MAX_TOTAL,ZENODO_ROLE_MAP,UPLOAD_WORKERS ,
    _get, _norm_list, _guess_dataset, _keywords_from_madmp,
    _has_personal_or_sensitive, _normalize_orcid, _affiliation_from_node,
    description_from_madmp, related_identifiers,
    files_from_x_dcas, regular_files_existing, sizes_bytes,
    estimate_zip_total_bytes, append_packaging_note,
    build_packaging_plan, realize_packaging_plan_parallel,
    build_packaging_plan_preserve_first_level,
)

package_installer(required_libraries=["streamlit", "requests"])

import requests
import streamlit as st  # type: ignore

# ========= Zenodo API (URL-based) =========

def _resolve_zenodo_base_url(base_url: Optional[str]) -> str:
    """
    Decide which API base URL to use:
      1) explicit base_url (preferred)
      2) env ZENODO_API_BASE
      4) default to sandbox
    """
    if base_url and base_url.strip():
        return base_url.rstrip("/")

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

def _z_create_deposit(token: str, api_base_url: str) -> dict:
    url = f"{api_base_url.rstrip('/')}/deposit/depositions"
    return _z_request("POST", url, _zenodo_headers(token), {}).json()

def _z_update_metadata(token: str, api_base_url: str, deposition_id: int, metadata: dict) -> dict:
    url = f"{api_base_url.rstrip('/')}/deposit/depositions/{deposition_id}"
    return _z_request("PUT", url, _zenodo_headers(token), {"metadata": metadata}).json()

def _z_publish(token: str, api_base_url: str, deposition_id: int) -> dict:
    url = f"{api_base_url.rstrip('/')}/deposit/depositions/{deposition_id}/actions/publish"
    return _z_request("POST", url, _zenodo_headers(token), None).json()

# ========= Parallel uploads =========

def _upload_one(token: str, bucket_url: str, filepath: str):
    headers = {"Authorization": f"Bearer {token}"}
    with open(filepath, "rb") as f:
        r = requests.put(f"{bucket_url}/{os.path.basename(filepath)}", data=f, headers=headers)
    if not r.ok:
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise PublishError(f"Zenodo upload failed for {filepath}: {detail}")
    return os.path.basename(filepath)

def _upload_many_parallel(token: str, bucket_url: str, paths: List[str]) -> List[str]:
    uploaded = []
    errors = []
    if not paths:
        return uploaded
    with ThreadPoolExecutor(max_workers=UPLOAD_WORKERS) as ex:
        futs = {ex.submit(_upload_one, token, bucket_url, p): p for p in paths}
        for fut in as_completed(futs):
            try:
                uploaded.append(fut.result())
            except Exception as e:
                errors.append((futs[fut], e))
    if errors:
        first = errors[0][1]
        failed = ", ".join(os.path.basename(p) for p, _ in errors[:10])
        raise PublishError(f"Some uploads failed: {failed} ... (showing up to 10). First error: {first}")
    return uploaded

# ========= Zenodo-specific metadata =========

def _role_to_zenodo_type(role_texts: List[str]) -> str:
    if not role_texts:
        return "Researcher"
    for r in role_texts:
        key = (r or "").strip().lower()
        if key in ZENODO_ROLE_MAP:
            return ZENODO_ROLE_MAP[key]
    return "Researcher"

def _contributors_for_zenodo_from_madmp(dmp: dict, ds: dict) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    def _iter_contrib_blocks():
        yield from _norm_list(_get(dmp, ["dmp", "contributor"]) or dmp.get("contributor"))
        yield from _norm_list(ds.get("contributor"))
    for c in _iter_contrib_blocks():
        if not isinstance(c, dict):
            continue
        name = c.get("name") or c.get("fullname")
        if not name: continue
        roles = [x for x in _norm_list(c.get("role")) if isinstance(x, str)]
        ztype = _role_to_zenodo_type(roles)
        orcid = None
        cid = c.get("contributor_id") or c.get("contact_id") or {}
        if (cid.get("type") or "").lower() == "orcid":
            orcid = _normalize_orcid(cid.get("identifier"))
        aff_name, aff_ror = _affiliation_from_node(c.get("affiliation") or c.get("organization"))
        item: Dict[str, Any] = {"name": name, "type": ztype}
        if aff_name: item["affiliation"] = aff_name
        if orcid: item["orcid"] = orcid
        if aff_name and aff_ror:
            item["affiliation_identifiers"] = [{"scheme":"ror","identifier":aff_ror}]
        out.append(item)
    seen = set(); deduped = []
    for x in out:
        k = (x.get("name"), x.get("type"), x.get("affiliation"))
        if k not in seen:
            seen.add(k); deduped.append(x)
    return deduped

def _license_from_madmp(ds: dict) -> Optional[str]:
    def _map_text_to_zenodo_id(txt: Optional[str]) -> Optional[str]:
        if not txt:
            return None
        t = str(txt).strip().lower()
        if "creativecommons.org" in t:
            if "/publicdomain/zero/" in t or "/cc0/" in t:
                return "cc0-1.0"
            parts = [p for p in t.split("/") if p]
            try:
                kind = parts[-2]
                ver = parts[-1]
                if all(ch.isdigit() or ch == "." for ch in ver):
                    return f"cc-{kind}-{ver}"
            except Exception:
                pass
        s = t.replace("_","-").replace("license","").strip().replace(" ","-")
        cc_map = {
            "cc-by-4.0":"cc-by-4.0","cc-by-sa-4.0":"cc-by-sa-4.0","cc-by-nd-4.0":"cc-by-nd-4.0",
            "cc-by-nc-4.0":"cc-by-nc-4.0","cc-by-nc-sa-4.0":"cc-by-nc-sa-4.0","cc-by-nc-nd-4.0":"cc-by-nc-nd-4.0",
            "cc0-1.0":"cc0-1.0","cc-0-1.0":"cc0-1.0","cc-zero-1.0":"cc0-1.0","cc-zero":"cc0-1.0"
        }
        if s in cc_map:
            return cc_map[s]
        if s in {"cc-by","cc-by-sa","cc-by-nd","cc-by-nc","cc-by-nc-sa","cc-by-nc-nd"}:
            return f"{s}-4.0"
        spdx_map = {
            "mit":"mit","apache-2.0":"apache-2.0","gpl-3.0":"gpl-3.0","gpl-2.0":"gpl-2.0",
            "bsd-3-clause":"bsd-3-clause","bsd-2-clause":"bsd-2-clause","lgpl-3.0":"lgpl-3.0",
            "mpl-2.0":"mpl-2.0","epl-2.0":"epl-2.0","artistic-2.0":"artistic-2.0"
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
                    m = _map_text_to_zenodo_id(v)
                    if m:
                        cand = m if not cand else cand
            elif isinstance(r, str):
                m = _map_text_to_zenodo_id(r)
                if m:
                    cand = m if not cand else cand
        if cand:
            break

    if not cand:
        for r in _norm_list(ds.get("rights", [])):
            if isinstance(r, dict):
                for k in ("license", "rightsUri", "spdx", "title"):
                    v = r.get(k)
                    m = _map_text_to_zenodo_id(v)
                    if m:
                        cand = m if not cand else cand
            elif isinstance(r, str):
                m = _map_text_to_zenodo_id(r)
                if m:
                    cand = m if not cand else cand
            if cand:
                break

    return cand

def _access_right_from_madmp(ds: dict, files_exist: bool) -> Tuple[str, Optional[str]]:
    """
    - If no files OR personal/sensitive → 'closed'
    - Else read distribution.data_access ∈ {open, shared, closed}
    - Embargo if license.start_date is a future date
    """

    def _first_distribution(ds: dict) -> dict:
        d = ds.get("distribution")
        if isinstance(d, dict):
            return d
        if isinstance(d, list) and d:
            return d[0]
        return {}

    def _first_license(dist: dict) -> dict:
        l = dist.get("license")
        if isinstance(l, dict):
            return l
        if isinstance(l, list) and l:
            return l[0]
        return {}

    if (not files_exist) or _has_personal_or_sensitive(ds):
        return "closed", None

    dist = _first_distribution(ds)
    access = (dist.get("data_access") or "").strip().lower()

    # map to publisher vocabulary
    if access == "open":
        base = "open"
    elif access == "shared":
        base = "restricted"
    elif access == "closed":
        base = "closed"
    else:
        base = "open"  # default

    # single license, optional embargo
    lic = _first_license(dist)
    embargo_date = None
    sd = (lic.get("start_date") or "").strip()
    if sd:
        try:
            if date.fromisoformat(sd) > date.today():
                embargo_date = sd
        except Exception:
            pass

    if embargo_date and base != "closed":
        base = "embargoed"

    return base, embargo_date

def build_zenodo_metadata_from_madmp_old(
    dmp: dict,
    dataset_id: Optional[str],
    *,
    files_exist: bool,
    sensitive_flag: bool,
    skipped_files: Optional[List[str]] = None,
) -> Tuple[dict, dict]:
    ds = _guess_dataset(dmp, dataset_id)
    title = ds.get("title") or _get(dmp, ["dmp", "title"]) or "Untitled dataset"
    description = description_from_madmp(ds)

    creators = [{
        "name": (_get(dmp, ["dmp","contact","name"]) or _get(dmp, ["contact","name"])
                 or _get(dmp, ["dmp","contact","mbox"]) or "Unknown, Unknown")
    }]
    c = _get(dmp, ["dmp","contact"]) or dmp.get("contact") or {}
    cid = c.get("contact_id") or {}
    if (cid.get("type") or "").lower() == "orcid":
        oc = _normalize_orcid(cid.get("identifier"))
        if oc: creators[0]["orcid"] = oc
    aff_name, aff_ror = _affiliation_from_node(c.get("affiliation") or c.get("organization"))
    if aff_name:
        creators[0]["affiliation"] = aff_name
    if aff_name and aff_ror:
        creators[0]["affiliation_identifiers"] = [{"scheme":"ror","identifier":aff_ror}]

    contributors = _contributors_for_zenodo_from_madmp(dmp, ds)
    keywords = _keywords_from_madmp(ds)
    license_id = _license_from_madmp(ds)
    access_right, embargo_date = _access_right_from_madmp(ds, files_exist=files_exist)
    rel_ids = related_identifiers(ds)

    dsid = ds.get("dataset_id") or {}
    if isinstance(dsid, dict) and (dsid.get("type") or "").lower() == "doi":
        doi_val = dsid.get("identifier")
        if isinstance(doi_val, str) and doi_val.strip():
            rel_ids = rel_ids or []
            rel_ids.append({"identifier": doi_val.strip(), "relation":"isAlternateIdentifier", "scheme":"doi"})

    lang = ds.get("language") or _get(dmp, ["dmp", "language"])
    language = lang.strip() if isinstance(lang, str) and lang.strip() else None

    if sensitive_flag:
        skipped = skipped_files or []
        if skipped:
            bullet = "\n".join(f"  - {os.path.basename(x)}" for x in skipped)
            note = ("\n\n[NOTICE] Files withheld due to personal/sensitive data. "
                    "A metadata-only record has been created. Skipped files:\n" + bullet)
        else:
            note = ("\n\n[NOTICE] Files withheld due to personal/sensitive data. "
                    "A metadata-only record has been created.")
        description = (description or "No description provided.") + note

    md: Dict[str, Any] = {
        "title": title,
        "upload_type": "dataset",
        "description": description or "No description provided.",
        "creators": creators,
    }
    if contributors: md["contributors"] = contributors
    if keywords: md["keywords"] = keywords
    if license_id: md["license"] = license_id
    if access_right: md["access_right"] = access_right
    if embargo_date and access_right == "embargoed":
        md["embargo_date"] = embargo_date
    if rel_ids: md["related_identifiers"] = rel_ids
    if language: md["language"] = language

    communities = []
    for ext_name in ("extension", "extensions", "x_dcas"):
        for ext in _norm_list(ds.get(ext_name, [])):
            if isinstance(ext, dict):
                comm = ext.get("community") or ext.get("zenodo_community")
                if comm:
                    communities.append({"identifier": comm})
    if communities:
        md["communities"] = communities[:5]

    return md, {"dataset_title": title, "license": license_id, "access_right": access_right}

def streamlit_publish_to_zenodo_old(
    *, dataset: dict, dmp: dict, token: str,
    base_url: Optional[str] = None,  # <— NEW preferred way
    publish: bool = False, allow_reused: bool = False,
) -> Dict[str, Any]:
    """
    Create a Zenodo deposition with full metadata at creation time, then
    finish packaging (zips), upload files, and optionally publish in the background.

    Pass a full API base URL (e.g. https://sandbox.zenodo.org/api or https://zenodo.org/api).
    If omitted, resolves from env ZENODO_API_BASE, else sandbox default.
    """
    if str(dataset.get("is_reused", "")).strip().lower() in {"true", "1", "yes"} and not allow_reused:
        raise PublishError("Blocked: dataset is marked re-used (is_reused=true) in the DMP.")

    api_base = _resolve_zenodo_base_url(base_url)

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as tf:
        json.dump(dmp, tf, ensure_ascii=False, indent=2)
        dmp_path = tf.name

    # Precompute metadata (plan only, no zips yet)
    with open(dmp_path, "r", encoding="utf-8") as fh:
        _dmp_pre = json.load(fh)
    ds_pre = _guess_dataset(_dmp_pre, dataset.get("title") or None)

    xdcas_files = files_from_x_dcas(ds_pre)
    sensitive   = _has_personal_or_sensitive(ds_pre)
    uploads_raw = [] if sensitive else regular_files_existing(xdcas_files)
    skipped_files = xdcas_files if sensitive else []
    pre_total, _ = sizes_bytes(uploads_raw)
    pre_count    = len(uploads_raw)

    packaging_report: List[dict] = []
    planned_final_paths: List[str] = uploads_raw[:]

    if not sensitive and pre_count > 0:
        if pre_total > ZENODO_MAX_TOTAL:
            est = estimate_zip_total_bytes(uploads_raw, pre_total)
            if est > ZENODO_MAX_TOTAL:
                # metadata-only draft — show note but don't imply uploads
                planned_final_paths = []
                packaging_report = []
        if planned_final_paths and (pre_count > ZENODO_MAX_FILES or pre_total > ZENODO_MAX_TOTAL or pre_count > 20):
            plan, packaging_report, _workdir = build_packaging_plan_preserve_first_level(uploads_raw)
            planned_final_paths = [(p.zip_path if p.kind == "zip" else p.path) for p in plan]

    files_exist_expected = (len(planned_final_paths) > 0) and not sensitive
    metadata, _extra = build_zenodo_metadata_from_madmp(
        _dmp_pre, dataset.get("title") or None,
        files_exist=files_exist_expected, sensitive_flag=sensitive, skipped_files=skipped_files,
    )
    metadata["description"] = append_packaging_note(
        metadata.get("description") or "",
        pre_files=pre_count, pre_bytes=pre_total,
        final_paths=planned_final_paths, report=packaging_report
    )

    # Create deposition WITH metadata so the draft shows everything right away
    dep = _z_request(
        "POST",
        f"{api_base.rstrip('/')}/deposit/depositions",
        _zenodo_headers(token),
        json_payload={"metadata": metadata},
        timeout=DEFAULT_TIMEOUT,
    ).json()

    deposition_id = dep.get("id")
    links = dep.get("links") or {}
    bucket_url = links.get("bucket")
    html_url   = links.get("html") or links.get("latest_html")
    if not deposition_id or not bucket_url:
        try: os.unlink(dmp_path)
        except Exception: pass
        raise PublishError("Could not obtain Zenodo deposition bucket/link.")

    if st is not None:
        st.success(f"✅ Zenodo deposition created (metadata set). Background upload will now start. [Open in Zenodo]({html_url})")

    # Background worker: realize packaging, upload, optionally publish
    def _worker_upload_then_publish():
        try:
            with open(dmp_path, "r", encoding="utf-8") as fh:
                _dmp = json.load(fh)
            ds = _guess_dataset(_dmp, dataset.get("title") or None)

            xdcas_files_w = files_from_x_dcas(ds)
            sensitive_w   = _has_personal_or_sensitive(ds)
            uploads_raw_w = [] if sensitive_w else regular_files_existing(xdcas_files_w)
            pre_total_w, _  = sizes_bytes(uploads_raw_w)
            pre_count_w     = len(uploads_raw_w)

            final_uploads: List[str] = uploads_raw_w
            if not sensitive_w and pre_count_w > 0:
                if pre_total_w > ZENODO_MAX_TOTAL:
                    est_w = estimate_zip_total_bytes(uploads_raw_w, pre_total_w)
                    if est_w > ZENODO_MAX_TOTAL:
                        final_uploads = []
                if final_uploads and (pre_count_w > ZENODO_MAX_FILES or pre_total_w > ZENODO_MAX_TOTAL or pre_count_w > 20):
                    plan_w, _report_w, _workdir_w = build_packaging_plan_preserve_first_level(uploads_raw_w)
                    final_uploads = realize_packaging_plan_parallel(plan_w)

            if final_uploads:
                _upload_many_parallel(token, bucket_url, final_uploads)

            if publish:
                _z_publish(token, api_base, deposition_id)

        except Exception:
            # swallow/log as needed
            pass
        finally:
            try: os.unlink(dmp_path)
            except Exception: pass

    Thread(target=_worker_upload_then_publish, daemon=True).start()

def build_zenodo_metadata_from_madmp(
    dmp: dict,
    dataset_id: Optional[str],
    *,
    files_exist: bool,
    sensitive_flag: bool,
    skipped_files: Optional[List[str]] = None,
) -> Tuple[dict, dict]:
     
    ds = _guess_dataset(dmp, dataset_id)
    title = ds.get("title") or _get(dmp, ["dmp", "title"]) or "Untitled dataset"
    description = description_from_madmp(ds)

    creators = [{
        "name": (_get(dmp, ["dmp","contact","name"]) or _get(dmp, ["contact","name"])
                 or _get(dmp, ["dmp","contact","mbox"]) or "Unknown, Unknown")
    }]
    c = _get(dmp, ["dmp","contact"]) or dmp.get("contact") or {}
    cid = c.get("contact_id") or {}
    if (cid.get("type") or "").lower() == "orcid":
        oc = _normalize_orcid(cid.get("identifier"))
        if oc: creators[0]["orcid"] = oc
    aff_name, aff_ror = _affiliation_from_node(c.get("affiliation") or c.get("organization"))
    if aff_name:
        creators[0]["affiliation"] = aff_name
    if aff_name and aff_ror:
        creators[0]["affiliation_identifiers"] = [{"scheme":"ror","identifier":aff_ror}]

    contributors = _contributors_for_zenodo_from_madmp(dmp, ds)
    keywords = _keywords_from_madmp(ds)
    license_id = _license_from_madmp(ds)
    access_right, embargo_date = _access_right_from_madmp(ds, files_exist=files_exist)
    rel_ids = related_identifiers(ds)

    dsid = ds.get("dataset_id") or {}
    if isinstance(dsid, dict) and (dsid.get("type") or "").lower() == "doi":
        doi_val = dsid.get("identifier")
        if isinstance(doi_val, str) and doi_val.strip():
            rel_ids = rel_ids or []
            rel_ids.append({"identifier": doi_val.strip(), "relation":"isAlternateIdentifier", "scheme":"doi"})

    lang = ds.get("language") or _get(dmp, ["dmp", "language"])
    language = lang.strip() if isinstance(lang, str) and lang.strip() else None

    if sensitive_flag:
        skipped = skipped_files or []
        if skipped:
            bullet = "\n".join(f"  - {os.path.basename(x)}" for x in skipped)
            note = ("\n\n[NOTICE] Files withheld due to personal/sensitive data. "
                    "A metadata-only record has been created. Skipped files:\n" + bullet)
        else:
            note = ("\n\n[NOTICE] Files withheld due to personal/sensitive data. "
                    "A metadata-only record has been created.")
        description = (description or "No description provided.") + note

    md: Dict[str, Any] = {
        "title": title,
        "upload_type": "dataset",
        "description": description or "No description provided.",
        "creators": creators,
    }
    if contributors: md["contributors"] = contributors
    if keywords: md["keywords"] = keywords
    if license_id: md["license"] = license_id
    if access_right: md["access_right"] = access_right
    if embargo_date and access_right == "embargoed":
        md["embargo_date"] = embargo_date
    if rel_ids: md["related_identifiers"] = rel_ids
    if language: md["language"] = language

    communities = []
    for ext_name in ("extension", "extensions", "x_dcas"):
        for ext in _norm_list(ds.get(ext_name, [])):
            if isinstance(ext, dict):
                comm = ext.get("community") or ext.get("zenodo_community")
                if comm:
                    communities.append({"identifier": comm})
    if communities:
        md["communities"] = communities[:5]

    return md, {"dataset_title": title, "license": license_id, "access_right": access_right}

def _merge_community_into_metadata(md: Dict[str, Any], community: Optional[str]) -> None:
    """
    Insert a community identifier into md['communities'] if provided, avoiding
    duplicates and respecting Zenodo's limit (we keep at most 5 entries).
    """
    slug = (community or "").strip()
    if not slug:
        return
    current = []
    for c in md.get("communities", []):
        if isinstance(c, dict) and c.get("identifier"):
            current.append(c["identifier"])
    if slug not in current:
        md.setdefault("communities", [])
        md["communities"].insert(0, {"identifier": slug})
        # keep only the first 5
        if len(md["communities"]) > 5:
            md["communities"] = md["communities"][:5]

def streamlit_publish_to_zenodo(
    *,
    dataset: dict,
    dmp: dict,
    token: str,
    base_url: Optional[str] = None,   # full API base URL
    community: Optional[str] = None,  # <— NEW: optional Zenodo community slug
    publish: bool = False,
    allow_reused: bool = False,
) -> Dict[str, Any]:
    """
    Create a Zenodo deposition with full metadata at creation time, then
    finish packaging (zips), upload files, and optionally publish in the background.

    Pass a full API base URL (e.g. https://sandbox.zenodo.org/api or https://zenodo.org/api).
    If omitted, resolves from env ZENODO_API_BASE, else sandbox default.

    If `community` is provided (or env ZENODO_COMMUNITY is set), it is injected
    into the outgoing metadata under `communities`.
    """
    if str(dataset.get("is_reused", "")).strip().lower() in {"true", "1", "yes"} and not allow_reused:
        raise PublishError("Blocked: dataset is marked re-used (is_reused=true) in the DMP.")

    api_base = _resolve_zenodo_base_url(base_url)

    # Fallback to env if parameter not provided
    if not community:
        env_comm = os.environ.get("ZENODO_COMMUNITY", "").strip()
        community = env_comm or None

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as tf:
        json.dump(dmp, tf, ensure_ascii=False, indent=2)
        dmp_path = tf.name

    # Precompute metadata (plan only, no zips yet)
    with open(dmp_path, "r", encoding="utf-8") as fh:
        _dmp_pre = json.load(fh)
    ds_pre = _guess_dataset(_dmp_pre, dataset.get("title") or None)

    xdcas_files = files_from_x_dcas(ds_pre)
    sensitive   = _has_personal_or_sensitive(ds_pre)
    uploads_raw = [] if sensitive else regular_files_existing(xdcas_files)
    skipped_files = xdcas_files if sensitive else []
    pre_total, _ = sizes_bytes(uploads_raw)
    pre_count    = len(uploads_raw)

    packaging_report: List[dict] = []
    planned_final_paths: List[str] = uploads_raw[:]

    if not sensitive and pre_count > 0:
        if pre_total > ZENODO_MAX_TOTAL:
            est = estimate_zip_total_bytes(uploads_raw, pre_total)
            if est > ZENODO_MAX_TOTAL:
                planned_final_paths = []
                packaging_report = []
        if planned_final_paths and (pre_count > ZENODO_MAX_FILES or pre_total > ZENODO_MAX_TOTAL or pre_count > 20):
            plan, packaging_report, _workdir = build_packaging_plan_preserve_first_level(uploads_raw)
            planned_final_paths = [(p.zip_path if p.kind == "zip" else p.path) for p in plan]

    files_exist_expected = (len(planned_final_paths) > 0) and not sensitive
    metadata, _extra = build_zenodo_metadata_from_madmp(
        _dmp_pre, dataset.get("title") or None,
        files_exist=files_exist_expected, sensitive_flag=sensitive, skipped_files=skipped_files,
    )
    metadata["description"] = append_packaging_note(
        metadata.get("description") or "",
        pre_files=pre_count, pre_bytes=pre_total,
        final_paths=planned_final_paths, report=packaging_report,
    )

    # NEW: merge explicit (or env) community into metadata
    _merge_community_into_metadata(metadata, community)

    # Create deposition WITH metadata so the draft shows everything right away
    dep = _z_request(
        "POST",
        f"{api_base.rstrip('/')}/deposit/depositions",
        _zenodo_headers(token),
        json_payload={"metadata": metadata},
        timeout=DEFAULT_TIMEOUT,
    ).json()

    deposition_id = dep.get("id")
    links = dep.get("links") or {}
    bucket_url = links.get("bucket")
    html_url   = links.get("html") or links.get("latest_html")
    if not deposition_id or not bucket_url:
        try: os.unlink(dmp_path)
        except Exception: pass
        raise PublishError("Could not obtain Zenodo deposition bucket/link.")

    if st is not None:
        st.success(f"✅ Zenodo deposition created (metadata set). Background upload will now start. [Open in Zenodo]({html_url})")

    def _worker_upload_then_publish():
        try:
            with open(dmp_path, "r", encoding="utf-8") as fh:
                _dmp = json.load(fh)
            ds = _guess_dataset(_dmp, dataset.get("title") or None)

            xdcas_files_w = files_from_x_dcas(ds)
            sensitive_w   = _has_personal_or_sensitive(ds)
            uploads_raw_w = [] if sensitive_w else regular_files_existing(xdcas_files_w)
            pre_total_w, _  = sizes_bytes(uploads_raw_w)
            pre_count_w     = len(uploads_raw_w)

            final_uploads: List[str] = uploads_raw_w
            if not sensitive_w and pre_count_w > 0:
                if pre_total_w > ZENODO_MAX_TOTAL:
                    est_w = estimate_zip_total_bytes(uploads_raw_w, pre_total_w)
                    if est_w > ZENODO_MAX_TOTAL:
                        final_uploads = []
                if final_uploads and (pre_count_w > ZENODO_MAX_FILES or pre_total_w > ZENODO_MAX_TOTAL or pre_count_w > 20):
                    plan_w, _report_w, _workdir_w = build_packaging_plan_preserve_first_level(uploads_raw_w)
                    final_uploads = realize_packaging_plan_parallel(plan_w)

            if final_uploads:
                _upload_many_parallel(token, bucket_url, final_uploads)

            if publish:
                _z_publish(token, api_base, deposition_id)

        except Exception:
            pass
        finally:
            try: os.unlink(dmp_path)
            except Exception: pass

    Thread(target=_worker_upload_then_publish, daemon=True).start()
    # (keep existing return behavior if any)


