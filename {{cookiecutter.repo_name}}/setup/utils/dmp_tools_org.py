from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .toml_tools import *


# ──────────────────────────────────────────────────────────────────────────────
# Time/IO helpers
# ──────────────────────────────────────────────────────────────────────────────

def now_iso_minute() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M")

def load_dmp_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return ensure_dmp_shape({})
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return ensure_dmp_shape(raw)

def save_dmp_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ──────────────────────────────────────────────────────────────────────────────
# Minimal DMP shaping (keeps existing content; fills sensible defaults)
# ──────────────────────────────────────────────────────────────────────────────
def to_bytes_mb(mb) -> Optional[int]:
    try:
        return int(round(float(mb) * 1024 * 1024))
    except Exception:
        return None

def norm_rel_urlish(p: Optional[str]) -> Optional[str]:
    if not p or not isinstance(p, str):
        return None
    p2 = p.strip().replace("\\", "/")
    while p2.startswith("./") or p2.startswith(".\\"):
        p2 = p2[2:]
    return p2 or None

def data_type_from_path(p: str) -> str:
    pp = pathlib.Path(p.replace("\\", "/"))
    parts = list(pp.parts)
    if "data" in parts:
        i = parts.index("data")
        if i + 1 < len(parts):
            return parts[i + 1]
    return "Uncategorised"

def make_dataset_id(title: str, access_or_download_url: Optional[str]) -> dict:
    """
    Always return a valid dataset_id {identifier, type}.
    Uses a stable, local-style identifier if no DOI/URL exists.
    """
    ident_src = norm_rel_urlish(access_or_download_url) or norm_rel_urlish(title) or "untitled"
    return {"identifier": f"local:{ident_src}", "type": "other"}

