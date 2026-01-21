from __future__ import annotations

import json as _json
from copy import deepcopy
from datetime import date, datetime
from typing import Any

import streamlit as st

from .deps import EXTRA_ENUMS, dmp_default_templates, fetch_schema
from .utils import key_for


STRING_LIST_HINTS = {"data_quality_assurance", "keyword", "format", "pid_system", "role"}


def _parse_iso_date(s: Any) -> date | None:
    if isinstance(s, date) and not isinstance(s, datetime):
        return s
    if isinstance(s, str) and s:
        try:
            return datetime.strptime(s, "%Y-%m-%d").date()
        except Exception:
            return None
    return None


def _get_schema_cached() -> dict[str, Any] | None:
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


def safe_fetch_schema() -> dict[str, Any] | None:
    return _get_schema_cached()


def _schema_node_for_path(path: tuple) -> dict[str, Any] | None:
    schema = safe_fetch_schema()
    if not schema:
        return None

    def _resolve_ref(n: dict[str, Any]) -> dict[str, Any]:
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

    node: dict[str, Any] = schema
    for comp in path:
        node = _resolve_ref(node)
        if isinstance(comp, str):
            props = node.get("properties")
            if isinstance(props, dict) and comp in props:
                node = props[comp]
                continue
            if node.get("type") == "array" and isinstance(node.get("items"), dict):
                items = _resolve_ref(node["items"])
                props = items.get("properties")
                if isinstance(props, dict) and comp in props:
                    node = props[comp]
                    continue
            return None
        else:
            if node.get("type") == "array" and isinstance(node.get("items"), dict):
                node = node["items"]
                continue
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


def _looks_like_string_list(arr: list[Any], path: tuple) -> bool:
    if arr and all(isinstance(x, str) for x in arr):
        return True
    return (not arr) and bool(path) and (path[-1] in STRING_LIST_HINTS)


def _path_signature(path: tuple) -> str:
    parts: list[str] = []
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
    node = _schema_node_for_path(path)
    base_mode: str | None = None
    base_options: list[str] = []
    if node:
        if node.get("type") == "string" and isinstance(node.get("enum"), list):
            base_mode = "single"
            base_options = list(node["enum"])
        elif node.get("type") == "array":
            it = node.get("items")
            if (
                isinstance(it, dict)
                and it.get("type") == "string"
                and isinstance(it.get("enum"), list)
            ):
                base_mode = "multi"
                base_options = list(it["enum"])

    sig = _path_signature(path)
    try:
        extras = EXTRA_ENUMS.get(sig, [])  # type: ignore[name-defined]
    except Exception:
        extras = []
    extra_values: list[str] = []
    if isinstance(extras, list):
        if extras and isinstance(extras[0], dict):
            extra_values = [d.get("value", "") for d in extras if isinstance(d, dict) and d.get("value")]
        else:
            extra_values = [str(x) for x in extras]

    inferred_mode: str | None = None
    if node and node.get("type") == "array":
        inferred_mode = "multi"
    elif node and node.get("type") == "string" or base_options or extra_values:
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
            if isinstance(d, dict) and d.get("value") == option_value:
                return d.get("label", option_value)
    return str(option_value)


def _show_readonly_json(label: str, value: Any, key: str | None = None) -> None:
    with st.expander(label, expanded=False):
        try:
            st.code(_json.dumps(value, indent=2, ensure_ascii=False), language="json")
        except Exception:
            st.code(str(value), language="json")


def _is_under_dataset_extension(path: tuple) -> bool:
    return (
        isinstance(path, tuple)
        and len(path) >= 5
        and path[0] == "dmp"
        and path[1] == "dataset"
        and isinstance(path[2], int)
        and path[3] == "extension"
    )


