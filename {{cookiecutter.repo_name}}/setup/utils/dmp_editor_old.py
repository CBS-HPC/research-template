import sys
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# --- Robust imports whether run as a package (CLI) or as a bare script (streamlit run) ---
try:
    from .general_tools import package_installer
    from .dmp_tools import *
except ImportError:
    pkg_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(pkg_root))
    from utils.general_tools import package_installer
    from utils.dmp_tools import *

package_installer(required_libraries=["streamlit"])

import streamlit as st
from streamlit.web.cli import main as st_main

# ──────────────────────────────────────────────────────────────────────────────
# Keys & simple detectors
# ──────────────────────────────────────────────────────────────────────────────

def _key_for(*parts: Any) -> str:
    return "|".join(str(p) for p in parts if p is not None)

STRING_LIST_HINTS = {"data_quality_assurance", "keyword", "format", "pid_system", "role"}

def _looks_like_string_list(arr: List[Any], path: tuple) -> bool:
    if arr and all(isinstance(x, str) for x in arr):
        return True
    return (not arr) and bool(path) and (path[-1] in STRING_LIST_HINTS)

def _is_dataset_root_path(path: tuple) -> bool:
    return len(path) >= 3 and path[0] == "dmp" and path[1] == "dataset" and isinstance(path[2], int)

def _is_bool_field(path: tuple) -> bool:
    return bool(path) and path[-1] == "is_reused"

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

# ──────────────────────────────────────────────────────────────────────────────
# Schema navigation (runtime; uses fetch_schema() provided in dmp_tools)
# ──────────────────────────────────────────────────────────────────────────────

def _schema_node_for_path(path: tuple) -> Optional[Dict[str, Any]]:
    schema = fetch_schema()
    if not schema:
        return None
    node = schema
    for comp in path:
        if isinstance(comp, str):
            props = node.get("properties")
            if isinstance(props, dict) and comp in props:
                node = props[comp]
            else:
                if node.get("type") == "array" and isinstance(node.get("items"), dict):
                    node = node["items"]
                    props = node.get("properties")
                    if isinstance(props, dict) and comp in props:
                        node = props[comp]
                    else:
                        return None
                else:
                    return None
        else:
            if node.get("type") == "array" and isinstance(node.get("items"), dict):
                node = node["items"]
            else:
                return None
    return node

def _enum_info_for_path(path: tuple) -> Tuple[Optional[str], List[str]]:
    node = _schema_node_for_path(path)
    if not node:
        return (None, [])
    if isinstance(node.get("enum"), list) and node.get("type") == "string":
        return ("single", list(node["enum"]))
    if node.get("type") == "array":
        it = node.get("items")
        if isinstance(it, dict) and isinstance(it.get("enum"), list) and it.get("type") == "string":
            return ("multi", list(it["enum"]))
    return (None, [])

# ──────────────────────────────────────────────────────────────────────────────
# Generic editors (schema-aware)
# ──────────────────────────────────────────────────────────────────────────────

def edit_primitive(label: str, value: Any, path: tuple, ns: Optional[str] = None) -> Any:
    # Force boolean checkbox for specific fields
    if _is_bool_field(path):
        keyb = _key_for(*path, ns, "bool")
        return st.checkbox(label, value=_coerce_to_bool(value), key=keyb)

    # Enum-backed single value -> selectbox with all acceptable inputs
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
            default_index = options_ui.index(value) if value in options_ui else 0
        selected = st.selectbox(label, options_ui, index=default_index, key=sel_key)
        return value if (custom_label and selected == custom_label) else selected

    # Non-enum primitives
    key = _key_for(*path, ns, "prim")
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
    return None if txt == "" else txt

