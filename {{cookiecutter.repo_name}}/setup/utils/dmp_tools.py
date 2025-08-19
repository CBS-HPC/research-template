import json
import os
import urllib.request
import pathlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .toml_tools import read_toml_json


# ──────────────────────────────────────────────────────────────────────────────
# Config (RDA-DMP 1.0)
# ──────────────────────────────────────────────────────────────────────────────

SCHEMA_URL = (
    "https://raw.githubusercontent.com/RDA-DMP-Common/RDA-DMP-Common-Standard/"
    "master/examples/JSON/JSON-schema/1.0/maDMP-schema-1.0.json"
)

# Always store this exact value in dmp["schema"]
RDA_DMP_SCHEMA_URL = (
    "https://github.com/RDA-DMP-Common/RDA-DMP-Common-Standard/"
    "tree/master/examples/JSON/JSON-schema/1.0"
)

DEFAULT_SCHEMA_CACHE = Path("./bin/maDMP-schema-1.0.json")

DEFAULT_DMP_PATH = Path("./datasets.json")

DMP_KEY_ORDER = [
    "schema",
    "title",
    "description",
    "language",
    "created",
    "modified",
    "ethical_issues_exist",
    "ethical_issues_description",
    "ethical_issues_report",
    "dmp_id",
    "contact",
    "project",
    "dataset",
    "extension",
]

def now_iso_minute() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M")

