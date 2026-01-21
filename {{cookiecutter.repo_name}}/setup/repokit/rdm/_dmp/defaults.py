from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any

from .compat import PROJECT_ROOT, read_toml, split_multi
from .config import (
    JSON_FILENAME,
    TOOL_NAME,
    TOML_PATH,
    SCHEMA_URLS,
    LICENSE_LINKS,
    DK_UNI_MAP,
)
from .schema import _deref, _resolve_first
from .extensions import get_extension_payload, set_extension_payload
from .paths import data_type_from_path

def now_iso_minute() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def today_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")

def _deep_apply_defaults(target: Any, template: Any) -> Any:
    if isinstance(template, dict):
        if not isinstance(target, dict):
            return target
        out = dict(target)
        for k, v in template.items():
            if k in out:
                if isinstance(out[k], dict) and isinstance(v, dict):
                    out[k] = _deep_apply_defaults(out[k], v)
                else:
                    pass
            else:
                out[k] = deepcopy(v)
        return out

    if isinstance(template, list):
        if isinstance(target, list):
            return target
        return target if target is not None else deepcopy(template)

    return target if target is not None else deepcopy(template)

def apply_defaults_in_place(target: dict, template: dict) -> None:
    merged = _deep_apply_defaults(target, template)
    target.clear()
    target.update(merged)

def dmp_default_templates(schema_url: str, now_dt: str | None = None, today: str | None = None) -> dict:
    now_dt = now_dt or now_iso_minute()
    today = today or today_iso()
    cookie = (
        read_toml(
            folder=str(PROJECT_ROOT),
            json_filename=JSON_FILENAME,
            tool_name=TOOL_NAME,
            toml_path=TOML_PATH,
        )
        or {}
    )
    return {
        "root": {
            "schema": schema_url,
            "title": "",
            "description": "",
            "language": "eng",
            "created": now_dt,
            "modified": now_dt,
            "ethical_issues_exist": "unknown",
            "ethical_issues_description": "",
            "ethical_issues_report": "https://example.org/ethics-report",
            "dmp_id": {"identifier": "https://example.org/dmp", "type": "url"},
            "contact": {
                "name": "",
                "mbox": "",
                "contact_id": {"identifier": "https://orcid.org/0000-0000-0000-0000", "type": "orcid"},
                "affiliation": {
                    "name": "",
                    "abbreviation": "",
                    "region": None,
                    "affiliation_id": {"type": "ror", "identifier": ""},
                },
            },
            "project": [],
            "dataset": [],
            "extension": [],
        },
        "project": {"title": "", "description": "", "start": today, "end": "", "funding": []},
        "dataset": {
            "title": "",
            "description": "",
            "issued": "",
            "modified": "",
            "language": "eng",
            "keyword": [],
            "type": "",
            "is_reused": False,
            "dataset_id": {"identifier": "", "type": "doi"},
            "personal_data": "unknown",
            "sensitive_data": "unknown",
            "distribution": [],
            "preservation_statement": "",
            "data_quality_assurance": [],
            "metadata": [{"language": "eng", "metadata_standard_id": {"identifier": "", "type": "url"}, "description": ""}],
            "security_and_privacy": [{"title": "", "description": ""}],
            "technical_resource": [{"name": "", "description": ""}],
            "extension": [],
        },
        "distribution": {
            "access_url": "",
            "format": [],
            "byte_size": 0,
            "data_access": "open",
            "available_until": "",
            "license": [{"license_ref": LICENSE_LINKS.get(cookie.get("DATA_LICENSE"), ""), "start_date": today}],
        },
        "x_dcas": {
            "data_type": "Uncategorised",
            "destination": "",
            "number_of_files": 0,
            "total_size_mb": 0,
            "file_formats": [],
            "data_files": [],
            "data_size_mb": [],
            "hash": "",
        },
    }

def _enum_default(prop_name: str | None, options: list[Any]) -> Any:
    str_opts = [o for o in options if isinstance(o, str)]
    lower = {o.lower() for o in str_opts}
    if prop_name and prop_name.lower().endswith("language") and "eng" in lower:
        return "eng"
    if {"yes", "no", "unknown"}.issubset(lower):
        return "unknown"
    if prop_name:
        p = prop_name.lower()
        if p.endswith("contact_id.type") and "orcid" in lower:
            return "orcid"
        if p.endswith("dmp_id.type") and "doi" in lower:
            return "doi"
    if "orcid" in lower:
        return "orcid"
    if "doi" in lower:
        return "doi"
    return options[0] if options else None