def _inject_dist_css_once() -> None:
    if st.session_state.get("__dist_css__"):
        return
    st.session_state["__dist_css__"] = True
    st.markdown(
        """
        <style>
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


def _ensure_dataset_id_before_distribution(keys: list[str]) -> list[str]:
    if "dataset_id" in keys and "distribution" in keys:
        di, dj = keys.index("dataset_id"), keys.index("distribution")
        if di > dj:
            k = keys.pop(di)
            keys.insert(dj, k)
    return keys


def _edit_distribution_inline(arr: list[Any], path: tuple, ns: str | None = None) -> list[Any]:
    if not isinstance(arr, list):
        return arr
    if not arr:
        templates = dmp_default_templates()
        arr.append(deepcopy(templates["distribution"]))
    if len(arr) == 1 and isinstance(arr[0], dict):
        _inject_dist_css_once()
        with st.expander("Distribution", expanded=True):
            arr[0] = edit_any(arr[0], path=(*path, 0), ns=ns)
        return arr
    return edit_array(arr, path=path, title_singular="Distribution", removable_items=True, ns=ns)


def _edit_dataset_id_inline(obj: Any, path: tuple, ns: str | None = None) -> dict[str, Any]:
    if not isinstance(obj, dict) or not obj:
        templates = dmp_default_templates()
        obj = deepcopy(templates["dataset"]["dataset_id"])
    with st.expander("Dataset ID", expanded=True):
        obj = edit_any(obj, path=path, ns=ns)
    return obj


def edit_primitive(label: str, value: Any, path: tuple, ns: str | None = None) -> Any:
    # Special handling for is_reused: use dropdown instead of checkbox
    if path and path[-1] == "is_reused":
        key = key_for(*path, ns, "is_reused_select")
        current = "yes" if _coerce_to_bool(value) else "no"
        selected = st.selectbox(
            label,
            options=["no", "yes"],
            index=0 if current == "no" else 1,
            key=key,
            help="Select 'yes' if this dataset reuses existing data",
        )
        return selected == "yes"

    if _is_boolean_schema(path):
        keyb = key_for(*path, ns, "bool")
        return st.checkbox(label, value=_coerce_to_bool(value), key=keyb)

    if _is_format_schema(path, "date"):
        base_key = key_for(*path, ns, "date")
        enable_key = key_for(*path, ns, "date_enabled")
        pending_key = key_for(*path, ns, "date_pending")
        set_key = key_for(*path, ns, "date_set_btn")
        clear_key = key_for(*path, ns, "date_clear_btn")

        existing = _parse_iso_date(value)
        if enable_key not in st.session_state:
            st.session_state[enable_key] = bool(existing)
        enabled = bool(st.session_state[enable_key])

        c1, c2 = st.columns([4, 1])
        with c2:
            st.markdown("<div style='height:0.15rem'></div>", unsafe_allow_html=True)
            if enabled:
                has_date_now = (base_key in st.session_state) or bool(existing)
                if st.button("Clear", key=clear_key, disabled=not has_date_now):
                    st.session_state.pop(base_key, None)
                    st.session_state[enable_key] = False
                    enabled = False
            else:
                if st.button("Set date", key=set_key):
                    st.session_state[enable_key] = True
                    st.session_state[pending_key] = True
                    enabled = True
        with c1:
            seed_today = bool(st.session_state.pop(pending_key, False))
            cur = (
                date.today()
                if (seed_today and not existing)
                else (st.session_state.get(base_key) or existing or date.today())
            )
            picked = st.date_input(label, value=cur, key=base_key, disabled=not enabled)
        return "" if not enabled else (picked.isoformat() if isinstance(picked, date) else "")

    mode, options = _enum_info_for_path(path)
    if mode == "single" and options:
        sel_key = key_for(*path, ns, "enum")
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

    key = key_for(*path, ns, "prim")
    if isinstance(value, bool):
        return st.checkbox(label, value=value, key=key)
    if isinstance(value, int):
        txt = st.text_input(label, str(value), key=key)
        try:
            return int(txt) if txt != "" else None
        except Exception:
            return value
    if isinstance(value, float):
        txt = st.text_input(label, str(value), key=key)
        try:
            return float(txt) if txt != "" else None
        except Exception:
            return value
    txt = st.text_input(label, "" if value is None else str(value), key=key)
    return txt


def edit_array(
    arr: list[Any],
    path: tuple,
    title_singular: str,
    removable_items: bool,
    ns: str | None = None,
) -> list[Any]:
    mode, options = _enum_info_for_path(path)
    if mode == "multi" and options:
        label = f"{path[-1] if path else title_singular} (choose any)"
        wkey = key_for(*path, ns, "enum_multi")
        current = [x for x in arr if isinstance(x, str) and x in options]
        selected = st.multiselect(
            label,
            options,
            default=current,
            key=wkey,
            format_func=lambda opt: _enum_label_for(path, opt),
        )
        return selected

    if _looks_like_string_list(arr, path):
        label = f"{path[-1] if path else title_singular} (one per line; saved as array)"
        key = key_for(*path, ns, "textlist")
        initial = "\n".join(x for x in arr if isinstance(x, str))
        txt = st.text_area(label, initial, key=key)
        lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]
        return lines

    if len(arr) == 1 and isinstance(arr[0], dict):
        label = path[-1] if path else title_singular
        st.caption(f"{label} — single entry")
        arr[0] = edit_any(arr[0], path=(*path, 0), ns=ns)
        if removable_items:
            if st.button(f"🗑️ Remove this {title_singular.lower()}", key=key_for(*path, ns, "rm_single")):
                arr.clear()
                st.rerun()
        return arr

    item_to_delete = None
    for i, item in enumerate(list(arr)):
        heading = f"{title_singular} #{i + 1}"
        if isinstance(item, dict):
            for pick in ("title", "name", "identifier"):
                if item.get(pick):
                    heading = f"{title_singular} #{i + 1}: {item[pick]}"
                    break
        with st.expander(heading, expanded=False):
            if item_to_delete != i:
                arr[i] = edit_any(item, path=(*path, i), ns=ns)
            if removable_items:
                if st.button(f"🗑️ Remove this {title_singular.lower()}", key=key_for(*path, i, ns, "rm")):
                    item_to_delete = i

    if item_to_delete is not None:
        del arr[item_to_delete]
        st.rerun()
    return arr


def edit_object(obj: dict[str, Any], path: tuple, allow_remove_keys: bool, ns: str | None = None) -> dict[str, Any]:
    keys = list(obj.keys())
    if _is_dataset_path(path):
        keys = _ensure_dataset_id_before_distribution(keys)

    remove_keys: list[str] = []
    for key in keys:
        val = obj.get(key)

        if path == ("dmp",) and key in ("project", "dataset", "contributor"):
            continue

        if key == "x_dcas" and _is_under_dataset_extension(path):
            _show_readonly_json("x_dcas (read-only)", val, key=key_for(*path, key, ns, "ro"))
            continue

        if key == "extension" and isinstance(val, list):
            with st.expander("extension", expanded=False):
                obj["extension"] = edit_array(val, path=(*path, "extension"), title_singular="Entry", removable_items=True, ns=ns)
            continue

        if isinstance(val, dict):
            if key == "dataset_id" and _is_dataset_path(path):
                obj[key] = _edit_dataset_id_inline(val, path=(*path, key), ns=ns)
                continue
            with st.expander(key, expanded=False):
                obj[key] = edit_any(val, path=(*path, key), ns=ns)

        elif isinstance(val, list):
            if key == "distribution" and _is_dataset_path(path):
                obj[key] = _edit_distribution_inline(val, path=(*path, key), ns=ns)
                continue
            with st.expander(key, expanded=False):
                title = "Distribution" if key == "distribution" else "Item"
                obj[key] = edit_array(val, path=(*path, key), title_singular=title, removable_items=False, ns=ns)

        else:
            obj[key] = edit_primitive(key, val, path=(*path, key), ns=ns)

        if allow_remove_keys and st.button(f"Remove key: {key}", key=key_for(*path, key, ns, "del")):
            remove_keys.append(key)

    for k in remove_keys:
        obj.pop(k, None)
    return obj


def edit_any(value: Any, path: tuple, ns: str | None = None) -> Any:
    if isinstance(value, dict):
        return edit_object(value, path, allow_remove_keys=False, ns=ns)
    if isinstance(value, list):
        return edit_array(value, path, title_singular="Item", removable_items=False, ns=ns)
    return edit_primitive("value", value, path, ns=ns)