def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def fetch_schema(schema_url: str = SCHEMA_URL,
                 cache_path: Path = DEFAULT_SCHEMA_CACHE,
                 force: bool = False) -> Dict[str, Any]:
    """Download the schema (or use cached copy)."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists() and not force:
        with cache_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    with urllib.request.urlopen(schema_url) as resp:
        raw = resp.read().decode("utf-8")
    data = json.loads(raw)
    with cache_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return data

def _resolve_ref(schema: Dict[str, Any], ref: str) -> Dict[str, Any]:
    """Resolve an internal JSON Pointer like '#/definitions/Dataset'."""
    if not ref.startswith("#/"):
        return {}
    node: Any = schema
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        node = node.get(part, {})
    return node if isinstance(node, dict) else {}

def _deref(schema: Dict[str, Any], node: Dict[str, Any]) -> Dict[str, Any]:
    """Return node with $ref resolved (one level); shallow merge with local overrides."""
    if "$ref" in node:
        base = _resolve_ref(schema, node["$ref"])
        merged = dict(base)
        merged.update({k: v for k, v in node.items() if k != "$ref"})
        return merged
    return node

def _resolve_first(schema: Dict[str, Any], candidates: List[str]) -> Dict[str, Any]:
    """Try multiple $ref candidates and return the first that resolves."""
    for c in candidates:
        node = _resolve_ref(schema, c)
        if node:
            return node
    return {}

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
    parts = Path(p.replace("\\", "/")).parts
    if "data" in parts:
        i = parts.index("data")
        if i + 1 < len(parts):
            return parts[i + 1]
    return "Uncategorised"

def make_dataset_id(title: str, access_or_download_url: Optional[str]) -> dict:
    """
    Always return a valid dataset_id {identifier, type}.
    Uses a stable local-style identifier if no DOI/URL exists.
    """
    ident_src = norm_rel_urlish(access_or_download_url) or norm_rel_urlish(title) or "untitled"
    return {"identifier": f"local:{ident_src}", "type": "other"}

def _ensure_extension(obj: Dict[str, Any]) -> List[Dict[str, Any]]:
    obj.setdefault("extension", [])
    return obj["extension"]

def _find_extension_index(obj: Dict[str, Any], key: str) -> int:
    ext = obj.get("extension") or []
    for i, item in enumerate(ext):
        if isinstance(item, dict) and key in item:
            return i
    return -1

def _get_extension_payload(obj: Dict[str, Any], key: str) -> Optional[Dict[str, Any]]:
    i = _find_extension_index(obj, key)
    if i == -1:
        return None
    payload = obj["extension"][i].get(key)
    return payload if isinstance(payload, dict) else None

def _set_extension_payload(obj: Dict[str, Any], key: str, payload: Dict[str, Any]) -> None:
    ext = _ensure_extension(obj)
    i = _find_extension_index(obj, key)
    if i == -1:
        ext.append({key: dict(payload)})
    else:
        if not isinstance(ext[i][key], dict):
            ext[i][key] = dict(payload)
        else:
            ext[i][key].update({k: v for k, v in payload.items()})

def _default_for_schema(schema: Dict[str, Any], node: Dict[str, Any]) -> Any:
    """
    Best-effort default constructor from a JSON Schema node.
    - objects  -> {}
    - arrays   -> []
    - string/number/integer/boolean -> None (unknown)
    - enums -> None (let caller decide)
    - $ref resolved one level
    """
    node = _deref(schema, node)

    if "default" in node:
        return node["default"]

    typ = node.get("type")
    if isinstance(typ, list):
        if "object" in typ:
            typ = "object"
        elif "array" in typ:
            typ = "array"
        else:
            typ = typ[0]

    if typ == "object":
        return {}
    if typ == "array":
        return []
    if typ in {"string", "number", "integer", "boolean"}:
        return None

    if "$ref" in node:
        return _default_for_schema(schema, node)

    return None

def _ensure_object_fields_from_schema(target: Dict[str, Any],
                                      schema: Dict[str, Any],
                                      obj_schema: Dict[str, Any],
                                      prefill: Dict[str, Any] | None = None) -> None:
    """
    Ensure keys exist on target based on 'properties' of obj_schema.
    Values are best-effort defaults; existing values are preserved.
    """
    obj_schema = _deref(schema, obj_schema)
    props = obj_schema.get("properties", {})
    for key, prop_schema in props.items():
        if key not in target:
            target[key] = _default_for_schema(schema, prop_schema)
    for key in obj_schema.get("required", []):
        target.setdefault(key, None)
    if prefill:
        for k, v in prefill.items():
            target.setdefault(k, v)

def ensure_dmp_shape(data: Dict[str, Any],
                     schema: Optional[Dict[str, Any]] = None,
                     **_: Any) -> Dict[str, Any]:
    """
    Ensure a well-formed RDA-DMP container. We always set dmp["schema"] to the
    GitHub 'tree' URL for the 1.0 schema (as requested).
    Also migrates legacy:
      - dataset["x_dcas"]  -> dataset["extension"] [{"x_dcas": {...}}]
      - dmp["x_ui"]        -> dmp["extension"] [{"x_ui": {...}}]
      - dmp["x_project"]   -> dmp["extension"] [{"x_project": {...}}]
    """
    now = now_iso_minute()

    # Case 1: already DMP-shaped
    if isinstance(data.get("dmp"), dict):
        dmp = data["dmp"]
        dmp.setdefault("title", "Replication Package DMP")
        dmp.setdefault("description", None)
        dmp.setdefault("language", "en")
        dmp.setdefault("created", now)
        dmp.setdefault("modified", now)
        dmp.setdefault("ethical_issues_exist", "unknown")
        dmp.setdefault("ethical_issues_description", None)
        dmp.setdefault("ethical_issues_report", None)
        dmp.setdefault("dmp_id", None)
        dmp.setdefault("contact", None)  # object in 1.0
        dmp.setdefault("project", [])
        dmp.setdefault("dataset", [])
        dmp["schema"] = RDA_DMP_SCHEMA_URL  # enforce exact link

        # Migrate top-level custom fields to root extension
        if isinstance(dmp.get("x_ui"), dict):
            _set_extension_payload(dmp, "x_ui", dmp.pop("x_ui"))
        if "__hide_fields__" in data:
            cur = _get_extension_payload(dmp, "x_ui") or {}
            cur.setdefault("hide_fields", data["__hide_fields__"])
            _set_extension_payload(dmp, "x_ui", cur)
        if isinstance(dmp.get("x_project"), dict):
            _set_extension_payload(dmp, "x_project", dmp.pop("x_project"))

        # Migrate legacy dataset.x_dcas => dataset.extension[{"x_dcas": {...}}]
        for ds in dmp.get("dataset", []):
            if isinstance(ds.get("x_dcas"), dict):
                _set_extension_payload(ds, "x_dcas", ds.pop("x_dcas"))

        return {"dmp": dmp}

    # Case 2: legacy {"datasets": [...]}
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

            x_dcas_payload = {
                "data_type": old.get("data_type") or data_type_from_path(access_url or ""),
                "destination": old.get("destination"),
                "number_of_files": old.get("number_of_files"),
                "total_size_mb": old.get("total_size_mb"),
                "file_formats": old.get("file_formats"),
                "data_files": old.get("data_files"),
                "data_size_mb": old.get("data_size"),
                "hash": old.get("hash"),
            }

            ds_obj = {
                "title": title,
                **({"description": old.get("description")} if old.get("description") else {}),
                **({"issued": issued_} if issued_ else {}),
                **({"modified": modified} if modified else {}),
                "language": None,
                "keyword": [],
                "type": None,
                "is_reused": None,
                "personal_data": "unknown",
                "sensitive_data": "unknown",
                "preservation_statement": None,
                "data_quality_assurance": [],
                "metadata": [],
                "security_and_privacy": [],
                "technical_resource": [],
                "dataset_id": make_dataset_id(title, zip_url or access_url),
                "distribution": [distribution],
                "extension": [ {"x_dcas": x_dcas_payload} ],
            }
            converted.append(ds_obj)

        dmp = {
            "schema": RDA_DMP_SCHEMA_URL,
            "title": "Replication Package DMP",
            "description": None,
            "language": "en",
            "created": issued_now,
            "modified": issued_now,
            "ethical_issues_exist": "unknown",
            "ethical_issues_description": None,
            "ethical_issues_report": None,
            "dmp_id": None,
            "contact": None,
            "project": [],
            "dataset": converted,
            "extension": [
                {"x_ui": {"hide_fields": data.get("__hide_fields__", [])}}
            ],
        }
        return {"dmp": dmp}

    # Case 3: fresh
    return {
        "dmp": {
            "schema": RDA_DMP_SCHEMA_URL,
            "title": "Replication Package DMP",
            "description": None,
            "language": "en",
            "created": now,
            "modified": now,
            "ethical_issues_exist": "unknown",
            "ethical_issues_description": None,
            "ethical_issues_report": None,
            "dmp_id": None,
            "contact": None,
            "project": [],
            "dataset": [],
            "extension": [
                {"x_ui": {"hide_fields": []}}
            ],
        }
    }

def normalize_root_in_place(data: Dict[str, Any],
                            schema: Optional[Dict[str, Any]]) -> None:
    """
    Normalize root-level structures and keep extensions under dmp.extension.
    Also ensure/shape the dmp.project array.
    """
    dmp = data.setdefault("dmp", {})
    dmp["schema"] = RDA_DMP_SCHEMA_URL  # enforce

    # Migrate legacy top-level custom fields into extension
    if isinstance(dmp.get("x_ui"), dict):
        _set_extension_payload(dmp, "x_ui", dmp.pop("x_ui"))
    if isinstance(dmp.get("x_project"), dict):
        _set_extension_payload(dmp, "x_project", dmp.pop("x_project"))

    # Ensure x_ui exists with hide_fields at least as empty list
    xui = _get_extension_payload(dmp, "x_ui") or {}
    xui.setdefault("hide_fields", [])
    _set_extension_payload(dmp, "x_ui", xui)

    # Project array (shape or create a stub)
    projects: List[Dict[str, Any]] = dmp.setdefault("project", [])
    if not projects:
        projects.append({
            "title": dmp.get("title") or "Project",
            "description": None,
            "start": None,
            "end": None,
            "funding": [],
        })

    proj_schema = None
    if schema:
        proj_schema = _resolve_first(schema, [
            "#/definitions/Project", "#/definitions/project"
        ]) or None

    if proj_schema:
        for prj in projects:
            _ensure_object_fields_from_schema(prj, schema, proj_schema)
    else:
        for prj in projects:
            prj.setdefault("title", dmp.get("title") or "Project")
            prj.setdefault("description", None)
            prj.setdefault("start", None)
            prj.setdefault("end", None)
            prj.setdefault("funding", [])

def normalize_datasets_in_place(data: Dict[str, Any],
                                schema: Optional[Dict[str, Any]]) -> None:
    """
    Ensure presence of expected RDA-DMP fields on each dataset & distribution.
    Also ensures dataset-level custom fields are under dataset.extension.x_dcas.
    """
    dmp = data.setdefault("dmp", {})
    datasets: List[Dict[str, Any]] = dmp.setdefault("dataset", [])

    ds_schema = dist_schema = None
    if schema:
        ds_schema = _resolve_first(schema, [
            "#/definitions/Dataset", "#/definitions/dataset"
        ]) or None
        dist_schema = _resolve_first(schema, [
            "#/definitions/Distribution", "#/definitions/distribution"
        ]) or None

    for ds in datasets:
        if isinstance(ds.get("x_dcas"), dict):
            _set_extension_payload(ds, "x_dcas", ds.pop("x_dcas"))

        if ds_schema:
            _ensure_object_fields_from_schema(ds, schema, ds_schema)
        else:
            ds.setdefault("title", "Dataset")
            ds.setdefault("language", None)
            ds.setdefault("keyword", [])
            ds.setdefault("type", None)
            ds.setdefault("is_reused", None)
            ds.setdefault("personal_data", "unknown")
            ds.setdefault("sensitive_data", "unknown")
            ds.setdefault("preservation_statement", None)
            ds.setdefault("data_quality_assurance", [])
            ds.setdefault("metadata", [])
            ds.setdefault("security_and_privacy", [])
            ds.setdefault("technical_resource", [])

        if not isinstance(ds.get("dataset_id"), dict) or not ds["dataset_id"].get("identifier"):
            dist0 = (ds.get("distribution") or [{}])[0]
            urlish = dist0.get("access_url") or dist0.get("download_url")
            ds["dataset_id"] = make_dataset_id(ds.get("title") or "untitled", urlish)

        ds.setdefault("distribution", [])
        if not ds["distribution"]:
            ds["distribution"].append({"title": ds.get("title") or "Dataset"})

        for dist in ds["distribution"]:
            if dist_schema:
                _ensure_object_fields_from_schema(dist, schema, dist_schema)
            else:
                dist.setdefault("title", ds.get("title") or "Dataset")
                dist.setdefault("access_url", None)
                dist.setdefault("download_url", None)
                dist.setdefault("format", [])
                dist.setdefault("byte_size", None)
                dist.setdefault("data_access", "open")
                dist.setdefault("host", {"title": "Project repository"})
                dist.setdefault("available_until", None)
                dist.setdefault("description", None)
                dist.setdefault("license", [])

        x = _get_extension_payload(ds, "x_dcas") or {}
        if not x.get("data_type"):
            hint = (ds.get("distribution") or [{}])[0].get("access_url") or ""
            x["data_type"] = data_type_from_path(hint)
        for k in ["destination", "number_of_files", "total_size_mb",
                  "file_formats", "data_files", "data_size_mb", "hash"]:
            x.setdefault(k, None)
        _set_extension_payload(ds, "x_dcas", x)

def _split_multi(val: Optional[str]) -> List[str]:
    if not val or not isinstance(val, str):
        return []
    raw = [p.strip() for p in val.replace(";", ",").split(",")]
    return [p for p in raw if p]

def _apply_cookiecutter_meta(project_root: Path, data: Dict[str, Any]) -> None:
    """
    Read cookiecutter and fill DMP meta iff missing:
      - dmp.title (PROJECT_NAME/REPO_NAME)
      - dmp.description (PROJECT_DESCRIPTION)
      - dmp.contact (first author/email[/orcid])
      - dmp.project[0].title/description
      - dmp.extension[x_project] = full cookiecutter dict
    """
    # read cookiecutter via your helper
    cookie = read_toml_json(
        folder=str(project_root),
        json_filename="cookiecutter.json",
        tool_name="cookiecutter",
        toml_path="pyproject.toml",
    ) or {}

    dmp = data.setdefault("dmp", {})

    # title / description (do not overwrite if already populated)
    proj_title = cookie.get("PROJECT_NAME") or cookie.get("REPO_NAME")
    if proj_title and (not dmp.get("title") or dmp["title"] == "Replication Package DMP"):
        dmp["title"] = proj_title
    proj_desc = cookie.get("PROJECT_DESCRIPTION")
    if proj_desc and not dmp.get("description"):
        dmp["description"] = proj_desc

    # contact (object in 1.0)
    authors = _split_multi(cookie.get("AUTHORS"))
    emails  = _split_multi(cookie.get("EMAIL"))
    orcids  = _split_multi(cookie.get("ORCIDS"))

    if not dmp.get("contact"):
        name = authors[0] if authors else None
        mbox = emails[0] if emails else None
        if name or mbox:
            contact: Dict[str, Any] = {}
            if name: contact["name"] = name
            if mbox: contact["mbox"] = mbox
            if orcids:
                contact["contact_id"] = {"type": "orcid", "identifier": orcids[0]}
            dmp["contact"] = contact

    # project[0] (minimal)
    projects: List[Dict[str, Any]] = dmp.setdefault("project", [])
    if not projects:
        projects.append({})
    prj0 = projects[0]
    if proj_title and not prj0.get("title"):
        prj0["title"] = proj_title
    if proj_desc and not prj0.get("description"):
        prj0["description"] = proj_desc
    prj0.setdefault("start", prj0.get("start") or None)
    prj0.setdefault("end", prj0.get("end") or None)
    prj0.setdefault("funding", prj0.get("funding") or [])

    # stash the full cookiecutter under extension[x_project]
    if cookie:
        _set_extension_payload(dmp, "x_project", cookie)

def reorder_dmp_keys(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return a new dict where data['dmp'] keys follow DMP_KEY_ORDER; extras appended afterwards."""
    dmp = data.get("dmp", {})
    ordered: Dict[str, Any] = {}
    for k in DMP_KEY_ORDER:
        if k in dmp:
            ordered[k] = dmp[k]
    for k, v in dmp.items():
        if k not in ordered:
            ordered[k] = v
    return {"dmp": ordered}