def edit_array(
    arr: List[Any],
    path: tuple,
    title_singular: str,
    removable_items: bool,
    ns: Optional[str] = None,
) -> List[Any]:
    # Array of enum'ed strings -> multiselect with all allowed values
    mode, options = _enum_info_for_path(path)
    if mode == "multi" and options:
        label = f"{path[-1] if path else title_singular} (choose any)"
        wkey = _key_for(*path, ns, "enum_multi")
        current = [x for x in arr if isinstance(x, str) and x in options]
        selected = st.multiselect(label, options, default=current, key=wkey)
        return selected

    # Plain list[str] -> one-per-line textarea
    if _looks_like_string_list(arr, path):
        label = f"{path[-1] if path else title_singular} (one per line; saved as array)"
        key = _key_for(*path, ns, "textlist")
        initial = "\n".join(x for x in arr if isinstance(x, str))
        txt = st.text_area(label, initial, key=key)
        lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]
        return lines

    # Default UI for arrays of dicts/complex types
    to_delete: List[int] = []
    for i, item in enumerate(list(arr)):
        heading = f"{title_singular} #{i+1}"
        if isinstance(item, dict):
            for pick in ("title", "name", "identifier"):
                if item.get(pick):
                    heading = f"{title_singular} #{i+1}: {item[pick]}"
                    break
        with st.expander(heading, expanded=False):
            arr[i] = edit_any(item, path=(*path, i), ns=ns)
            if removable_items and st.button(
                f"Remove this {title_singular.lower()}",
                key=_key_for(*path, i, ns, "rm"),
            ):
                to_delete.append(i)
    for i in reversed(to_delete):
        del arr[i]
    return arr

def _render_extension_read_only(ext: List[Any], path: tuple, ns: Optional[str] = None) -> None:
    st.markdown("**extension (read-only)**")
    for idx, item in enumerate(ext):
        if isinstance(item, dict) and len(item) == 1:
            k = next(iter(item))
            with st.expander(k, expanded=False):
                st.json(item[k])
        else:
            with st.expander(f"extension[{idx}]", expanded=False):
                st.json(item)

def edit_extension(obj: Dict[str, Any], path: tuple, ns: Optional[str] = None) -> None:
    ext: List[Any] = obj.setdefault("extension", [])
    st.markdown("**Extension**")
    with st.expander("Add extension entry", expanded=False):
        new_key = st.text_input("Extension key", key=_key_for(*path, ns, "ext", "new"))
        if st.button("Add", key=_key_for(*path, ns, "ext", "add")):
            if new_key and not any(isinstance(it, dict) and new_key in it for it in ext):
                ext.append({new_key: {}})
    to_delete: List[int] = []
    for idx, item in enumerate(ext):
        if isinstance(item, dict) and len(item) == 1:
            k = next(iter(item))
            with st.expander(k, expanded=False):
                inner = item[k]
                edit_object(inner, path=(*path, "extension", idx, k), ns=ns, allow_remove_keys=False)
                item[k] = inner
                if st.button("Remove this extension entry", key=_key_for(*path, ns, "ext", idx, "rm")):
                    to_delete.append(idx)
        else:
            with st.expander(f"extension[{idx}]", expanded=False):
                ext[idx] = edit_any(item, path=(*path, "extension", idx), ns=ns)
                if st.button("Remove this extension entry", key=_key_for(*path, ns, "ext", idx, "rm")):
                    to_delete.append(idx)
    for i in reversed(to_delete):
        del ext[i]
    obj["extension"] = ext

