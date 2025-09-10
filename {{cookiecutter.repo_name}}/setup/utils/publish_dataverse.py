#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import argparse
import json
import os
import tempfile
from typing import Any, Dict, List, Optional, Tuple



from .general_tools import package_installer
from publish_common import (
    PublishError, _get, _norm_list, _guess_dataset,
    _has_personal_or_sensitive, description_from_madmp,
    files_from_x_dcas, regular_files_existing
)


package_installer(required_libraries=["streamlit", "requests"])
import requests
import streamlit as st  # type: ignore


# ========= Dataverse API =========

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

def _dv_upload_file(base_url: str, token: str, dataset_id: int,
                    filepath: str, description: Optional[str] = None,
                    directory_label: Optional[str] = None,
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

# ========= Dataverse field builders =========

def _dv_field(name, value, tclass="primitive", multiple=False):
    return {"typeName": name, "typeClass": tclass, "multiple": multiple, "value": value}

def _dv_authors_from_madmp(ds: dict, dmp: dict) -> List[dict]:
    authors = []
    c = _get(dmp, ["dmp", "contact"]) or dmp.get("contact") or {}
    cname = c.get("name") or c.get("mbox") or "Unknown, Unknown"
    comp = {"authorName": _dv_field("authorName", cname)}
    aff = (c.get("affiliation") or c.get("organization") or {}).get("name") if isinstance(c.get("affiliation") or c.get("organization"), dict) else None
    if aff:
        comp["authorAffiliation"] = _dv_field("authorAffiliation", aff)
    authors.append(_dv_field("author", comp, tclass="compound"))

    for cont in _norm_list(_get(dmp, ["dmp", "contributor"]) or dmp.get("contributor")):
        if not isinstance(cont, dict): continue
        nm = cont.get("name") or cont.get("fullname")
        if not nm: continue
        aff = (cont.get("affiliation") or cont.get("organization") or {}).get("name") if isinstance(cont.get("affiliation") or cont.get("organization"), dict) else None
        comp = {"authorName": _dv_field("authorName", nm)}
        if aff:
            comp["authorAffiliation"] = _dv_field("authorAffiliation", aff)
        authors.append(_dv_field("author", comp, tclass="compound"))
    return authors

def _dv_contacts_from_madmp(ds: dict, dmp: dict) -> List[dict]:
    contacts = []
    for c in _norm_list(ds.get("contact", [])):
        email = c.get("mbox") or c.get("email") or c.get("contactEmail")
        name = c.get("name") or c.get("fullname") or email or "Unknown"
        if email:
            comp = {"datasetContactEmail": _dv_field("datasetContactEmail", email),
                    "datasetContactName": _dv_field("datasetContactName", name)}
            contacts.append({"typeName": "datasetContact", "typeClass": "compound", "multiple": False, "value": comp})
    if contacts:
        return contacts
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

def _dv_description_value(ds: dict, sensitive_flag: bool, skipped_files: List[str]) -> str:
    base = description_from_madmp(ds)
    if sensitive_flag:
        if skipped_files:
            bullet = "\n".join(f"  - {os.path.basename(x)}" for x in skipped_files)
            note = ("\n\n[NOTICE] Files withheld due to personal/sensitive data. "
                    "A metadata-only record has been created. Skipped files:\n" + bullet)
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

    desc_val = _dv_description_value(ds, sensitive_flag, skipped_files or [])
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

# ========= Dataverse publish flow (x_dcas-only) =========

def publish_dataset_to_dataverse(
    dmp_path: str,
    token: str,
    dataverse_alias: str = "tmpdemo",
    base_url: str = "https://dataverse.deic.dk",
    dataset_id_selector: Optional[str] = None,
    publish: bool = False,
    release_type: str = "major"
) -> Dict[str, Any]:

    with open(dmp_path, "r", encoding="utf-8") as fh:
        dmp = json.load(fh)

    ds = _guess_dataset(dmp, dataset_id_selector)
    sensitive = _has_personal_or_sensitive(ds)

    # Authoritative x_dcas files
    xdcas_files = files_from_x_dcas(ds)
    uploads = [] if sensitive else regular_files_existing(xdcas_files)
    skipped_files = xdcas_files if sensitive else []

    dataset_version, extra = build_dataverse_dataset_version_from_madmp(
        dmp, dataset_id_selector, sensitive_flag=sensitive, skipped_files=skipped_files
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
        "sensitive_or_personal": sensitive,
        "published": bool(publish_result),
        "dataset_title": extra.get("dataset_title"),
    }

# ========= Streamlit wrapper =========

def streamlit_publish_to_dataverse(
    *, dataset: dict, dmp: dict, token: str,
    base_url: str = "https://dataverse.deic.dk", alias: str = "tmpdemo",
    publish: bool = False, allow_reused: bool = False, release_type: str = "major",
) -> Dict[str, Any]:
    if str(dataset.get("is_reused", "")).strip().lower() in {"true", "1", "yes"} and not allow_reused:
        raise PublishError("Blocked: dataset is marked re-used (is_reused=true) in the DMP.")
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as tf:
        json.dump(dmp, tf, ensure_ascii=False, indent=2)
        dmp_path = tf.name
    try:
        result = publish_dataset_to_dataverse(
            dmp_path=dmp_path, token=token, dataverse_alias=alias,
            base_url=base_url, dataset_id_selector=dataset.get("title") or None,
            publish=publish, release_type=release_type,
        )
        if st is not None:
            landing = result.get("landing_page")
            pid = result.get("persistentId")
            if not landing and pid:
                landing = f"{base_url.rstrip('/')}/dataset.xhtml?persistentId={pid}"
            if landing:
                msg = "published" if result.get("published") else "draft created"
                st.success(f"✅ Dataverse {msg} — [Open dataset]({landing})")
            if result.get("sensitive_or_personal"):
                skipped = result.get("skipped_files") or []
                if skipped:
                    st.warning(f"Files not uploaded due to personal/sensitive data: {', '.join(skipped)}")
        return result
    finally:
        try: os.unlink(dmp_path)
        except Exception: pass

# ========= CLI =========

def _parse_args():
    p = argparse.ArgumentParser(description="Publish from maDMP to Dataverse (x_dcas only)")
    p.add_argument("--dmp", required=True, help="Path to maDMP JSON")
    p.add_argument("--token", required=True, help="Dataverse API token")
    p.add_argument("--alias", default="tmpdemo", help="Target Dataverse collection alias")
    p.add_argument("--base-url", default="https://dataverse.deic.dk", help="Dataverse base URL")
    p.add_argument("--dataset-id", help="Dataset selector in maDMP (id or title)")
    p.add_argument("--publish", action="store_true", help="Publish after creating (default: draft only)")
    p.add_argument("--release-type", choices=["major", "minor"], default="major", help="Dataverse release type")
    return p.parse_args()

def main():
    args = _parse_args()
    result = publish_dataset_to_dataverse(
        dmp_path=args.dmp, token=args.token, dataverse_alias=args.alias,
        base_url=args.base_url, dataset_id_selector=args.dataset_id,
        publish=args.publish, release_type=args.release_type
    )
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
