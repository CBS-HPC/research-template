import json
import os
import urllib.request
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..general_tools import split_multi,PROJECT_ROOT
from .tomlutils import read_toml_json


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ──────────────────────────────────────────────────────────────────────────────
# Config (RDA-DMP 1.)
# ──────────────────────────────────────────────────────────────────────────────


SCHEMA_DOWNLOAD_URLS: Dict[str, str] = {
    "1.0": (
        "https://raw.githubusercontent.com/RDA-DMP-Common/"
        "RDA-DMP-Common-Standard/master/examples/JSON/JSON-schema/"
        "1.0/maDMP-schema-1.0.json"
    ),
    "1.1": (
        "https://raw.githubusercontent.com/RDA-DMP-Common/"
        "RDA-DMP-Common-Standard/master/examples/JSON/JSON-schema/"
        "1.1/maDMP-schema-1.1.json"
    ),
    "1.2": (
        "https://raw.githubusercontent.com/RDA-DMP-Common/"
        "RDA-DMP-Common-Standard/master/examples/JSON/JSON-schema/"
        "1.2/maDMP-schema-1.2.json"
    ),
}

SCHEMA_CACHE_FILES: Dict[str, Path] = {
    "1.0": Path("./bin/maDMP-schema-1.0.json"),
    "1.1": Path("./bin/maDMP-schema-1.1.json"),
    "1.2": Path("./bin/maDMP-schema-1.2.json"),
}

# Always store this exact value in dmp["schema"]
SCHEMA_URLS: Dict[str, str] = {
    "1.0": (
        "https://github.com/RDA-DMP-Common/RDA-DMP-Common-Standard/"
        "tree/master/examples/JSON/JSON-schema/1.0"
    ),
    "1.1": (
        "https://github.com/RDA-DMP-Common/RDA-DMP-Common-Standard/"
        "tree/master/examples/JSON/JSON-schema/1.1"
    ),
    "1.2": (
        "https://github.com/RDA-DMP-Common/RDA-DMP-Common-Standard/"
        "tree/master/examples/JSON/JSON-schema/1.2"
    ),
}


DEFAULT_DMP_PATH = Path("./dmp.json")

def schema_version_from_url(url: str, default: str = "1.2") -> str:
    """
    Return the schema version (e.g. "1.0", "1.1", "1.2") if the URL
    exactly matches one of the known SCHEMA_URLS values.
    Otherwise, return the default ("1.2").
    """
    if not isinstance(url, str):
        return default
    for ver, known_url in SCHEMA_URLS.items():
        if url.strip() == known_url:
            return ver
    return default

dmp = load_json(DEFAULT_DMP_PATH)

schema_url = dmp.get("dmp", {}).get("schema")
if schema_url:
    SCHEMA_VERSION = schema_version_from_url(schema_url)
else:
    SCHEMA_VERSION = "1.2"
    
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
    "contributor",
    "project",
    "dataset",
    "extension",
]

# Order of fields inside each dataset object
DATASET_KEY_ORDER: List[str] = [
    "title",
    "description",
    "issued",
    "modified",
    "language",
    "keyword",
    "is_reused",
    "personal_data",
    "sensitive_data",
    "type",
    "preservation_statement",
    "dataset_id",
    "distribution",
    "data_quality_assurance",
    "metadata",
    "security_and_privacy",
    "technical_resource",
    "extension",
]

# Order of fields inside each distribution object
DISTRIBUTION_KEY_ORDER: List[str] = [
    #"title",
    #"description",
    "access_url",
    #"download_url",
    "format",
    "byte_size",
    "data_access",
    "host",
    "available_until",
    "license",
]

# Small nested objects
DATASET_ID_KEY_ORDER = ["identifier", "type"]
METADATA_ITEM_KEY_ORDER = ["language", "metadata_standard_id", "description"]
SEC_PRIV_ITEM_KEY_ORDER = ["title", "description"]
TECH_RES_ITEM_KEY_ORDER = ["name", "description"]
HOST_KEY_ORDER = ["title", "url"]
LICENSE_ITEM_KEY_ORDER = ["license_ref", "start_date"]



# Central license mapping: short code → canonical URL
LICENSE_LINKS: Dict[str, str] = {
    "CC-BY-4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC0-1.0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "None": "",
}

# Extra enums we want the editor to offer in addition to (or instead of) schema-provided enums
EXTRA_ENUMS: Dict[str, List[str]] = {
    # For dataset.distribution[].license[].license_ref we want the *URL* values as the choices
    "dmp.dataset[].distribution[].license[].license_ref": list(LICENSE_LINKS.values()),
}