def edit_object(
    obj: Dict[str, Any],
    path: tuple,
    allow_remove_keys: bool,
    ns: Optional[str] = None,
) -> Dict[str, Any]:
    keys = list(obj.keys())
    remove_keys: List[str] = []
    for key in keys:
        val = obj.get(key)

        # Keep Projects/Datasets out of the root object editor
        if path == ("dmp",) and key in ("project", "dataset"):
            continue

        # Special-case: dataset-level extension is read-only
        if key == "extension" and isinstance(val, list):
            if _is_dataset_root_path(path):
                with st.expander("extension", expanded=False):
                    _render_extension_read_only(val, path=(*path, "extension"), ns=ns)
                continue
            else:
                with st.expander("extension", expanded=False):
                    edit_extension(obj, path=(*path,), ns=ns)
                continue

        if isinstance(val, dict):
            with st.expander(key, expanded=False):
                obj[key] = edit_any(val, path=(*path, key), ns=ns)

        elif isinstance(val, list):
            # Prefer enum-driven UI if schema says this is an array-of-enum
            mode, options = _enum_info_for_path((*path, key))
            if mode == "multi" and options:
                label = f"{key} (choose any)"
                wkey = _key_for(*path, key, ns, "enum_multi")
                current = [x for x in val if isinstance(x, str) and x in options]
                obj[key] = st.multiselect(label, options, default=current, key=wkey)

            elif _looks_like_string_list(val, (*path, key)):
                label = f"{key} (one per line; saved as array)"
                wkey = _key_for(*path, key, ns, "textlist")
                initial = "\n".join(x for x in val if isinstance(x, str))
                txt = st.text_area(label, initial, key=wkey)
                obj[key] = [ln.strip() for ln in txt.splitlines() if ln.strip()]

            # NEW: unwrap arrays that contain exactly one dict (no "Item #1")
            elif len(val) == 1 and isinstance(val[0], dict):
                with st.expander(key, expanded=False):
                    val[0] = edit_any(val[0], path=(*path, key, 0), ns=ns)
                obj[key] = val

            else:
                with st.expander(key, expanded=False):
                    obj[key] = edit_array(
                        val,
                        path=(*path, key),
                        title_singular="Item",
                        removable_items=False,
                        ns=ns,
                    )

        else:
            obj[key] = edit_primitive(key, val, path=(*path, key), ns=ns)

        if allow_remove_keys and st.button(
            f"Remove key: {key}", key=_key_for(*path, key, ns, "del")
        ):
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
    start = start or Path.cwd()
    for base in [start, *start.parents]:
        p = base / "datasets.json"
        if p.exists():
            return p
    return Path(DEFAULT_DMP_PATH)

def draw_root_section(dmp_root: Dict[str, Any]) -> None:
    st.subheader("Root")
    dmp_root.setdefault("schema", dmp_root.get("schema") or RDA_DMP_SCHEMA_URL)
    edit_object(dmp_root, path=("dmp",), allow_remove_keys=False, ns=None)

def draw_projects_section(dmp_root: Dict[str, Any]) -> None:
    st.subheader("Projects")
    projects: List[Dict[str, Any]] = dmp_root.setdefault("project", [])
    cols = st.columns(2)
    with cols[0]:
        if st.button("➕ Add project", key=_key_for("project", "add")):
            projects.append({"title": dmp_root.get("title") or "Project"})
    dmp_root["project"] = edit_array(
        projects, path=("dmp", "project"), title_singular="Project", removable_items=True, ns=None
    )

def _dataset_label(i: int, ds: Dict[str, Any]) -> str:
    t = ds.get("title") or "Dataset"
    return f"Dataset #{i+1}: {t}"

def draw_datasets_section(dmp_root: Dict[str, Any]) -> None:
    st.subheader("Datasets")
    datasets: List[Dict[str, Any]] = dmp_root.setdefault("dataset", [])
    top = st.columns([1, 3])
    with top[0]:
        if st.button("➕ Add dataset", key=_key_for("dataset", "add")):
            datasets.append({
                "title": "Dataset",
                "is_reused": False,
                "distribution": [{"title": "Dataset"}],
                "extension": []
            })
            st.success("Dataset added")
    indices = list(range(len(datasets)))
    for i in indices:
        if i >= len(datasets):
            break
        ds = datasets[i]
        ds.setdefault("is_reused", False)
        header = _dataset_label(i, ds)
        with st.expander(header, expanded=False):
            if st.button("🗑️ Remove this dataset", key=_key_for("dataset", i, "rm")):
                del datasets[i]
                st.stop()
            datasets[i] = edit_any(ds, path=("dmp", "dataset", i), ns="deep")