def _default_for_schema(schema: dict[str, Any], node: dict[str, Any], prop_name: str | None = None) -> Any:
    node = _deref(schema, node)
    if "default" in node:
        return deepcopy(node["default"])
    if "enum" in node and isinstance(node["enum"], list):
        choice = _enum_default(prop_name, node["enum"])
        if choice is not None:
            return deepcopy(choice)
    typ = node.get("type")
    if isinstance(typ, list):
        for t in ("object","array","string","integer","number","boolean"):
            if t in typ:
                typ = t
                break
        if isinstance(typ, list):
            typ = typ[0]
    if typ == "object":
        return {}
    if typ == "array":
        return []
    if typ == "string":
        return ""
    if typ == "integer":
        return 0
    if typ == "number":
        return 0.0
    if typ == "boolean":
        return False
    if "$ref" in node:
        return _default_for_schema(schema, node, prop_name=prop_name)
    return None

def repair_empty_enums(obj: Any, schema: dict[str, Any], node: dict[str, Any], path: str | None = None) -> None:
    node = _deref(schema, node)
    if isinstance(obj, dict):
        props = node.get("properties", {})
        for k, v in obj.items():
            pnode = _deref(schema, props.get(k, {}))
            key_path = f"{path}.{k}" if path else k
            if isinstance(v, str) and v == "" and "enum" in pnode:
                obj[k] = _enum_default(key_path, pnode["enum"]) or v
            repair_empty_enums(v, schema, pnode, path=key_path)
    elif isinstance(obj, list):
        items = _deref(schema, node.get("items", {}))
        for i, it in enumerate(obj):
            repair_empty_enums(it, schema, items, path=f"{path}[{i}]" if path else f"[{i}]")

def _ensure_required_object_from_schema(obj: dict[str, Any], schema: dict[str, Any], obj_schema: dict[str, Any], path: str | None = None) -> None:
    s = _deref(schema, obj_schema)
    props: dict[str, Any] = s.get("properties", {})
    required = s.get("required", [])
    for key in required:
        prop_schema = props.get(key, {})
        key_path = f"{path}.{key}" if path else key
        if key not in obj or obj[key] is None:
            obj[key] = _default_for_schema(schema, prop_schema, prop_name=key_path)
        if isinstance(obj[key], dict):
            _ensure_required_object_from_schema(obj[key], schema, prop_schema, path=key_path)
        elif isinstance(obj[key], list):
            prop_s = _deref(schema, prop_schema)
            items_schema = _deref(schema, prop_s.get("items", {}))
            min_items = prop_s.get("minItems", 0)
            if min_items and not obj[key]:
                default_item = _default_for_schema(schema, items_schema, prop_name=f"{key_path}[]")
                obj[key].append(default_item if default_item is not None else {})
            for i, it in enumerate(obj[key]):
                if isinstance(it, dict):
                    _ensure_required_object_from_schema(it, schema, items_schema, path=f"{key_path}[{i}]")
    for key, val in list(obj.items()):
        if key not in props:
            continue
        prop_schema = props[key]
        key_path = f"{path}.{key}" if path else key
        prop_s = _deref(schema, prop_schema)
        if isinstance(val, dict):
            _ensure_required_object_from_schema(val, schema, prop_s, path=key_path)
        elif isinstance(val, list):
            items_schema = _deref(schema, prop_s.get("items", {}))
            for i, it in enumerate(val):
                if isinstance(it, dict):
                    _ensure_required_object_from_schema(it, schema, items_schema, path=f"{key_path}[{i}]")

def ensure_required_by_schema(data: dict[str, Any], schema: dict[str, Any]) -> None:
    root_props = schema.get("properties", {})
    dmp_schema_node = root_props.get("dmp")
    if not isinstance(dmp_schema_node, dict):
        return
    dmp_obj = data.setdefault("dmp", {})
    _ensure_required_object_from_schema(dmp_obj, schema, dmp_schema_node, path="dmp")

def affiliation_from_email(email: str) -> dict | None:
    if not isinstance(email, str) or "@" not in email:
        return None
    domain = email.split("@", 1)[1].strip().lower()

    def _matches_suffix(dom: str, suffix: str) -> bool:
        return dom == suffix or dom.endswith("." + suffix)

    for suffix, org in DK_UNI_MAP.items():
        if _matches_suffix(domain, suffix):
            return {
                "name": org["name"],
                "abbreviation": org["abbreviation"],
                "region": None,
                "affiliation_id": {"type": "ror", "identifier": org["ror"]} if org.get("ror") else None,
            }

    return {"name": "", "abbreviation": "", "region": None, "affiliation_id": {"type": "ror", "identifier": ""}}