# Minimal offline fallbacks for the common triads
LOCAL_FALLBACK_ENUMS: Dict[str, List[str]] = {
    "dmp.dataset[].personal_data": ["yes", "no", "unknown"],
    "dmp.dataset[].sensitive_data": ["yes", "no", "unknown"],
    # You can add more safe fallbacks here if useful
}


    # Minimal, readable mapping. Add/adjust as needed.

DK_UNI_MAP = {
    # Copenhagen Business School
    "cbs.dk": {
        "name": "Copenhagen Business School",
        "abbreviation": "CBS",
        "ror": "https://ror.org/04sppb023",
        "dataverse_alias": "cbs",
        "dataverse_default_base_url": "https://demo.dataverse.deic.dk",
    },
    # University of Copenhagen
    "ku.dk": {
        "name": "University of Copenhagen",
        "abbreviation": "KU",
        "ror": "https://ror.org/035b05819",
        "dataverse_alias": "ku",
        "dataverse_default_base_url": "https://dataverse.deic.dk",  # production for KU
    },
    # University of Southern Denmark
    "sdu.dk": {
        "name": "University of Southern Denmark",
        "abbreviation": "SDU",
        "ror": "https://ror.org/03yrrjy16",
        "dataverse_alias": "sdu",
        "dataverse_default_base_url": "https://demo.dataverse.deic.dk",
    },
    # Aarhus University
    "au.dk": {
        "name": "Aarhus University",
        "abbreviation": "AU",
        "ror": "https://ror.org/01aj84f44",
        "dataverse_alias": "au",
        "dataverse_default_base_url": "https://demo.dataverse.deic.dk",
    },
    # Technical University of Denmark
    "dtu.dk": {
        "name": "Technical University of Denmark",
        "abbreviation": "DTU",
        "ror": "https://ror.org/04qtj9h94",
        "dataverse_alias": "dtu",
        "dataverse_default_base_url": "https://demo.dataverse.deic.dk",
    },
    # Aalborg University
    "aau.dk": {
        "name": "Aalborg University",
        "abbreviation": "AAU",
        "ror": "https://ror.org/04m5j1k67",
        "dataverse_alias": "aau",
        "dataverse_default_base_url": "https://demo.dataverse.deic.dk",
    },
    # Roskilde University
    "ruc.dk": {
        "name": "Roskilde University",
        "abbreviation": "RUC",
        "ror": "https://ror.org/014axpa37",
        "dataverse_alias": "ruc",
        "dataverse_default_base_url": "https://demo.dataverse.deic.dk",
    },
    # IT University of Copenhagen
    "itu.dk": {
        "name": "IT University of Copenhagen",
        "abbreviation": "ITU",
        "ror": "https://ror.org/02309jg23",
        "dataverse_alias": "itu",
        "dataverse_default_base_url": "https://demo.dataverse.deic.dk",
    },
}


