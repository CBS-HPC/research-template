from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

import streamlit as st

from .deps import (
    ensure_required_by_schema,
    normalize_datasets_in_place,
    normalize_root_in_place,
    now_iso_minute,
    reorder_dmp_keys,
    repair_empty_enums,
)
from .schema_editors import safe_fetch_schema


def schema_fixups_in_place(data: dict[str, Any]) -> dict[str, Any]:
    schema = safe_fetch_schema()
    normalize_root_in_place(data, schema=schema)
    normalize_datasets_in_place(data, schema=schema)
    if schema:
        ensure_required_by_schema(data, schema)
        repair_empty_enums(
            data.get("dmp", {}),
            schema,
            schema.get("properties", {}).get("dmp", {}),
            path="dmp",
        )
    return data


def ordered_output_without_touching_modified() -> dict[str, Any]:
    """
    Make a canonical, ordered snapshot WITHOUT bumping dmp.modified.
    Used only for autosave-change detection.
    """
    snap = deepcopy(st.session_state["data"])
    snap = reorder_dmp_keys(schema_fixups_in_place(snap))
    snap.setdefault("dmp", {}).setdefault("modified", snap.get("dmp", {}).get("modified", ""))
    return snap


def json_hash_for_autosave(obj: dict[str, Any]) -> str:
    payload = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


def autosave_if_changed(force_write: bool = False) -> None:
    """
    If the DMP content changed since last snapshot, bump modified and write to disk.
    Also sync cookiecutter.json from the current DMP.

    If `force_write=True`, we always write once even if this is the first call
    (i.e. no existing baseline hash yet).
    """
    from .deps import update_cookiecutter_from_dmp  # avoid import cycles

    if "save_path" not in st.session_state or not st.session_state["save_path"]:
        return
    base_path = Path(st.session_state["save_path"]).resolve()
    base_path.parent.mkdir(parents=True, exist_ok=True)

    current_snapshot = ordered_output_without_touching_modified()
    current_hash = json_hash_for_autosave(current_snapshot)

    first_call = "__autosave_last_hash__" not in st.session_state

    if first_call and not force_write:
        st.session_state["__autosave_last_hash__"] = current_hash
        st.session_state["__autosave_feedback__"] = f"Autosave ready – changes will be saved to {base_path.name}"
        return

    if (not first_call) and current_hash == st.session_state["__autosave_last_hash__"]:
        return

    to_save = deepcopy(current_snapshot)
    try:
        to_save["dmp"]["modified"] = now_iso_minute()
    except Exception:
        pass

    try:
        base_path.write_text(json.dumps(to_save, indent=4, ensure_ascii=False), encoding="utf-8")
        st.session_state["__autosave_last_hash__"] = current_hash
        st.session_state["__autosave_feedback__"] = f"💾 Autosaved {base_path.name} at {datetime.now().strftime('%H:%M:%S')}"

        try:
            update_cookiecutter_from_dmp(dmp_path=base_path)
        except Exception as e:
            st.session_state["__autosave_feedback__"] += f" (cookiecutter sync failed: {e})"

    except Exception as e:
        st.session_state["__autosave_feedback__"] = f"⚠️ Autosave failed: {e}"
