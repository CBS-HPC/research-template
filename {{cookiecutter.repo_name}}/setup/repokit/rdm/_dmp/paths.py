from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Union

from .compat import PROJECT_ROOT, read_toml, write_toml
from .config import JSON_FILENAME, TOML_PATH

def _parse_dataset_path(raw: str | Path) -> dict:
    s = str(raw).strip().replace("\\", "/")
    sub_dir = False
    if s.endswith("/*"):
        sub_dir = True
        s = s[:-2]
    if s.startswith("./"):
        s = s[2:]
    s = s.rstrip("/")
    if not s:
        s = "."
    s = os.path.normpath(s)
    parent_path = Path(s)
    return {"parent_path": parent_path, "sub_dir": sub_dir}

def load_default_dataset_path(first_pattern: Optional[Union[str, Path]] = None) -> tuple[dict, str]:
    # 1) explicit argument
    if isinstance(first_pattern, (str, Path)):
        s = str(first_pattern).strip()
        first_pattern = s if s else None
    else:
        first_pattern = None

    # 2) TOML config
    if not first_pattern:
        cfg = read_toml(
            folder=str(PROJECT_ROOT),
            json_filename=JSON_FILENAME,
            tool_name="datasets",
            toml_path=TOML_PATH,
        ) or {}
        patterns = cfg.get("patterns")
        if isinstance(patterns, (list, tuple)):
            for p in patterns:
                if not p:
                    continue
                s = str(p).strip()
                if s:
                    first_pattern = s
                    break
        elif isinstance(patterns, (str, Path)):
            s = str(patterns).strip()
            if s:
                first_pattern = s

    # 3) fallback + write back
    if not first_pattern:
        first_pattern = str(PROJECT_ROOT / "/data/*")
        write_toml(
            data={"patterns": first_pattern},
            folder=str(PROJECT_ROOT),
            json_filename=JSON_FILENAME,
            tool_name="datasets",
            toml_path=TOML_PATH,
        )

    return _parse_dataset_path(first_pattern), str(first_pattern)

def to_bytes_mb(mb) -> int | None:
    try:
        return int(round(float(mb) * 1024 * 1024))
    except Exception:
        return None

def norm_rel_urlish(p: str | None) -> str | None:
    if not p or not isinstance(p, str):
        return None
    p2 = p.strip().replace("\\", "/")
    if not p2:
        return None
    try:
        path_obj = Path(p2)
        if path_obj.is_absolute():
            try:
                rel = path_obj.relative_to(PROJECT_ROOT)
                p2 = rel.as_posix()
            except ValueError:
                p2 = path_obj.as_posix()
        else:
            p2 = path_obj.as_posix()
    except Exception:
        pass
    while p2.startswith("./"):
        p2 = p2[2:]
    return p2 or None

def data_type_from_path(p: str) -> str:
    cfg, _ = load_default_dataset_path()
    parent = Path(cfg["parent_path"])
    use_subdirs = bool(cfg.get("sub_dir", False))
    if not use_subdirs:
        return "Uncategorised"
    norm = Path(p.replace("\\", "/"))
    try:
        rel = norm.relative_to(parent)
    except ValueError:
        try:
            rel = norm.resolve().relative_to(parent.resolve())
        except Exception:
            return "Uncategorised"
    parts = rel.parts
    if len(parts) >= 2:
        return parts[0]
    return "Uncategorised"
