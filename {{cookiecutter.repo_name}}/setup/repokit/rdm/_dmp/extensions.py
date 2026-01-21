from __future__ import annotations

from typing import Any

def _ensure_extension(obj: dict[str, Any]) -> list[dict[str, Any]]:
    obj.setdefault("extension", [])
    return obj["extension"]

def _find_extension_index(obj: dict[str, Any], key: str) -> int:
    ext = obj.get("extension") or []
    for i, item in enumerate(ext):
        if isinstance(item, dict) and key in item:
            return i
    return -1

def get_extension_payload(obj: dict[str, Any], key: str) -> dict[str, Any] | None:
    i = _find_extension_index(obj, key)
    if i == -1:
        return None
    payload = obj["extension"][i].get(key)
    return payload if isinstance(payload, dict) else None

def set_extension_payload(obj: dict[str, Any], key: str, payload: dict[str, Any]) -> None:
    ext = _ensure_extension(obj)
    i = _find_extension_index(obj, key)
    if i == -1:
        ext.append({key: dict(payload)})
    else:
        if not isinstance(ext[i].get(key), dict):
            ext[i][key] = dict(payload)
        else:
            ext[i][key].update({k: v for k, v in payload.items()})
