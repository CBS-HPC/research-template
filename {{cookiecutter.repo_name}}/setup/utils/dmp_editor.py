#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit RDA-DMP JSON editor with per-dataset publish buttons:
- "Publish to Zenodo"
- "Publish to DeiC Dataverse"

Depends on:
- utils/general_tools.py  (package_installer, load/save helpers if you use them)
- utils/dmp_tools.py      (fetch_schema, ensure_dmp_shape, reorder_dmp_keys, now_iso_minute, etc.)
- publish_from_dmp.py     (publisher with  mapping + streamlit wrappers)
- streamlit_tokens.py     (token retrieval via secrets/env/sidebar)

Run:
  streamlit run dmp_editor.py
"""
import os
import sys
import json
import getpass
import socket
import ipaddress
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import date, datetime


# --- Robust imports whether run as a package (CLI) or directly via `streamlit run` ---
try:
    from .general_tools import package_installer, load_from_env, save_to_env 
    from .dmp_tools import *  # noqa: F401,F403
    #from .publish_from_dmp import *
    from .publish_common import *
    from .publish_zenodo import *
    from .publish_dataverse import *


except ImportError:
    pkg_root = Path(__file__).resolve().parent
    #sys.path.insert(0, str(pkg_root / "utils"))
    sys.path.insert(0, str(pkg_root))
    from utils.general_tools import package_installer, load_from_env, save_to_env 
    from utils.dmp_tools import *  # noqa: F401,F403
    #from utils.publish_from_dmp import *
    from utils.publish_common import *
    from utils.publish_zenodo import *
    from utils.publish_dataverse import *

package_installer(required_libraries=["streamlit", "jsonschema"])

import streamlit as st
from streamlit.web.cli import main as st_main
from jsonschema import Draft7Validator


def _has_privacy_flags(ds: dict) -> bool:
    return str(ds.get("personal_data", "")).lower() == "yes" or \
           str(ds.get("sensitive_data", "")).lower() == "yes"

def _enforce_privacy_access(ds: dict) -> bool:
    """If personal/sensitive == yes, force all distributions to closed."""
    changed = False
    for dist in ds.get("distribution", []) or []:
        if _has_privacy_flags(ds) and dist.get("data_access") != "closed":
            dist["data_access"] = "closed"
            changed = True
    return changed

def _normalize_license_by_access(ds: dict) -> bool:
    """
    If data_access is shared/closed, remove CC license URLs (misleading for non-open).
    Allows non-CC/custom terms URLs to remain.
    """
    changed = False
    for dist in ds.get("distribution", []) or []:
        access = (dist.get("data_access") or "").lower()
        if access in {"shared", "closed"}:
            for lic in dist.get("license", []) or []:
                ref = (lic or {}).get("license_ref") or ""
                if "creativecommons.org" in ref:
                    lic["license_ref"] = ""
                    changed = True
    return changed

def _ensure_open_has_license(ds: dict) -> bool:
    """
    If data_access is open and license is empty, set a sensible default (e.g., CC-BY-4.0).
    Skip if the user already put something in.
    """
    changed = False
    default_ref = LICENSE_LINKS.get("CC-BY-4.0", "")
    for dist in ds.get("distribution", []) or []:
        if (dist.get("data_access") or "").lower() == "open":
            lics = dist.get("license") or []
            if not lics:
                dist["license"] = [{"license_ref": default_ref, "start_date": today_iso()}]
                changed = True
            else:
                for lic in lics:
                    if not (lic or {}).get("license_ref"):
                        lic["license_ref"] = default_ref
                        changed = True
    return changed

def _inject_dist_css_once() -> None:
    # Only add very light styling; keep expanders fully clickable.
    if st.session_state.get("__dist_css__"):
        return
    st.session_state["__dist_css__"] = True
    st.markdown(
        """
        <style>
        /* Subtle background and left border for expander bodies (applies everywhere) */
        [data-testid="stExpander"] > div {
            border-left: 3px solid #c8d6e5;
            background: rgba(0,0,0,.02);
            padding: .6rem 1rem .8rem 1rem;
            border-radius: 6px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def _is_dataset_path(path: tuple) -> bool:
    return (
        isinstance(path, tuple)
        and len(path) == 3
        and path[0] == "dmp"
        and path[1] == "dataset"
        and isinstance(path[2], int)
    )

def _edit_distribution_inline(arr: List[Any], path: tuple, ns: Optional[str] = None) -> List[Any]:
    if not isinstance(arr, list):
        return arr

    # If empty, seed one distribution so users can fill it in
    if not arr:
        templates = dmp_default_templates()
        arr.append(deepcopy(templates["distribution"]))

    # Single distribution → show inline under a normal, closable expander
    if len(arr) == 1 and isinstance(arr[0], dict):
        _inject_dist_css_once()
        with st.expander("Distribution", expanded=True):
            arr[0] = edit_any(arr[0], path=(*path, 0), ns=ns)
        return arr

    # 2+ distributions → default list UI
    return edit_array(arr, path=path, title_singular="Distribution", removable_items=True, ns=ns)

def _edit_dataset_id_inline(obj: Any, path: tuple, ns: Optional[str] = None) -> Dict[str, Any]:
    """
    Render dataset_id inline (inside its own closable expander).
    Seeds from templates if missing/empty.
    """
    if not isinstance(obj, dict) or not obj:
        templates = dmp_default_templates()
        obj = deepcopy(templates["dataset"]["dataset_id"])
    with st.expander("Dataset ID", expanded=True):
        obj = edit_any(obj, path=path, ns=ns)   # path already includes "dataset_id"
    return obj

def _ensure_dataset_id_before_distribution(keys: List[str]) -> List[str]:
    # If both exist and dataset_id comes after distribution, move it just before.
    if "dataset_id" in keys and "distribution" in keys:
        di, dj = keys.index("dataset_id"), keys.index("distribution")
        if di > dj:
            k = keys.pop(di)
            keys.insert(dj, k)
    return keys


# ──────────────────────────────────────────────────────────────────────────────
# Minimal helpers (schema-aware editors)  — unchanged parts from your editor
# ──────────────────────────────────────────────────────────────────────────────

def _key_for(*parts: Any) -> str:
    return "|".join(str(p) for p in parts if p is not None)

def _parse_iso_date(s: Any) -> Optional[date]:
    if isinstance(s, date) and not isinstance(s, datetime):
        return s
    if isinstance(s, str) and s:
        try:
            return datetime.strptime(s, "%Y-%m-%d").date()
        except Exception:
            return None
    return None

def _get_schema_cached() -> Optional[Dict[str, Any]]:
    key = "__rda_schema__"
    if key in st.session_state:
        return st.session_state[key]
    try:
        sch = fetch_schema()
        st.session_state[key] = sch
        return sch
    except Exception:
        st.session_state[key] = None
        return None

def safe_fetch_schema() -> Optional[Dict[str, Any]]:
    return _get_schema_cached()

def _schema_node_for_path(path: tuple) -> Optional[Dict[str, Any]]:
    schema = safe_fetch_schema()
    if not schema:
        return None

    def _resolve_ref(n: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(n, dict):
            return {}
        if "$ref" in n:
            ref = n["$ref"]
            if not (isinstance(ref, str) and ref.startswith("#/")):
                return {}
            cur: Any = schema
            for part in ref[2:].split("/"):
                part = part.replace("~1", "/").replace("~0", "~")
                cur = cur.get(part, {})
            n = cur if isinstance(cur, dict) else {}
        return n

    node: Dict[str, Any] = schema
    for comp in path:
        node = _resolve_ref(node)
        if isinstance(comp, str):
            props = node.get("properties")
            if isinstance(props, dict) and comp in props:
                node = props[comp]; continue
            if node.get("type") == "array" and isinstance(node.get("items"), dict):
                items = _resolve_ref(node["items"])
                props = items.get("properties")
                if isinstance(props, dict) and comp in props:
                    node = props[comp]; continue
            return None
        else:
            if node.get("type") == "array" and isinstance(node.get("items"), dict):
                node = node["items"]; continue
            return None
    return _resolve_ref(node)

def _is_format_schema(path: tuple, fmt: str) -> bool:
    node = _schema_node_for_path(path)
    return bool(node and node.get("type") == "string" and node.get("format") == fmt)

def _is_boolean_schema(path: tuple) -> bool:
    node = _schema_node_for_path(path)
    return bool(node and node.get("type") == "boolean")

def _coerce_to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value in (None, ""):
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    if isinstance(value, (int, float)):
        return value != 0
    return False

STRING_LIST_HINTS = {"data_quality_assurance", "keyword", "format", "pid_system", "role"}

def _looks_like_string_list(arr: List[Any], path: tuple) -> bool:
    if arr and all(isinstance(x, str) for x in arr):
        return True
    return (not arr) and bool(path) and (path[-1] in STRING_LIST_HINTS)

def _path_signature(path: tuple) -> str:
    parts: List[str] = []
    for p in path:
        if isinstance(p, int):
            if parts:
                parts[-1] = parts[-1] + "[]"
            else:
                parts.append("[]")
        else:
            parts.append(str(p))
    return ".".join(parts)

def _enum_info_for_path(path: tuple):
    # Enums are loaded from schema + EXTRA_ENUMS (from dmp_tools)
    node = _schema_node_for_path(path)
    base_mode: Optional[str] = None
    base_options: List[str] = []
    if node:
        if node.get("type") == "string" and isinstance(node.get("enum"), list):
            base_mode = "single"; base_options = list(node["enum"])
        elif node.get("type") == "array":
            it = node.get("items")
            if isinstance(it, dict) and it.get("type") == "string" and isinstance(it.get("enum"), list):
                base_mode = "multi"; base_options = list(it["enum"])
    sig = _path_signature(path)
    try:
        extras = EXTRA_ENUMS.get(sig, [])  # type: ignore[name-defined]
    except Exception:
        extras = []
    extra_values: List[str] = []
    if isinstance(extras, list):
        if extras and isinstance(extras[0], dict):
            extra_values = [d.get("value", "") for d in extras if isinstance(d, dict) and d.get("value")]
        else:
            extra_values = [str(x) for x in extras]
    inferred_mode: Optional[str] = None
    if node and node.get("type") == "array":
        inferred_mode = "multi"
    elif node and node.get("type") == "string":
        inferred_mode = "single"
    elif (base_options or extra_values):
        inferred_mode = "single"
    merged = list(dict.fromkeys(base_options + extra_values))
    if not merged:
        return (None, [])
    return (base_mode or inferred_mode or "single", merged)

def _enum_label_for(path: tuple, option_value: str) -> str:
    sig = _path_signature(path)
    try:
        extras = EXTRA_ENUMS.get(sig, [])  # type: ignore[name-defined]
    except Exception:
        extras = []
    if isinstance(extras, list):
        for d in extras:
            if isinstance(d, dict):
                if d.get("value") == option_value:
                    return d.get("label", option_value)
    return str(option_value)

def edit_primitive(label: str, value: Any, path: tuple, ns: Optional[str] = None) -> Any:
    

    if _is_boolean_schema(path) or (path and path[-1] == "is_reused"):
        keyb = _key_for(*path, ns, "bool")
        return st.checkbox(label, value=_coerce_to_bool(value), key=keyb)
    
    if _is_format_schema(path, "date"):
        base_key    = _key_for(*path, ns, "date")           # date_input widget key
        enable_key  = _key_for(*path, ns, "date_enabled")   # whether picker is enabled
        pending_key = _key_for(*path, ns, "date_pending")   # one-shot flag to seed today after "Set date"
        set_key     = _key_for(*path, ns, "date_set_btn")   # button: Set date
        clear_key   = _key_for(*path, ns, "date_clear_btn") # button: Clear

        # Current value from the DMP (string -> date or None)
        existing = _parse_iso_date(value)

        # Initialize enable flag on first render of this field
        if enable_key not in st.session_state:
            st.session_state[enable_key] = bool(existing)

        enabled = bool(st.session_state[enable_key])

        c1, c2 = st.columns([4, 1])

        # --- Right column: buttons FIRST (so we can update state before the widget is created)
        with c2:
            st.markdown("<div style='height:0.15rem'></div>", unsafe_allow_html=True)

            if enabled:
                # Only allow clearing if a date actually exists (in session or DMP)
                has_date_now = (base_key in st.session_state) or bool(existing)
                if st.button("Clear", key=clear_key, disabled=not has_date_now):
                    # Remove any staged widget value *before* creating the widget
                    st.session_state.pop(base_key, None)
                    st.session_state[enable_key] = False
                    enabled = False  # reflect immediately; no rerun required
            else:
                if st.button("Set date", key=set_key):
                    # Arm a one-shot to seed the picker with today on this very run
                    st.session_state[enable_key] = True
                    st.session_state[pending_key] = True
                    enabled = True  # reflect immediately; no rerun required

        # --- Left column: the date picker (created AFTER button logic)
        with c1:
            # Decide default shown in the picker (this does not save to the DMP until we return)
            seed_today = bool(st.session_state.pop(pending_key, False))
            if seed_today and not existing:
                cur = date.today()
            else:
                # Prefer any existing widget value (if present), else DMP value, else show today (UI only)
                cur = st.session_state.get(base_key) or existing or date.today()

            picked = st.date_input(
                label,
                value=cur,
                key=base_key,
                disabled=not enabled,
            )

        # Commit to DMP:
        # - when disabled → keep empty string (no date in the JSON)
        # - when enabled  → save whatever is picked
        return "" if not enabled else (picked.isoformat() if isinstance(picked, date) else "")
        

    mode, options = _enum_info_for_path(path)
    if mode == "single" and options:
        sel_key = _key_for(*path, ns, "enum")
        options_ui = list(options)
        custom_label = None
        if value not in (None, "") and value not in options_ui:
            custom_label = f"(custom) {value}"
            options_ui = [custom_label] + options_ui
            default_index = 0
        else:
            try:
                default_index = options_ui.index(value)
            except Exception:
                default_index = 0
        selected = st.selectbox(
            label,
            options_ui,
            index=default_index,
            key=sel_key,
            format_func=lambda opt: _enum_label_for(path, opt if opt != custom_label else value),
        )
        return value if (custom_label and selected == custom_label) else selected
    key = _key_for(*path, ns, "prim")
    if isinstance(value, bool):
        return st.checkbox(label, value=value, key=key)
    if isinstance(value, int):
        txt = st.text_input(label, str(value), key=key)
        try: return int(txt) if txt != "" else None
        except Exception: return value
    if isinstance(value, float):
        txt = st.text_input(label, str(value), key=key)
        try: return float(txt) if txt != "" else None
        except Exception: return value
    txt = st.text_input(label, "" if value is None else str(value), key=key)
    return txt

def edit_array(arr: List[Any], path: tuple, title_singular: str, removable_items: bool, ns: Optional[str] = None) -> List[Any]:
    mode, options = _enum_info_for_path(path)

    # Enum-multi arrays: use multiselect as before
    if mode == "multi" and options:
        label = f"{path[-1] if path else title_singular} (choose any)"
        wkey = _key_for(*path, ns, "enum_multi")
        current = [x for x in arr if isinstance(x, str) and x in options]
        selected = st.multiselect(
            label, options, default=current, key=wkey,
            format_func=lambda opt: _enum_label_for(path, opt),
        )
        return selected

    # Simple string lists: textarea as before
    if _looks_like_string_list(arr, path):
        label = f"{path[-1] if path else title_singular} (one per line; saved as array)"
        key = _key_for(*path, ns, "textlist")
        initial = "\n".join(x for x in arr if isinstance(x, str))
        txt = st.text_area(label, initial, key=key)
        lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]
        return lines

    # NEW: Inline rendering for single-object arrays
    if len(arr) == 1 and isinstance(arr[0], dict):
        # Small caption to indicate we're editing the single entry directly
        label = path[-1] if path else title_singular
        st.caption(f"{label} — single entry")
        arr[0] = edit_any(arr[0], path=(*path, 0), ns=ns)
        # Optional: allow removing the sole entry if the caller asked for it
        if removable_items and st.button(f"Remove this {title_singular.lower()}", key=_key_for(*path, ns, "rm_single")):
            arr.clear()
        return arr

    # Default: one expander per item
    to_delete: List[int] = []
    for i, item in enumerate(list(arr)):
        heading = f"{title_singular} #{i+1}"
        if isinstance(item, dict):
            for pick in ("title", "name", "identifier"):
                if item.get(pick):
                    heading = f"{title_singular} #{i+1}: {item[pick]}"; break
        with st.expander(heading, expanded=False):
            arr[i] = edit_any(item, path=(*path, i), ns=ns)
            if removable_items and st.button(f"Remove this {title_singular.lower()}", key=_key_for(*path, i, ns, "rm")):
                to_delete.append(i)
    for i in reversed(to_delete):
        del arr[i]
    return arr

def edit_object(obj: Dict[str, Any], path: tuple, allow_remove_keys: bool, ns: Optional[str] = None) -> Dict[str, Any]:
    keys = list(obj.keys())

    # NEW: keep dataset_id visually above distribution when editing a dataset
    if _is_dataset_path(path):
        keys = _ensure_dataset_id_before_distribution(keys)

    remove_keys: List[str] = []
    for key in keys:
        val = obj.get(key)

        # Keep Projects/Datasets/Contributors out of the root object editor; they get bespoke UIs
        if path == ("dmp",) and key in ("project", "dataset", "contributor"):
            continue

        # Special-case: extension as before (optional)
        if key == "extension" and isinstance(val, list):
            with st.expander("extension", expanded=False):
                obj["extension"] = edit_array(val, path=(*path, "extension"), title_singular="Entry", removable_items=True, ns=ns)
            continue

        if isinstance(val, dict):
            # NEW: unfold dataset_id inline for datasets
            if key == "dataset_id" and _is_dataset_path(path):
                obj[key] = _edit_dataset_id_inline(val, path=(*path, key), ns=ns)
                continue

            with st.expander(key, expanded=False):
                obj[key] = edit_any(val, path=(*path, key), ns=ns)

        elif isinstance(val, list):
            # Existing special-case for distribution
            if key == "distribution" and _is_dataset_path(path):
                obj[key] = _edit_distribution_inline(val, path=(*path, key), ns=ns)
                continue
            with st.expander(key, expanded=False):
                title = "Distribution" if key == "distribution" else "Item"
                obj[key] = edit_array(val, path=(*path, key), title_singular=title, removable_items=False, ns=ns)

        else:
            obj[key] = edit_primitive(key, val, path=(*path, key), ns=ns)

        if allow_remove_keys and st.button(f"Remove key: {key}", key=_key_for(*path, key, ns, "del")):
            remove_keys.append(key)

    for k in remove_keys:
        obj.pop(k, None)
    return obj

def edit_any(value: Any, path: tuple, ns: Optional[str] = None) -> Any:
    if isinstance(value, dict):
        return edit_object(value, path, allow_remove_keys=False, ns=ns)
    if isinstance(value, list):
        return edit_array(value, path, title_singular="Item", removable_items=False, ns=ns)
    return edit_primitive("value", value, path, ns=ns)


# ──────────────────────────────────────────────────────────────────────────────
# High-level sections (Root, Projects, Datasets)
# ──────────────────────────────────────────────────────────────────────────────

def find_default_dmp_path(start: Optional[Path] = None) -> Path:
    start = start or Path(__file__).resolve().parent
    candidates = ["dmp.json"]
    for base in [start, *start.parents]:
        for name in candidates:
            p = base / name
            if p.exists():
                return p
    return Path("./dmp.json") if not Path(DEFAULT_DMP_PATH).exists() else Path(DEFAULT_DMP_PATH)

def draw_root_section(dmp_root: Dict[str, Any]) -> None:
    st.subheader("Root")

    # Ensure required keys exist
    dmp_root.setdefault("schema", dmp_root.get("schema") or SCHEMA_URLS[SCHEMA_VERSION])
    dmp_root.setdefault("contact", dmp_root.get("contact") or {
        "name": "",
        "mbox": "",
        "contact_id": {"type": "orcid", "identifier": ""},
    })

    # Template for a new contributor (use your template if available)
    templates = dmp_default_templates() if "dmp_default_templates" in globals() else {}
    default_contrib = deepcopy(templates.get("contributor")) if templates and "contributor" in templates else {
        "name": "",
        "mbox": "",
        "contributor_id": {"type": "orcid", "identifier": ""},
        "role": [],  # array of strings per 1.2 schema
    }

    # --- The rest of the Root fields (excluding project/dataset/contact/contributor) ---
    for key in list(dmp_root.keys()):
        if key in ("project", "dataset"):
            continue
        val = dmp_root.get(key)
        if isinstance(val, dict):
            with st.expander(key, expanded=False):
                dmp_root[key] = edit_any(val, path=("dmp", key), ns=None)
        elif isinstance(val, list):
            with st.expander(key, expanded=False):
                dmp_root[key] = edit_array(val, path=("dmp", key), title_singular="Item", removable_items=False, ns=None)
        else:
            dmp_root[key] = edit_primitive(key, val, path=("dmp", key), ns=None)

    # --- ADD CONTRIBUTOR button (bottom of Root) ---
    add_col, _ = st.columns([1, 6])
    with add_col:
        if st.button("➕ Add contributor", key=_key_for("dmp", "contributor", "add", "bottom")):
            # Append and force an immediate rerun so it shows up right away
            dmp_root["contributor"].append(deepcopy(default_contrib))
            st.rerun()

def draw_projects_section(dmp_root: Dict[str, Any]) -> None:
    st.subheader("Projects")
    projects: List[Dict[str, Any]] = dmp_root.setdefault("project", [])
    cols = st.columns(2)
    templates = dmp_default_templates()
    with cols[0]:
        if st.button("➕ Add project", key=_key_for("project", "add")):
            projects.append(templates["project"])
    dmp_root["project"] = edit_array(projects, path=("dmp", "project"), title_singular="Project", removable_items=True, ns=None)

def draw_datasets_section(dmp_root: dict) -> None:
    st.subheader("Datasets")
    datasets = dmp_root.setdefault("dataset", [])
    top = st.columns([1, 3])
    templates = dmp_default_templates()
    with top[0]:
        if st.button("➕ Add dataset", key=_key_for("dataset", "add")):
            datasets.append(templates["dataset"])
            st.success("Dataset added")

    def _is_unknown(v: Any) -> bool:
        s = str(v or "").strip().lower()
        return s in {"unknown", "unkown", ""}  # treat blank as unknown too

    for i, ds in enumerate(list(datasets)):
        with st.expander(f"Dataset #{i+1}: {ds.get('title') or 'Dataset'}", expanded=False):
            is_reused = _is_reused(ds)

            # Disable publishing if personal/sensitive is unknown
            has_unknown_privacy = _is_unknown(ds.get("personal_data")) or _is_unknown(ds.get("sensitive_data"))

            # Read/maintain override flag from session
            override_key = f"allow_reused_{i}"
            allow_override = st.session_state.get(override_key, False)

            # If not reused, force override off (prevents stale True)
            if not is_reused and allow_override:
                st.session_state[override_key] = False
                allow_override = False

            # Disable rules
            zen_disabled = (is_reused and not allow_override) or has_unknown_privacy
            dv_disabled  = (is_reused and not allow_override) or has_unknown_privacy

            # Button row
            cols = st.columns([1, 1, 1, 1, 6])

            with cols[0]:
                if st.button("🗑️ Remove this dataset", key=f"rm_ds_{i}"):
                    del datasets[i]
                    st.stop()

            with cols[1]:
                if st.button("Publish to Zenodo", key=f"pub_zen_{i}", disabled=zen_disabled):
                    token = get_token_from_state("zenodo")
                    if not token:
                        st.warning("Please set a Zenodo token in the sidebar and press Save.")
                        st.stop()
                    try:
                        res = streamlit_publish_to_zenodo(
                            dataset=ds,
                            dmp=st.session_state["data"],
                            token=token,
                            sandbox=True,
                            publish=False,
                            allow_reused=allow_override,
                        )
                    except PublishError as e:
                        st.error(str(e))

            with cols[2]:
                if st.button("Publish to DeiC Dataverse", key=f"pub_dv_{i}", disabled=dv_disabled):
                    token = get_token_from_state("dataverse")
                    if not token:
                        st.warning("Please set a Dataverse token in the sidebar and press Save.")
                        st.stop()
                    try:
                        res = streamlit_publish_to_dataverse(
                            dataset=ds,
                            dmp=st.session_state["data"],
                            token=token,
                            base_url="https://dataverse.deic.dk",
                            alias="tmpdemo",
                            publish=False,
                            release_type="major",
                            allow_reused=allow_override,
                        )
                    except PublishError as e:
                        st.error(str(e))

            # Only active if the dataset is marked as reused
            with cols[3]:
                st.checkbox(
                    "Allow publish reused?",
                    key=override_key,
                    value=allow_override,
                    disabled=not is_reused,  # <-- inactive unless reused
                    help="Enabled only when 'is_reused' is set on this dataset.",
                )

            # show/edit dataset metadata
            datasets[i] = edit_any(ds, path=("dmp", "dataset", i), ns="deep")

            # Post-edit guardrails
            changed = False
            changed |= _enforce_privacy_access(datasets[i])          # force data_access="closed" if personal/sensitive == yes
            changed |= _normalize_license_by_access(datasets[i])     # strip CC licenses when shared/closed
            changed |= _ensure_open_has_license(datasets[i])         # add default CC for open (if empty)

            if changed:
                # optional toast after the rerun
                st.session_state["__last_rule_msg__"] = (
                    "Privacy flags require closed access; adjusted access/license fields."
                    if _has_privacy_flags(datasets[i])
                    else "Adjusted license to match access."
                )
                st.rerun()

def _is_reused(ds: dict) -> bool:
    """maDMP 1.2 `is_reused` means the data were not produced by this project."""
    v = ds.get("is_reused")
    # Be tolerant to truthy strings/values:
    return str(v).strip().lower() in {"true", "1", "yes"}

TOKENS_STATE = {
    "zenodo": {"env_key": "ZENODO_TOKEN", "state_key": "__token_zenodo__"},
    "dataverse": {"env_key": "DATAVERSE_TOKEN", "state_key": "__token_dataverse__"},
}

def render_token_controls():
    """Render a single sidebar section that:
       - shows current token source (secrets/env)
       - lets the user enter a token
       - saves it to .env on submit
       - mirrors it into st.session_state for immediate use
    """
    with st.sidebar:
        st.header("Repository tokens")

        for service in ("zenodo", "dataverse"):
            env_key   = TOKENS_STATE[service]["env_key"]
            state_key = TOKENS_STATE[service]["state_key"]

            # 1) Prefer st.secrets if present
            token = ""
            try:
                token = st.secrets[env_key]  # type: ignore[index]
            except Exception:
                token = ""

            # 2) Then .env / process env
            if not token:
                token = os.environ.get(env_key) or (load_from_env(env_key) or "")

            # 3) Mirror whatever we found into session (so buttons can use it)
            if state_key not in st.session_state:
                st.session_state[state_key] = token

            st.subheader(service.capitalize())
            # Buffered form — only commits on submit
            with st.form(f"{service}_token_form", clear_on_submit=False):
                entered = st.text_input(
                    f"{service.capitalize()} API token",
                    type="password",
                    value=st.session_state[state_key],
                    help="Click Save to write to .env and update session.",
                )
                submitted = st.form_submit_button("Save")
                if submitted:
                    if entered.strip():
                        # Persist & reflect immediately
                        save_to_env(entered.strip(), env_key)   # (value, key)
                        os.environ[env_key] = entered.strip()   # immediate availability
                        st.session_state[state_key] = entered.strip()
                        st.success(f"Saved {env_key} to .env and updated session.")
                    else:
                        st.warning("Please enter a non-empty token.")

def get_token_from_state(service: str) -> str:
    """Read the best-known token without rendering UI."""
    service = service.lower().strip()
    env_key   = TOKENS_STATE[service]["env_key"]
    state_key = TOKENS_STATE[service]["state_key"]

    # priority: session (set by form) -> secrets -> env/.env
    val = st.session_state.get(state_key, "")
    if val:
        return val
    try:
        val = st.secrets[env_key]  # type: ignore[index]
        if val:
            return val
    except Exception:
        pass
    return os.environ.get(env_key) or (load_from_env(env_key) or "")

# ──────────────────────────────────────────────────────────────────────────────
# App
# ──────────────────────────────────────────────────────────────────────────────

def _schema_fixups_in_place(data: Dict[str, Any]) -> Dict[str, Any]:
    schema = safe_fetch_schema()
    normalize_root_in_place(data, schema=schema)
    normalize_datasets_in_place(data, schema=schema)
    if schema:
        ensure_required_by_schema(data, schema)
        repair_empty_enums(
            data.get("dmp", {}), schema, schema.get("properties", {}).get("dmp", {}), path="dmp",
        )
    return data

def _ensure_data_initialized(default_path: Path) -> None:
    """Ensure st.session_state['data'] exists and track its source + message."""
    st.session_state.setdefault("__loaded_from__", "")
    st.session_state.setdefault("__last_upload_hash__", None)
    st.session_state.setdefault("__load_message__", "")
    st.session_state.setdefault("save_path", str(default_path))  # default initial save target

    if "data" in st.session_state and st.session_state["data"]:
        st.session_state["data"] = ensure_dmp_shape(st.session_state["data"])
        return

    if default_path.exists():
        try:
            with default_path.open("r", encoding="utf-8") as f:
                st.session_state["data"] = ensure_dmp_shape(json.load(f))
            st.session_state["__loaded_from__"] = str(default_path.resolve())
            st.session_state["__load_message__"] = f"✅ Loaded default DMP from {default_path.resolve()}"
            st.session_state["save_path"] = str(default_path.resolve())
            return
        except Exception as e:
            st.warning(f"Failed to load default DMP. Started empty. Error: {e}")

    st.session_state["data"] = ensure_dmp_shape({})
    st.session_state["__loaded_from__"] = "new"
    st.session_state["__load_message__"] = "⚠️ Started with an empty DMP."
    # still keep save_path pointing to default_path
    st.session_state["save_path"] = str(default_path)

def main() -> None:
    st.set_page_config(page_title=f"RDA-DMP {SCHEMA_VERSION} JSON Editor", layout="wide")
    st.title(f"RDA-DMP {SCHEMA_VERSION} JSON Editor")

    _inject_dist_css_once()

    # ---------------------------
    # Session defaults (for UX)
    # ---------------------------
    st.session_state.setdefault("__loaded_from__", "")
    st.session_state.setdefault("__load_message__", "")
    st.session_state.setdefault("__last_upload_hash__", None)  # debounces same-file re-uploads
    st.session_state.setdefault("__uploader_ver__", 0)         # bump to reset file_uploader widget
    st.session_state.setdefault("save_path", "")               # current save target path

    # ---------------------------
    # Tokens UI (Zenodo / Dataverse)
    # ---------------------------
    render_token_controls()

    # ---------------------------
    # Schema & default DMP path
    # ---------------------------
    schema_now = safe_fetch_schema()
    default_path = find_default_dmp_path()

    # Initialize data (loads default file if present, sets load message/save_path)
    _ensure_data_initialized(default_path)

    # Show load message directly under title
    if st.session_state.get("__load_message__"):
        st.info(st.session_state["__load_message__"])

    # Helper: produce ordered/validated output snapshot
    def _current_ordered_output() -> Dict[str, Any]:
        st.session_state["data"]["dmp"]["modified"] = now_iso_minute()
        return reorder_dmp_keys(_schema_fixups_in_place(deepcopy(st.session_state["data"])))

    # Working folder for all files = directory of the default dmp
    working_folder: Path = default_path.parent

    # ---------------------------
    # Sidebar: Load / Save
    # ---------------------------
    with st.sidebar:
        st.header("Load / Save")
        st.caption(f"Schema: {'✅ loaded' if schema_now else '⚠️ unavailable (fallbacks)'}")

        # --- OPEN JSON: uploader that loads immediately, saves into working_folder, and syncs save_path ---
        uploader_key = f"open_json_uploader_{st.session_state['__uploader_ver__']}"
        uploaded = st.file_uploader(
            "Open JSON",
            type=["json"],
            help=f"Uploads are saved to: {working_folder.resolve()}",
            key=uploader_key,
        )

        # CASE A: user selected a file (and it's new content)
        if uploaded is not None:
            import hashlib
            payload = uploaded.getvalue()
            h = hashlib.sha256(payload).hexdigest()
            if st.session_state.get("__last_upload_hash__") != h:
                try:
                    # Save uploaded file into working folder with its original filename
                    working_folder.mkdir(parents=True, exist_ok=True)
                    dst_path = (working_folder / uploaded.name).resolve()
                    dst_path.write_bytes(payload)

                    # Load into the app
                    data = json.loads(payload.decode("utf-8"))
                    st.session_state["data"] = ensure_dmp_shape(data)
                    st.session_state["__last_upload_hash__"] = h
                    st.session_state["__loaded_from__"] = str(dst_path)
                    st.session_state["__load_message__"] = f"✅ Loaded DMP from {dst_path}"
                    st.session_state["save_path"] = str(dst_path)  # keep Save to path in sync
                    st.session_state.pop("ds_selected", None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to load uploaded JSON: {e}")

        # CASE B: user cleared the uploader after having uploaded before
        elif st.session_state.get("__last_upload_hash__"):
            # Reset hash marker so we don't loop
            st.session_state["__last_upload_hash__"] = None
            try:
                if default_path.exists():
                    with default_path.open("r", encoding="utf-8") as f:
                        st.session_state["data"] = ensure_dmp_shape(json.load(f))
                    st.session_state["__loaded_from__"] = str(default_path.resolve())
                    st.session_state["__load_message__"] = f"✅ Loaded default DMP from {default_path.resolve()}"
                    st.session_state["save_path"] = str(default_path.resolve())
                else:
                    # No default DMP: start fresh, target new_dmp.json
                    new_path = (working_folder / "new_dmp.json").resolve()
                    st.session_state["data"] = ensure_dmp_shape({})
                    st.session_state["__loaded_from__"] = "new"
                    st.session_state["__load_message__"] = f"⚠️ Default DMP not found. Started a new DMP (will save to {new_path})"
                    st.session_state["save_path"] = str(new_path)
                st.session_state.pop("ds_selected", None)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to reload default DMP: {e}")

        # --- NEW DMP: create empty, set save path to default_path.parent / 'new_dmp.json', reset uploader ---

        if st.button("➕ Create New DMP"):
            st.session_state["data"] = ensure_dmp_shape({})
            new_path = (working_folder / "new_dmp.json").resolve()
            st.session_state["__loaded_from__"] = "new"
            st.session_state["__load_message__"] = f"✅ Started a new DMP (will save to {new_path})"
            st.session_state["save_path"] = str(new_path)
            st.session_state["__last_upload_hash__"] = None
            st.session_state.pop("ds_selected", None)

            # Reset/clear the file_uploader by bumping the key version
            st.session_state["__uploader_ver__"] += 1
            st.rerun()

        # --- DOWNLOAD JSON: filename follows current save_path ---
        out_for_dl = _current_ordered_output()
        st.download_button(
            "⬇️ Download JSON",
            data=json.dumps(out_for_dl, indent=4, ensure_ascii=False).encode("utf-8"),
            file_name=Path(st.session_state["save_path"]).name or "dmp.json",
            mime="application/json",
            key="download",
        )

        if st.button("💾 Save to disk", key="save"):
            try:
                out = _current_ordered_output()
                schema = safe_fetch_schema()
                if schema:
                    errs = list(Draft7Validator(schema).iter_errors(out))
                    if errs:
                        st.error("Schema validation failed:")
                        for e in errs[:50]:
                            st.write(f"• {'/'.join(map(str, e.path)) or '<root>'}: {e.message}")
                        st.stop()
                else:
                    st.warning("Schema unavailable (offline?). Skipping validation.")
                p = Path(st.session_state["save_path"]).resolve()
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps(out, indent=4, ensure_ascii=False), encoding="utf-8")
                st.success(f"Saved to {p} (modified={out['dmp'].get('modified')})")
            except Exception as e:
                st.error(f"Failed to save: {e}")


    # ---------------------------
    # Main editor area
    # ---------------------------
    data = ensure_dmp_shape(st.session_state["data"])
    dmp_root = data["dmp"]
    draw_root_section(dmp_root)
    draw_projects_section(dmp_root)
    draw_datasets_section(dmp_root)

def cli() -> None:
    """
    CLI entrypoint for the Streamlit DMP editor.
    Usage:
        python dmp_editor.py          # normal mode
        python dmp_editor.py ssh      # SSH tunnel mode (prints port-forward instructions)
    """
    app_path = Path(__file__).resolve()

    # Did user request "ssh" mode?
    ssh_mode = len(sys.argv) > 1 and sys.argv[1] == "ssh"
    if ssh_mode:
        # remove "ssh" so it doesn't confuse Streamlit
        sys.argv.pop(1)

        app_port = int(os.environ.get("DMP_PORT", "8501"))
        _ssh_hint(app_port)

        cmd = f"ssh -N -L {app_port}:localhost:{app_port} example@host.dk -p PORT (The host and port you have connected)"
        print("\n=== SSH port forwarding ===")
        print("Run this on your LOCAL machine, then open the URL below:")
        print(f"  {cmd}\n")
    

        sys.argv = [
            "streamlit", "run", str(app_path),
            "--server.headless", "true",
            "--server.address", "localhost",
            "--server.port", str(app_port),
            *sys.argv[1:],
        ]
    else:
        sys.argv = ["streamlit", "run", str(app_path), *sys.argv[1:]]

    sys.exit(st_main())


if __name__ == "__main__":
    main()