def create_or_update_dmp_from_schema(dmp_path: Path = DEFAULT_DMP_PATH,
                                     schema_url: str = SCHEMA_URL,
                                     schema_cache: Path = DEFAULT_SCHEMA_CACHE,
                                     force_schema_refresh: bool = False) -> Path:
    """
    - If DMP doesn't exist: create a fresh DMP scaffold.
    - If it exists: load it, normalize root & project & datasets (preserving values).
    - Always set dmp["schema"] to the GitHub 'tree' URL for 1.0.
    - Wrap root custom fields (x_ui, x_project) and dataset custom fields (x_dcas)
      under their respective 'extension' arrays.
    - Pull metadata from cookiecutter (title, description, contact, project).
    - Ensure the top-level 'dmp' object is saved in the exact key order you specified.
    """
    schema = fetch_schema(schema_url, schema_cache, force=force_schema_refresh)

    if not dmp_path.exists():
        shaped = ensure_dmp_shape({}, schema=schema)
        # Apply cookiecutter immediately so a new file gets meta, too
        _apply_cookiecutter_meta(project_root=Path.cwd(), data=shaped)
        shaped = reorder_dmp_keys(shaped)
        save_json(dmp_path, shaped)
        return dmp_path

    data = load_json(dmp_path)
    data = ensure_dmp_shape(data, schema=schema)
    normalize_root_in_place(data, schema=schema)
    normalize_datasets_in_place(data, schema=schema)

    # ⬇️ fill from cookiecutter (does not overwrite existing populated values)
    _apply_cookiecutter_meta(project_root=Path.cwd(), data=data)

    data["dmp"]["schema"] = RDA_DMP_SCHEMA_URL  # enforce requested value
    data["dmp"]["modified"] = now_iso_minute()

    # Reorder top-level keys to match your example
    data = reorder_dmp_keys(data)

    save_json(dmp_path, data)
    return dmp_path

def main() -> None:
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)
    create_or_update_dmp_from_schema(
        dmp_path=DEFAULT_DMP_PATH,
        schema_url=SCHEMA_URL,
        schema_cache=DEFAULT_SCHEMA_CACHE,
        force_schema_refresh=False,
    )
    print(f"DMP ensured at {DEFAULT_DMP_PATH.resolve()} using maDMP 1.0 schema (ordered).")

if __name__ == "__main__":
    main()