def ensure_dmp_shape(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure we have a well-formed RDA-DMP container:

      {
        "dmp": {
          "title": ...,
          "language": "en",
          "created": ...,
          "modified": ...,
          "dataset": [],
          "x_ui": {"hide_fields": [...]}
        }
      }

    If legacy {"datasets": [...]} is detected, convert each entry into an
    RDA-DMP dataset (incl. distribution + a generated dataset_id), and keep
    your DCAS extension under x_dcas.

    Requires helper functions defined elsewhere in your module:
      now_iso_minute(), norm_rel_urlish(), to_bytes_mb(), data_type_from_path()
    """
    now = now_iso_minute()

    # ── Case 1: Already a DMP dict -> fill missing top-level defaults
    if isinstance(data.get("dmp"), dict):
        dmp = data["dmp"]
        dmp.setdefault("title", "Replication Package DMP")
        dmp.setdefault("language", "en")
        dmp.setdefault("created", now)
        dmp.setdefault("modified", now)
        dmp.setdefault("dataset", [])

        # Promote legacy hide-fields if present; otherwise ensure the key exists
        dmp.setdefault("x_ui", {})
        if "__hide_fields__" in data:
            if not dmp["x_ui"].get("hide_fields"):
                dmp["x_ui"]["hide_fields"] = data["__hide_fields__"]
        dmp["x_ui"].setdefault("hide_fields", [])

        return {"dmp": dmp}

    # ── Case 2: Legacy structure with "datasets": convert to RDA-DMP datasets
    if isinstance(data.get("datasets"), list):
        issued_now = now
        converted = []
        for old in data["datasets"]:
            title = old.get("data_name") or old.get("destination") or "Untitled dataset"
            issued_ = old.get("created") or issued_now
            modified = old.get("lastest_change") or None

            access_url = norm_rel_urlish(old.get("destination"))
            zip_url    = norm_rel_urlish(old.get("zip_file"))
            formats    = [f.strip(".") for f in (old.get("file_formats") or []) if f]
            byte_size  = to_bytes_mb(old.get("total_size_mb"))

            # Distribution with explicit defaults per RDA-DMP
            distribution = {
                "title": title,
                **({"download_url": zip_url} if zip_url else {}),
                **({"access_url": access_url} if access_url and not zip_url else {}),
                **({"format": formats} if formats else {}),
                **({"byte_size": byte_size} if byte_size is not None else {}),
                "data_access": "open" if old.get("data_files") else "closed",
                "host": {"title": "Project repository"},
                "available_until": None,
                "description": None,
                "license": [],
            }

            ds_obj = {
                # Core dataset fields with safe defaults
                "title": title,
                **({"description": old.get("description")} if old.get("description") else {}),
                **({"issued": issued_} if issued_ else {}),
                **({"modified": modified} if modified else {}),
                "language": None,              # ISO 639-3 (e.g., "eng") if known
                "keyword": [],                 # 0..n
                "type": None,                  # DataCite/COAR/common name if known
                "is_reused": None,             # bool or None
                "personal_data": "unknown",    # yes|no|unknown
                "sensitive_data": "unknown",   # yes|no|unknown
                "preservation_statement": None,
                "data_quality_assurance": [],
                "metadata": [],
                "security_and_privacy": [],
                "technical_resource": [],

                # Required: dataset_id
                "dataset_id": make_dataset_id(title, zip_url or access_url),

                # Distributions
                "distribution": [distribution],

                # Keep your extension
                "x_dcas": {
                    "data_type": old.get("data_type") or data_type_from_path(access_url or ""),
                    "destination": old.get("destination"),
                    "number_of_files": old.get("number_of_files"),
                    "total_size_mb": old.get("total_size_mb"),
                    "file_formats": old.get("file_formats"),
                    "data_files": old.get("data_files"),
                    "data_size_mb": old.get("data_size"),  # legacy name kept
                    "hash": old.get("hash"),
                },
            }
            converted.append(ds_obj)

        dmp = {
            "title": "Replication Package DMP",
            "language": "en",
            "created": issued_now,
            "modified": issued_now,
            "dataset": converted,
            "x_ui": {"hide_fields": data.get("__hide_fields__", [])},
        }
        return {"dmp": dmp}

    # ── Case 3: Fresh empty structure
    return {
        "dmp": {
            "title": "Replication Package DMP",
            "language": "en",
            "created": now,
            "modified": now,
            "dataset": [],
            "x_ui": {"hide_fields": []},
        }
    }

def normalize_dataset_fields(json_path="./datasets.json"):
    """
    Ensure presence of expected RDA-DMP fields on each dataset and distribution.
    (No source/run_command/doi/citation/license in x_dcas—kept minimal.)
    """
    json_path = pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(json_path)
    data = load_dmp_json(json_path)
    dmp = data["dmp"]
    datasets = dmp.get("dataset", [])

    for ds in datasets:
        # --- dataset-level (RDA-DMP) ---
        ds.setdefault("title", "Untitled dataset")
        ds.setdefault("description", None)
        ds.setdefault("issued", None)
        ds.setdefault("modified", None)
        ds.setdefault("language", None)               # ISO 639-3 (e.g., "eng")
        ds.setdefault("keyword", [])
        ds.setdefault("type", None)
        ds.setdefault("is_reused", None)              # bool or None
        ds.setdefault("personal_data", "unknown")     # yes|no|unknown
        ds.setdefault("sensitive_data", "unknown")    # yes|no|unknown
        ds.setdefault("preservation_statement", None)
        ds.setdefault("data_quality_assurance", [])
        ds.setdefault("metadata", [])
        ds.setdefault("security_and_privacy", [])
        ds.setdefault("technical_resource", [])

        # dataset_id (required)
        if not ds.get("dataset_id") or not isinstance(ds.get("dataset_id"), dict):
            dist0 = (ds.get("distribution") or [{}])[0]
            urlish = dist0.get("access_url") or dist0.get("download_url")
            ds["dataset_id"] = make_dataset_id(ds.get("title") or "untitled", urlish)

        # --- distribution(s) (RDA-DMP) ---
        ds.setdefault("distribution", [])
        if not ds["distribution"]:
            ds["distribution"].append({"title": ds["title"]})

        for dist in ds["distribution"]:
            dist.setdefault("title", ds["title"])
            dist.setdefault("access_url", None)
            dist.setdefault("download_url", None)
            dist.setdefault("format", [])
            dist.setdefault("byte_size", None)
            dist.setdefault("data_access", "open")  # open|shared|closed
            dist.setdefault("host", {"title": "Project repository"})
            dist.setdefault("available_until", None)
            dist.setdefault("description", None)
            dist.setdefault("license", [])

        # --- extension (x_dcas) ---
        ds.setdefault("x_dcas", {})
        x = ds["x_dcas"]
        if "data_type" not in x or x["data_type"] in (None, ""):
            hint = (ds.get("distribution") or [{}])[0].get("access_url") or ""
            x["data_type"] = data_type_from_path(hint)
        for k in ["destination", "number_of_files", "total_size_mb",
                  "file_formats", "data_files", "data_size_mb", "hash"]:
            x.setdefault(k, None)

    dmp["dataset"] = datasets
    save_dmp_json(json_path, data)
    return json_path


# ──────────────────────────────────────────────────────────────────────────────
# Small utils for shaping content
# ──────────────────────────────────────────────────────────────────────────────

def _dedupe_tr(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate technical_resource by (title, description) case-insensitive."""
    seen: set[Tuple[str, str]] = set()
    out: List[Dict[str, Any]] = []
    for it in items or []:
        title = str(it.get("title", "")).strip().lower()
        desc = str(it.get("description", "")).strip().lower()
        key = (title, desc)
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out

def _dedupe_contacts(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate contacts by (mbox or contact_id.identifier or name)."""
    seen: set[str] = set()
    out: List[Dict[str, Any]] = []
    for c in items or []:
        ident = (
            str(c.get("mbox") or "").strip().lower()
            or str(((c.get("contact_id") or {}).get("identifier") or "")).strip().lower()
            or str(c.get("name") or "").strip().lower()
        )
        if not ident:
            ident = json.dumps(c, sort_keys=True)
        if ident in seen:
            continue
        seen.add(ident)
        out.append(c)
    return out

def _split_multi(val: Optional[str]) -> List[str]:
    """Split comma/semicolon separated list into normalized entries."""
    if not val or not isinstance(val, str):
        return []
    raw = [p.strip() for p in val.replace(";", ",").split(",")]
    return [p for p in raw if p]

def _build_contacts(cookiecutter: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Build RDA-DMP 'contact' objects from:
      AUTHORS (comma/semicolon separated names),
      ORCIDS (comma/semicolon separated IDs),
      EMAIL (comma/semicolon separated emails)
    """
    authors = _split_multi(cookiecutter.get("AUTHORS"))
    orcids = _split_multi(cookiecutter.get("ORCIDS"))
    emails = _split_multi(cookiecutter.get("EMAIL"))

    n = max(len(authors), len(orcids), len(emails), 1)
    contacts: List[Dict[str, Any]] = []

    def _safe(lst: List[str], i: int) -> Optional[str]:
        if not lst:
            return None
        return lst[i] if i < len(lst) else lst[0]

    for i in range(n):
        name = _safe(authors, i) or "Contact"
        mbox = _safe(emails, i) or "unknown@example.com"
        orcid = _safe(orcids, i)

        contact_id = {"identifier": orcid or "", "type": "orcid" if orcid else "other"}
        contacts.append({
            "contact_id": contact_id,
            "mbox": mbox,
            "name": name,
        })

    return _dedupe_contacts(contacts)

def _build_preservation_statement(cookiecutter: Dict[str, Any]) -> Optional[str]:
    """
    Compose a simple preservation statement from cookiecutter hints (REMOTE_STORAGE/BACKUP).
    Returns None if no useful info is present.
    """
    storage = str(cookiecutter.get("REMOTE_STORAGE") or "").strip()
    backup = str(cookiecutter.get("REMOTE_BACKUP") or "").strip()
    if not storage and not backup:
        return None

    parts = []
    if storage:
        parts.append(f"Data are stored using '{storage}'.")
    if backup:
        parts.append(f"Backups are handled via '{backup}'.")
    parts.append("Integrity and retention are monitored by the project.")
    return " ".join(parts)

def _apply_title_and_project_meta(dmp: Dict[str, Any], cookiecutter: Dict[str, Any]) -> None:
    proj_name = cookiecutter.get("PROJECT_NAME") or cookiecutter.get("REPO_NAME")
    if proj_name:
        dmp["title"] = f"{proj_name} DMP"
    dmp["x_project"] = cookiecutter

def _build_technical_resources(cookiecutter: Dict[str, Any]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []

    def _add(title: str, key: str) -> None:
        val = cookiecutter.get(key)
        if val:
            items.append({"title": title, "description": str(val)})

    _add("Programming language", "PROGRAMMING_LANGUAGE")      # e.g., Python
    #_add("Python version", "PYTHON_VERSION")                   # e.g., Python 3.13.5
    #_add("Environment manager", "PYTHON_ENV_MANAGER")          # e.g., Venv
    #_add("Version control", "VERSION_CONTROL")                 # e.g., Git
    #_add("Code hosting", "CODE_REPO")                          # e.g., GitHub

    return items

def _ensure_distribution_stub(ds: Dict[str, Any]) -> None:
    ds.setdefault("distribution", [])
    if not ds["distribution"]:
        ds["distribution"].append({"title": ds.get("title") or "Dataset"})

def _apply_license_if_missing(ds: Dict[str, Any], data_license: Optional[str]) -> None:
    if not data_license:
        return
    for dist in ds.get("distribution", []):
        lic = dist.get("license") or []
        if not lic:
            dist["license"] = [{"license_ref": data_license}]


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def update_dmp(project_root,json_path: str) -> Path:
    """
    Update DMP with cookiecutter-derived fields:
      - dmp.title & dmp.x_project
      - contacts at DMP and dataset level
      - technical_resource items (deduped)
      - DATA_LICENSE applied to distributions missing a license
      - normalize datasets with missing RDA-DMP subfields
    """
    json_path = project_root / json_path

    # 1) Inputs
    cookiecutter = read_toml_json(folder = str(project_root), json_filename =  "cookiecutter.json" , tool_name = "cookiecutter", toml_path = "pyproject.toml")

    data_license: Optional[str] = (cookiecutter.get("DATA_LICENSE") or "").strip() or None

    # 2) Normalize required dataset fields up-front
    normalize_dataset_fields(json_path)

    # 3) Load DMP
    data = load_dmp_json(json_path)
    dmp = data["dmp"]

    # 4) Top-level updates
    _apply_title_and_project_meta(dmp, cookiecutter)
    tech_items = _build_technical_resources(cookiecutter)
    contacts = _build_contacts(cookiecutter)

    if contacts:
        dmp.setdefault("contact", [])
        dmp["contact"].extend(contacts)
        dmp["contact"] = _dedupe_contacts(dmp["contact"])

    # Optional: Fill a preservation statement at DMP-level if absent
    if not dmp.get("preservation_statement"):
        ps = _build_preservation_statement(cookiecutter)
        if ps:
            dmp["preservation_statement"] = ps

    # 5) Per-dataset updates
    for ds in dmp.get("dataset", []):
        # Add technical resources
        ds["technical_resource"].extend(tech_items)
        ds["technical_resource"] = _dedupe_tr(ds["technical_resource"])

        # Ensure there is at least a distribution stub and apply license
        _ensure_distribution_stub(ds)
        _apply_license_if_missing(ds, data_license)

        # If dataset.type is missing, try to infer from any x_dcas.data_type if present
        x_dcas = ds.get("x_dcas") or {}
        if not ds.get("type") and x_dcas.get("data_type"):
            # Accept the common name (e.g., "00_raw", "02_processed") as a provisional type
            ds["type"] = str(x_dcas["data_type"])

    # 6) Save
    dmp["modified"] = now_iso_minute()
    save_dmp_json(json_path, data)
    return json_path


def main() -> None:
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)

    update_dmp(project_root = project_root,json_path="datasets.json")


if __name__ == "__main__":
    main()