def dmp_default_templates(now_dt: Optional[str] = None, today: Optional[str] = None) -> dict:
    """
    Single source of truth for default values.
    Returns dict with keys: root, project, dataset, distribution, x_dcas.
    All optional strings default to "", booleans are true bools,
    and date/time fields match the schema's formats.
    """
    now_dt = now_dt or now_iso_minute()  # date-time with Z
    today = today or today_iso()
    
    cookie = read_toml_json(
    folder=str(PROJECT_ROOT),
    json_filename="cookiecutter.json",
    tool_name="cookiecutter",
    toml_path="pyproject.toml",
    ) or {}
    
    return {
        "root": {
            "schema": SCHEMA_URLS[SCHEMA_VERSION],
            "title": "",
            "description": "",
            "language": "eng",
            "created": now_dt,               # required date-time
            "modified": now_dt,              # required date-time
            "ethical_issues_exist": "unknown",
            "ethical_issues_description": "",
            "ethical_issues_report": "https://example.org/ethics-report",
            "dmp_id": {                      # required (identifier, type)
                "identifier": "https://example.org/dmp",
                "type": "url",
            },
            "contact": {                     # required (contact_id, mbox, name)
                "name": "",
                "mbox": "",
                "contact_id": {
                    "identifier": "https://orcid.org/0000-0000-0000-0000",
                    "type": "orcid",
                },
                "affiliation": {
                "name": "",
                "abbreviation": "",
                "region": None,
                "affiliation_id": {
                    "type": "ror",
                    "identifier": ""
                }
            }
            },
            #"contributor": [{                    # required (contact_id, mbox, name)
            #    "name": "",
            #    "mbox": "",
            #    "contributor_id": {
            #        "identifier": "https://orcid.org/0000-0000-0000-0000",
            #        "type": "orcid",
            #    },
                #"affiliation": {
                #"name": "Copenhagen Business School",
                #"abbreviation": "CBS",
                #"region": None,
                #"affiliation_id": {
                #    "type": "ror",
                #    "identifier": "https://ror.org/04sppb023"
                #}
            #}],
            "project": [],                   # array
            "dataset": [],                   # required array
            "extension": [],
        },
        "project": {                         # items must have title
            "title": "",
            "description": "",
            "start": today,                     # format: date if set
            "end": "",                       # format: date if set
            "funding": [],
            #"funding": [{"funder_id": "", "funder_status": "","grant_id": {"identifier": "", "type": ""}}],
        },
        "dataset": {
            "title": "",              # required
            "description": "",
            "issued": "",                 # format: date
            "modified": "",                  # optional string if you use it
            "language": "eng",
            "keyword": [],
            "type": "",
            "is_reused": False,              # boolean
            "dataset_id": {
                "identifier": "",
                "type": "doi",
            },
            "personal_data": "unknown",      # enum
            "sensitive_data": "unknown",     # enum

            "distribution": [],
            "preservation_statement": "",
            "data_quality_assurance": [],
            "metadata": [{
                "language": "eng",
                "metadata_standard_id": {"identifier": "", "type": "url"},
                "description": "",
            }],
            "security_and_privacy": [{"title": "", "description": ""}],
            "technical_resource": [{"name": "", "description": ""}],
            "extension": [],
        },
        "distribution": {
            #"title": "",              # required
            #"description": "",               # string
            "access_url": "",                # string (url if you have one)
            #"download_url": "",              # string (url if you have one)
            "format": [],
            "byte_size": 0,                  # integer
            "data_access": "open",           # enum
            #"host": {                        # required object: title+url
            #    "title": "Project repository",
            #    "url": "https://example.org",
            #},
            "available_until": "",           # format: date if set

            "license": [{
                "license_ref": LICENSE_LINKS.get(cookie.get("DATA_LICENSE"), ""),
                "start_date": today,
            }],
        },
        "x_dcas": {  # extension payload (not part of RDA schema; free-form)
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

def _affiliation_from_email(email: str) -> Optional[dict]:
    """
    Guess affiliation from a Danish university email.
    Returns an 'affiliation' dict like your DMP schema expects, or None if unknown.

    Example return:
    {
        "name": "Copenhagen Business School",
        "abbreviation": "CBS",
        "region": None,
        "affiliation_id": {"type": "ror", "identifier": "https://ror.org/04sppb023"}
    }
    """
    if not isinstance(email, str) or "@" not in email:
        return None

    domain = email.split("@", 1)[1].strip().lower()

    def _matches_suffix(dom: str, suffix: str) -> bool:
        # handles "dept.ku.dk", "student.cbs.dk", etc.
        return dom == suffix or dom.endswith("." + suffix)

    for suffix, org in DK_UNI_MAP.items():
        if _matches_suffix(domain, suffix):
            return {
                "name": org["name"],
                "abbreviation": org["abbreviation"],
                "region": None,
                "affiliation_id": {
                    "type": "ror",
                    "identifier": org["ror"],
                } if org.get("ror") else None,
            }

    return  {
            "name": "",
            "abbreviation": "",
            "region": None,
            "affiliation_id": {
                "type": "ror",
                "identifier": ""
            }}

def _set_contacts(dmp:dict,cookie:dict,overwrite:bool=False):
    authors = split_multi(cookie.get("AUTHORS"))
    emails = split_multi(cookie.get("EMAIL"))
    orcids = split_multi(cookie.get("ORCIDS"))

    name = authors[0] if authors else None
    mbox = emails[0] if emails else None
    orcid = orcids[0] if orcids else None

    if overwrite or ((name or mbox or orcid)  and not dmp.get("contact")):
        info: Dict[str, Any] = {}
        if name:
            info["name"] = name
        if mbox:
            info["mbox"] = mbox
        if orcid:
            info["contact_id"] = {"type": "orcid", "identifier": orcid}
        if mbox:
            info["affiliation"] = _affiliation_from_email(mbox)
        
        dmp["contact"] = info

    # contributors (idx 1..end)
    contributors = []
    max_len = max(len(authors), len(emails), len(orcids)) if (authors or emails or orcids) else 0

    for i in range(1, max_len):
        name = authors[i] if i < len(authors) else None
        mbox = emails[i] if i < len(emails) else None
        orcid = orcids[i] if i < len(orcids) else None

        if not (name or mbox or orcid):
            continue

        info: Dict[str, Any] = {}
        if name:
            info["name"] = name
        if mbox:
            info["mbox"] = mbox
            info["affiliation"] = _affiliation_from_email(mbox)
        if orcid:
            info["contributor_id"] = {"type": "orcid", "identifier": orcid}

        contributors.append(info)

    if overwrite or (contributors and not dmp.get("contributor")):
        if not contributors:
            dmp.pop("contributor", None)
        else:
            dmp["contributor"] = contributors      # list of dicts

    return dmp

def _apply_cookiecutter_meta(project_root: Path, data: Dict[str, Any],overwrite:bool=False) -> None:
    """
    Read cookiecutter and fill DMP meta iff missing:
      - dmp.title (PROJECT_NAME/REPO_NAME)
      - dmp.description (PROJECT_DESCRIPTION)
      - dmp.contact (first author/email[/orcid])
      - dmp.project[0].title/description
    """
    cookie = read_toml_json(
        folder=str(project_root),
        json_filename="cookiecutter.json",
        tool_name="cookiecutter",
        toml_path="pyproject.toml",
    ) or {}

    dmp = data.setdefault("dmp", {})
    templates = dmp_default_templates()

    # ensure base defaults are present before applying cookiecutter hints
    apply_defaults_in_place(dmp, templates["root"])

    # title / description (do not overwrite if already populated)
    proj_title = cookie.get("PROJECT_NAME") or cookie.get("REPO_NAME")
    if proj_title:
        if overwrite:
            dmp["title"] = proj_title
        else:
            dmp["title"] = dmp.get("title") or proj_title

    proj_desc = cookie.get("PROJECT_DESCRIPTION")
    if proj_desc:
        if overwrite:
            dmp["description"] = proj_desc
        else:    
            dmp["description"] = dmp.get("description") or proj_desc

    # contact & contributor
    dmp = _set_contacts(dmp,cookie,overwrite)

    # project[0] (minimal)
    projects: List[Dict[str, Any]] = dmp.setdefault("project", [])
    if not projects:
        projects.append(deepcopy(templates["project"]))
    prj0 = projects[0]

    if proj_title and not prj0.get("title"):
        prj0["title"] = proj_title
    if proj_desc and not prj0.get("description"):
        prj0["description"] = proj_desc
    apply_defaults_in_place(prj0, templates["project"])

def now_iso_minute() -> str:
    """RFC 3339 / JSON Schema 'date-time' with UTC 'Z' and seconds precision."""
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def fetch_schema(schema_url: str = SCHEMA_DOWNLOAD_URLS[SCHEMA_VERSION],
                 cache_path: Path = SCHEMA_CACHE_FILES[SCHEMA_VERSION],
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


# --- shared, soft-dependency validator ---------------------------------------
def validate_against_schema(data: Dict[str, Any],
                            schema: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Return a list of error messages. If jsonschema is unavailable, returns [].
    """
    try:
        from jsonschema import Draft7Validator
    except Exception:
        return []
    schema = schema or fetch_schema()
    v = Draft7Validator(schema)
    errs = sorted(v.iter_errors(data), key=lambda e: list(e.path))

    errs = [f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errs]
    if errs:
        print("⚠️ Schema validation issues (new file, after schema-driven auto-fix):")
        for e in errs[:50]:
            print(" -", e)

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

def _ensure_extension(obj: Dict[str, Any]) -> List[Dict[str, Any]]:
    obj.setdefault("extension", [])
    return obj["extension"]

def _find_extension_index(obj: Dict[str, Any], key: str) -> int:
    ext = obj.get("extension") or []
    for i, item in enumerate(ext):
        if isinstance(item, dict) and key in item:
            return i
    return -1

def get_extension_payload(obj: Dict[str, Any], key: str) -> Optional[Dict[str, Any]]:
    i = _find_extension_index(obj, key)
    if i == -1:
        return None
    payload = obj["extension"][i].get(key)
    return payload if isinstance(payload, dict) else None

def set_extension_payload(obj: Dict[str, Any], key: str, payload: Dict[str, Any]) -> None:
    ext = _ensure_extension(obj)
    i = _find_extension_index(obj, key)
    if i == -1:
        ext.append({key: dict(payload)})
    else:
        if not isinstance(ext[i][key], dict):
            ext[i][key] = dict(payload)
        else:
            ext[i][key].update({k: v for k, v in payload.items()})

# ──────────────────────────────────────────────────────────────────────────────
# CENTRALIZED DEFAULTS
# ──────────────────────────────────────────────────────────────────────────────

def today_iso() -> str:
    """JSON Schema 'date' string."""
    return datetime.utcnow().strftime("%Y-%m-%d")

def _deep_apply_defaults(target: Any, template: Any) -> Any:
    """
    Deep, non-destructive default overlay.

    Rules (conservative, editor-safe):
    - dict vs dict: add ONLY missing keys (recursively for dicts); do not overwrite existing values.
    - list: if target is a list, ALWAYS keep it as-is (even if empty). Never inject template list items.
    - type mismatch: if target exists and is not the same container type as template, keep target as-is.
    - primitives: if target is None, use template; otherwise keep target.
    """
    # dicts
    if isinstance(template, dict):
        if not isinstance(target, dict):
            # target already has a non-dict value; preserve it
            return target
        # add only missing keys from template
        out = dict(target)
        for k, v in template.items():
            if k in out:
                # recurse only if both sides are dicts; otherwise preserve user's value
                if isinstance(out[k], dict) and isinstance(v, dict):
                    out[k] = _deep_apply_defaults(out[k], v)
                else:
                    # keep user's existing non-dict (or list) value
                    pass
            else:
                out[k] = deepcopy(v)
        return out

    # lists
    if isinstance(template, list):
        # If the user already has a list (even empty), keep it verbatim.
        if isinstance(target, list):
            return target
        # If user has some other value, keep it; otherwise fall back to template for "missing"
        return target if target is not None else deepcopy(template)

    # primitives
    return target if target is not None else deepcopy(template)

def apply_defaults_in_place(target: dict, template: dict) -> None:
    """
    In-place wrapper using conservative overlay: only add missing keys;
    never replace existing lists or primitives.
    """
    merged = _deep_apply_defaults(target, template)
    target.clear()
    target.update(merged)


# ──────────────────────────────────────────────────────────────────────────────
# Enum defaulting (project rules) + schema-driven default constructor
# ──────────────────────────────────────────────────────────────────────────────

def _enum_default(prop_name: Optional[str], options: List[Any]) -> Any:
    """
    Choose a default for enum fields using project rules:
    - language -> 'eng'
    - {'yes','no','unknown'} -> 'unknown'
    - contact.contact_id.type -> 'orcid'
    - dmp_id.type -> 'doi'
    - otherwise: first option
    """
    str_opts = [o for o in options if isinstance(o, str)]
    lower = {o.lower() for o in str_opts}

    # language code
    if prop_name and prop_name.lower().endswith("language") and "eng" in lower:
        return "eng"

    # yes/no/unknown triad
    if {"yes", "no", "unknown"}.issubset(lower):
        return "unknown"

    # specific typed IDs via full path hints
    if prop_name:
        p = prop_name.lower()
        if p.endswith("contact_id.type") and "orcid" in lower:
            return "orcid"
        if p.endswith("dmp_id.type") and "doi" in lower:
            return "doi"

    # generic 'type' fallbacks (if path isn't specific)
    if "orcid" in lower:
        return "orcid"
    if "doi" in lower:
        return "doi"

    # final fallback
    return options[0] if options else None


def _default_for_schema(schema: Dict[str, Any], node: Dict[str, Any], prop_name: Optional[str] = None) -> Any:
    """
    Best-effort default constructor from a JSON Schema node (schema-driven).
    - objects  -> {}
    - arrays   -> []
    - string   -> ""
    - integer  -> 0
    - number   -> 0.0
    - boolean  -> False
    - enums    -> pick via _enum_default(...) using project rules
    - respects 'default' if present, resolves $ref one level
    """
    node = _deref(schema, node)

    # explicit schema default wins
    if "default" in node:
        return deepcopy(node["default"])

    # enum handling (multiple choice)
    if "enum" in node and isinstance(node["enum"], list):
        choice = _enum_default(prop_name, node["enum"])
        if choice is not None:
            return deepcopy(choice)

    # Resolve type (could be list like ["null","string"])
    typ = node.get("type")
    if isinstance(typ, list):
        for t in ("object", "array", "string", "integer", "number", "boolean"):
            if t in typ:
                typ = t
                break
        if isinstance(typ, list):
            typ = typ[0]  # fallback

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

    # If only $ref given, resolve again
    if "$ref" in node:
        return _default_for_schema(schema, node, prop_name=prop_name)

    return None


def repair_empty_enums(obj: Any, schema: Dict[str, Any], node: Dict[str, Any], path: Optional[str] = None) -> None:
    """
    Traverse existing object and if a property is an enum but current value is "",
    replace it with the enum default according to project rules.
    """
    node = _deref(schema, node)
    if isinstance(obj, dict):
        props = node.get("properties", {})
        for k, v in obj.items():
            pnode = _deref(schema, props.get(k, {}))
            key_path = f"{path}.{k}" if path else k
            # repair empty string on enums
            if isinstance(v, str) and v == "" and "enum" in pnode:
                obj[k] = _enum_default(key_path, pnode["enum"]) or v
            # recurse
            repair_empty_enums(v, schema, pnode, path=key_path)
    elif isinstance(obj, list):
        items = _deref(schema, node.get("items", {}))
        for i, it in enumerate(obj):
            repair_empty_enums(it, schema, items, path=f"{path}[{i}]" if path else f"[{i}]")


# ──────────────────────────────────────────────────────────────────────────────
# Schema-driven required-field filling
# ──────────────────────────────────────────────────────────────────────────────

def _ensure_required_object_from_schema(
    obj: Dict[str, Any],
    schema: Dict[str, Any],
    obj_schema: Dict[str, Any],
    path: Optional[str] = None,
) -> None:
    """
    Ensure that every key listed in obj_schema['required'] exists on obj,
    initializing with schema-driven defaults (with enum rules). Recurse into
    nested structures. Also traverse existing non-required object/array fields
    to satisfy their nested requireds.
    """
    s = _deref(schema, obj_schema)
    props: Dict[str, Any] = s.get("properties", {})
    required = s.get("required", [])

    # Fill required keys (and recurse)
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

            # If minItems > 0 and list empty, seed one default item
            if min_items and not obj[key]:
                default_item = _default_for_schema(schema, items_schema, prop_name=f"{key_path}[]")
                obj[key].append(default_item if default_item is not None else {})

            # For any existing items that are objects, ensure their requireds
            for i, it in enumerate(obj[key]):
                if isinstance(it, dict):
                    _ensure_required_object_from_schema(it, schema, items_schema, path=f"{key_path}[{i}]")

    # Traverse existing non-required object/array properties to satisfy nested requireds
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

def ensure_required_by_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Ensure required fields exist for the root 'dmp' object (and nested objects)
    by reading ONLY from the JSON Schema. No field names are hardcoded.
    """
    # Locate the top-level 'dmp' property schema
    root_props = schema.get("properties", {})
    dmp_schema_node = root_props.get("dmp")
    if not isinstance(dmp_schema_node, dict):
        return  # nothing to do if schema shape is unexpected

    dmp_obj = data.setdefault("dmp", {})
    _ensure_required_object_from_schema(dmp_obj, schema, dmp_schema_node, path="dmp")


# ──────────────────────────────────────────────────────────────────────────────
# Shaping & normalization (using centralized defaults + migrations)
# ──────────────────────────────────────────────────────────────────────────────

def ensure_dmp_shape(data: Dict[str, Any],
                     **_: Any) -> Dict[str, Any]:
    """
    Ensure a well-formed RDA-DMP container.
    Uses centralized defaults and preserves existing values where present.
    Also migrates legacy:
      - dataset["x_dcas"]  -> dataset["extension"] [{"x_dcas": {...}}]
    """
    templates = dmp_default_templates()

    # Already DMP-shaped?
    if isinstance(data.get("dmp"), dict):
        dmp = data["dmp"]
        apply_defaults_in_place(dmp, templates["root"])
        dmp["schema"] = SCHEMA_URLS[SCHEMA_VERSION]  # enforce exact link

        # project must be an array
        if not isinstance(dmp.get("project"), list):
            dmp["project"] = []

        # migrate legacy dataset.x_dcas
        for ds in dmp.get("dataset", []):
            if isinstance(ds.get("x_dcas"), dict):
                set_extension_payload(ds, "x_dcas", ds.pop("x_dcas"))

        return {"dmp": dmp}

    # Fresh container
    root = deepcopy(templates["root"])
    return {"dmp": root}

def normalize_root_in_place(data: Dict[str, Any],
                            schema: Optional[Dict[str, Any]]) -> None:
    """
    Normalize root-level structures and keep extensions under dmp.extension.
    Also ensure/shape the dmp.project array.
    """
    templates = dmp_default_templates()
    dmp = data.setdefault("dmp", {})
    apply_defaults_in_place(dmp, templates["root"])
    dmp["schema"] = SCHEMA_URLS[SCHEMA_VERSION]  # enforce

    # Project array (shape or create a stub)
    projects: List[Dict[str, Any]] = dmp.setdefault("project", [])
    if not isinstance(projects, list):
        projects = []
        dmp["project"] = projects
    if not projects:
        # seed a single project using defaults; title mirrors dmp.title if present
        prj = deepcopy(templates["project"])
        prj["title"] = dmp.get("title") or "Project"
        projects.append(prj)

    # Optionally complement from schema if available
    if schema:
        proj_schema = _resolve_first(schema, ["#/definitions/Project", "#/definitions/project"]) or None
        if proj_schema:
            for prj in projects:
                _ensure_object_fields_from_schema(prj, schema, proj_schema, path="dmp.project[]")
                apply_defaults_in_place(prj, templates["project"])
        else:
            for prj in projects:
                apply_defaults_in_place(prj, templates["project"])
    else:
        for prj in projects:
            apply_defaults_in_place(prj, templates["project"])

def normalize_datasets_in_place(data: Dict[str, Any],
                                schema: Optional[Dict[str, Any]]) -> None:
    """
    Ensure presence of expected RDA-DMP fields on each dataset & distribution.
    Also ensures dataset-level custom fields are under dataset.extension.x_dcas.
    """
    templates = dmp_default_templates()
    dmp = data.setdefault("dmp", {})
    datasets: List[Dict[str, Any]] = dmp.setdefault("dataset", [])
    if not isinstance(datasets, list):
        dmp["dataset"] = datasets = []

    ds_schema = dist_schema = None
    if schema:
        ds_schema = _resolve_first(schema, ["#/definitions/Dataset", "#/definitions/dataset"]) or None
        dist_schema = _resolve_first(schema, ["#/definitions/Distribution", "#/definitions/distribution"]) or None

    for ds in datasets:
        # legacy migration
        if isinstance(ds.get("x_dcas"), dict):
            set_extension_payload(ds, "x_dcas", ds.pop("x_dcas"))

        # dataset defaults (central)
        apply_defaults_in_place(ds, templates["dataset"])

        # schema-top up (optional)
        if ds_schema:
            _ensure_object_fields_from_schema(ds, schema, ds_schema, path="dmp.dataset[]")

        # distribution array + defaults for each distribution
        ds.setdefault("distribution", [])
        if not ds["distribution"]:
            # create one distribution seeded with dataset title
            dist = deepcopy(templates["distribution"])
            #dist["title"] = ds.get("title") or dist["title"]
            ds["distribution"].append(dist)

        for dist in ds["distribution"]:
            apply_defaults_in_place(dist, templates["distribution"])
            # schema-top up (optional)
            if dist_schema:
                _ensure_object_fields_from_schema(
                    dist, schema, dist_schema, path="dmp.dataset[].distribution[]"
                )

        # x_dcas payload
        x = get_extension_payload(ds, "x_dcas") or {}
        apply_defaults_in_place(x, templates["x_dcas"])
        if not x.get("data_type"):
            hint = (ds.get("distribution") or [{}])[0].get("access_url") or ""
            x["data_type"] = data_type_from_path(hint)
        set_extension_payload(ds, "x_dcas", x)

def _ensure_object_fields_from_schema(target: Dict[str, Any],
                                      schema: Dict[str, Any],
                                      obj_schema: Dict[str, Any],
                                      prefill: Optional[Dict[str, Any]] = None,
                                      path: Optional[str] = None) -> None:
    """
    Ensure keys exist on target based on 'properties' of obj_schema.
    Values are best-effort defaults; existing values are preserved.
    """
    obj_schema = _deref(schema, obj_schema)
    props = obj_schema.get("properties", {})
    for key, prop_schema in props.items():
        if key not in target:
            key_path = f"{path}.{key}" if path else key
            target[key] = _default_for_schema(schema, prop_schema, prop_name=key_path)
    for key in obj_schema.get("required", []):
        if key not in target:
            key_path = f"{path}.{key}" if path else key
            target[key] = _default_for_schema(schema, props.get(key, {}), prop_name=key_path)
    if prefill:
        for k, v in prefill.items():
            target.setdefault(k, v)

def _order_dict(d: Dict[str, Any], order: List[str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k in order:
        if k in d:
            out[k] = d[k]
    for k, v in d.items():
        if k not in out:
            out[k] = v
    return out

def reorder_dmp_keys(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return a new dict where:
       - data['dmp'] keys follow DMP_KEY_ORDER (as before)
       - each dataset follows DATASET_KEY_ORDER
       - each dataset.distribution[] follows DISTRIBUTION_KEY_ORDER
       - common nested objects are ordered (dataset_id, metadata items, etc.)
    """
    dmp = data.get("dmp", {})
    # Root ordering first
    ordered_root: Dict[str, Any] = _order_dict(dmp, DMP_KEY_ORDER)

    # Reorder datasets (and their children)
    ds_list = ordered_root.get("dataset", [])
    new_ds_list: List[Dict[str, Any]] = []
    if isinstance(ds_list, list):
        for ds in ds_list:
            if not isinstance(ds, dict):
                new_ds_list.append(ds)
                continue

            ds2 = _order_dict(ds, DATASET_KEY_ORDER)

            # dataset_id
            if isinstance(ds2.get("dataset_id"), dict):
                ds2["dataset_id"] = _order_dict(ds2["dataset_id"], DATASET_ID_KEY_ORDER)

            # metadata[]
            if isinstance(ds2.get("metadata"), list):
                ds2["metadata"] = [
                    _order_dict(m, METADATA_ITEM_KEY_ORDER) if isinstance(m, dict) else m
                    for m in ds2["metadata"]
                ]

            # security_and_privacy[]
            if isinstance(ds2.get("security_and_privacy"), list):
                ds2["security_and_privacy"] = [
                    _order_dict(x, SEC_PRIV_ITEM_KEY_ORDER) if isinstance(x, dict) else x
                    for x in ds2["security_and_privacy"]
                ]

            # technical_resource[]
            if isinstance(ds2.get("technical_resource"), list):
                ds2["technical_resource"] = [
                    _order_dict(x, TECH_RES_ITEM_KEY_ORDER) if isinstance(x, dict) else x
                    for x in ds2["technical_resource"]
                ]

            # distribution[]
            if isinstance(ds2.get("distribution"), list):
                new_dists: List[Dict[str, Any]] = []
                for dist in ds2["distribution"]:
                    if not isinstance(dist, dict):
                        new_dists.append(dist)
                        continue
                    dist2 = _order_dict(dist, DISTRIBUTION_KEY_ORDER)

                    # host
                    if isinstance(dist2.get("host"), dict):
                        dist2["host"] = _order_dict(dist2["host"], HOST_KEY_ORDER)

                    # license[]
                    if isinstance(dist2.get("license"), list):
                        dist2["license"] = [
                            _order_dict(lic, LICENSE_ITEM_KEY_ORDER) if isinstance(lic, dict) else lic
                            for lic in dist2["license"]
                        ]

                    new_dists.append(dist2)
                ds2["distribution"] = new_dists

            new_ds_list.append(ds2)

    ordered_root["dataset"] = new_ds_list

    # Return new container with ordered root
    return {"dmp": ordered_root}

def create_or_update_dmp_from_schema(dmp_path: Path = DEFAULT_DMP_PATH) -> Path:
    """
    - If DMP doesn't exist: create a fresh DMP scaffold.
    - If it exists: load it, normalize root & project & datasets (preserving values).
    - Always set dmp["schema"] to the GitHub 'tree' URL for 1.X.
    - Wrap root custom fieldsand dataset custom fields (x_dcas)
      under their respective 'extension' arrays.
    - Pull metadata from cookiecutter (title, description, contact, project).
    - Ensure the top-level 'dmp' object is saved in the exact key order you specified.
    """

    schema = fetch_schema()

    if not dmp_path.exists():

        schema = fetch_schema()
        # Fresh shape
        shaped = ensure_dmp_shape({})
        _apply_cookiecutter_meta(project_root=PROJECT_ROOT, data=shaped,overwrite=True)
        normalize_root_in_place(shaped, schema=schema)
        normalize_datasets_in_place(shaped, schema=schema)

        # Fill required fields based purely on the schema (no hardcoding)
        ensure_required_by_schema(shaped, schema)
        # Also repair any existing empty enums ("") to rule-compliant defaults
        repair_empty_enums(shaped.get("dmp", {}), schema, schema.get("properties", {}).get("dmp", {}), path="dmp")

        shaped = reorder_dmp_keys(shaped)

        # Validate after auto-repair
        #validate_against_schema(shaped, schema=schema)
        
        save_json(dmp_path, shaped)
        return dmp_path

    # Update/normalize existing
    data = load_json(dmp_path)
    data = ensure_dmp_shape(data)
    normalize_root_in_place(data, schema=schema)
    normalize_datasets_in_place(data, schema=schema)
    _apply_cookiecutter_meta(project_root=PROJECT_ROOT, data=data,overwrite=False)

    data["dmp"]["schema"] = SCHEMA_URLS[SCHEMA_VERSION]  # enforce requested value
    data["dmp"]["modified"] = now_iso_minute()  # ensure date-time with Z

    # Schema-driven required-field filling + enum repair
    ensure_required_by_schema(data, schema)
    repair_empty_enums(data.get("dmp", {}), schema, schema.get("properties", {}).get("dmp", {}), path="dmp")

    data = reorder_dmp_keys(data)

    #validate_against_schema(data, schema=schema)

    save_json(dmp_path, data)
    print(f"DMP ensured at {DEFAULT_DMP_PATH.resolve()} using maDMP {SCHEMA_VERSION} schema (ordered).")
    return dmp_path

def main() -> None:
    os.chdir(PROJECT_ROOT)
    create_or_update_dmp_from_schema(dmp_path=DEFAULT_DMP_PATH)

if __name__ == "__main__":
    main()
