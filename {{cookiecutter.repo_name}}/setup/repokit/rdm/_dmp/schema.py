from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any

from .config import SCHEMA_DOWNLOAD_URLS, SCHEMA_CACHE_FILES, SCHEMA_URLS

def schema_version_from_url(url: str, default: str = "1.2") -> str:
    if not isinstance(url, str):
        return default
    for ver, known_url in SCHEMA_URLS.items():
        if url.strip() == known_url:
            return ver
    return default

def fetch_schema(schema_url: str, cache_path: Path, force: bool = False) -> dict[str, Any]:
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

def validate_against_schema(data: dict[str, Any], schema: dict[str, Any] | None = None) -> list[str]:
    try:
        from jsonschema import Draft7Validator
    except Exception:
        return []
    if schema is None:
        raise ValueError("schema must be provided (or call fetch_schema yourself).")
    v = Draft7Validator(schema)
    errs = sorted(v.iter_errors(data), key=lambda e: list(e.path))
    return [f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errs]

def _resolve_ref(schema: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        return {}
    node: Any = schema
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        node = node.get(part, {})
    return node if isinstance(node, dict) else {}

def _deref(schema: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    if "$ref" in node:
        base = _resolve_ref(schema, node["$ref"])
        merged = dict(base)
        merged.update({k: v for k, v in node.items() if k != "$ref"})
        return merged
    return node

def _resolve_first(schema: dict[str, Any], candidates: list[str]) -> dict[str, Any]:
    for c in candidates:
        node = _resolve_ref(schema, c)
        if node:
            return node
    return {}