# ──────────────────────────────────────────────────────────────────────────────
# App
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(page_title="RDA-DMP 1.2 Editor", layout="wide")
    st.title("RDA-DMP 1.2 JSON Editor")

    # Ensure schema is loaded so enum lookups work
    _ = fetch_schema()

    default_path = find_default_dmp_path()
    with st.sidebar:
        st.header("Load / Save")
        path_input = st.text_input("Default file path", str(default_path), key="default_path")
        target_path = Path(path_input)
        uploaded = st.file_uploader("Open JSON (optional)", type=["json"])
        btn_new = st.button("New empty DMP")
        btn_load_disk = st.button("Load from disk")

    if "data" not in st.session_state:
        if default_path.exists():
            try:
                with default_path.open("r", encoding="utf-8") as f:
                    st.session_state["data"] = ensure_dmp_shape(json.load(f))
                st.success(f"Loaded default DMP from {default_path.resolve()}")
            except Exception as e:
                st.session_state["data"] = ensure_dmp_shape({})
                st.warning(f"Failed to load default DMP. Started empty. Error: {e}")
        else:
            st.session_state["data"] = ensure_dmp_shape({})

    if btn_new:
        st.session_state["data"] = ensure_dmp_shape({})
        st.session_state.pop("ds_selected", None)

    if uploaded is not None:
        try:
            data = json.loads(uploaded.getvalue().decode("utf-8"))
            st.session_state["data"] = ensure_dmp_shape(data)
            st.success("Loaded from upload.")
            st.session_state.pop("ds_selected", None)
        except Exception as e:
            st.error(f"Failed to load uploaded JSON: {e}")

    if btn_load_disk:
        try:
            if target_path.exists():
                with target_path.open("r", encoding="utf-8") as f:
                    st.session_state["data"] = ensure_dmp_shape(json.load(f))
                st.success(f"Loaded from {target_path}")
                st.session_state.pop("ds_selected", None)
            else:
                st.warning(f"{target_path} not found, created new structure.")
                st.session_state["data"] = ensure_dmp_shape({})
        except Exception as e:
            st.error(f"Failed to load: {e}")

    data = ensure_dmp_shape(st.session_state["data"])
    dmp_root = data["dmp"]

    draw_root_section(dmp_root)
    draw_projects_section(dmp_root)
    draw_datasets_section(dmp_root)

    st.markdown("---")
    colA, colB, colC = st.columns([1, 1, 2])

    with colA:
        if st.button("Reorder keys & Update modified", key="reorder"):
            data["dmp"]["modified"] = now_iso_minute()
            st.session_state["data"] = reorder_dmp_keys(deepcopy(data))
            st.success("Key order applied.")

    with colB:
        save_to_str = st.text_input("Save to path", str(default_path), key="save_path")
        if st.button("Save to disk", key="save"):
            try:
                # ⏱️ bump modified timestamp on every save
                st.session_state["data"]["dmp"]["modified"] = now_iso_minute()

                out = reorder_dmp_keys(deepcopy(st.session_state["data"]))
                p = Path(save_to_str)
                p.parent.mkdir(parents=True, exist_ok=True)
                with p.open("w", encoding="utf-8") as f:
                    json.dump(out, f, indent=4, ensure_ascii=False)
                st.success(f"Saved to {p.resolve()} (modified={out['dmp'].get('modified')})")
            except Exception as e:
                st.error(f"Failed to save: {e}")


    with colC:
        out = reorder_dmp_keys(deepcopy(st.session_state["data"]))
        st.download_button(
            "⬇️ Download JSON",
            data=json.dumps(out, indent=4, ensure_ascii=False).encode("utf-8"),
            file_name="dmp.json",
            mime="application/json",
            key="download",
        )

def cli() -> None:
    app_path = Path(__file__).resolve()
    sys.argv = ["streamlit", "run", str(app_path), *sys.argv[1:]]
    sys.exit(st_main())

if __name__ == "__main__":
    main()
