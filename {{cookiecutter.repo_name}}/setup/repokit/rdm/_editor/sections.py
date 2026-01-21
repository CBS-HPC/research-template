from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import streamlit as st

from .autosave import autosave_if_changed
from .deps import (
    DATA_PARENT_PATH,
    DEFAULT_DMP_PATH,
    JSON_FILENAME,
    PROJECT_ROOT,
    TOML_PATH,
    TOOL_NAME,
    dmp_default_templates,
    ensure_dmp_shape,
    streamlit_publish_to_dataverse,
    streamlit_publish_to_zenodo,
    write_toml,
    dataset_main,
    dataset_path_update,
    PublishError,
)
from .file_dialog import browse_for_directory
from .publish_sidebar import (
    get_dataverse_config,
    get_token_from_state,
    get_zenodo_api_base,
    get_zenodo_community,
    guess_dataverse_defaults_from_university,
)
from .schema_editors import edit_any, edit_array, edit_primitive
from .utils import (
    DATAVERSE_SITE_CHOICES,
    enforce_privacy_access,
    ensure_open_has_license,
    has_privacy_flags,
    is_empty_alias,
    is_reused,
    key_for,
    normalize_chosen_path,
    normalize_license_by_access,
)


def reload_dmp_from_disk(
    save_path: Path,
    clear_widget_keys: bool = True,
    reset_autosave_baseline: bool = True,
    force_widget_refresh: bool = False,
    rerun: bool = False,
) -> None:
    try:
        with save_path.open("r", encoding="utf-8") as f:
            reloaded = json.load(f)
        st.session_state["data"] = ensure_dmp_shape(reloaded)
    except Exception as e:
        st.error(f"Failed to reload updated DMP: {e}")
        return

    if clear_widget_keys:
        keys_to_clear = [
            k for k in list(st.session_state.keys())
            if isinstance(k, str) and (k.startswith("dmp|") or k.startswith("deep|"))
        ]
        for k in keys_to_clear:
            del st.session_state[k]

    if reset_autosave_baseline:
        st.session_state.pop("__autosave_last_hash__", None)

    if force_widget_refresh:
        counter = st.session_state.get("__widget_refresh_counter__", 0)
        st.session_state["__widget_refresh_counter__"] = counter + 1

    if rerun:
        st.rerun()


def draw_root_section(dmp_root: dict[str, Any], schema_url: str) -> None:
    st.subheader("Root")
    dmp_root.setdefault("schema", dmp_root.get("schema") or schema_url)
    dmp_root.setdefault(
        "contact",
        dmp_root.get("contact")
        or {"name": "", "mbox": "", "contact_id": {"type": "orcid", "identifier": ""}},
    )

    templates = dmp_default_templates() if "dmp_default_templates" in globals() else {}
    default_contrib = (
        deepcopy(templates.get("contributor"))
        if templates and "contributor" in templates
        else {"name": "", "mbox": "", "contributor_id": {"type": "orcid", "identifier": ""}, "role": []}
    )

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

    add_col, _ = st.columns([1, 6])
    with add_col:
        if st.button("➕ Add contributor", key=key_for("dmp", "contributor", "add", "bottom")):
            contribs = dmp_root.setdefault("contributor", [])
            contribs.append(deepcopy(default_contrib))
            st.rerun()


def draw_projects_section(dmp_root: dict[str, Any]) -> None:
    st.subheader("Projects")
    projects = dmp_root.get("project")
    if not isinstance(projects, list):
        projects = []
        dmp_root["project"] = projects

    cols = st.columns(2)
    templates = dmp_default_templates()
    with cols[0]:
        if st.button("➕ Add project", key=key_for("project", "add")):
            projects.append(templates["project"])
            st.rerun()

    project_to_delete = None
    for i, proj in enumerate(projects):
        title_key = key_for("dmp", "project", i, "title", "prim")
        live_title = st.session_state.get(title_key, proj.get("title") or proj.get("name"))
        header_title = (live_title or proj.get("title") or proj.get("name") or "Project").strip() or "Project"

        with st.expander(f"Project #{i + 1}: {header_title}", expanded=False):
            projects[i] = edit_any(proj, path=("dmp", "project", i), ns=None)

            if st.button("🗑️ Remove this project", key=key_for("dmp", "project", i, "rm")):
                project_to_delete = i

    if project_to_delete is not None:
        del projects[project_to_delete]
        st.rerun()

    dmp_root["project"] = projects


def draw_datasets_section(dmp_root: dict[str, Any]) -> None:
    st.subheader("Datasets")

    widget_version = st.session_state.get("__widget_refresh_counter__", 0)

    datasets = dmp_root.get("dataset")
    if not isinstance(datasets, list):
        datasets = []
        dmp_root["dataset"] = datasets

    top = st.columns([1, 4, 1])
    templates = dmp_default_templates()

    if "__parent_data_path__" not in st.session_state:
        st.session_state["__parent_data_path__"] = str(DATA_PARENT_PATH)

    parent_data_path = st.session_state["__parent_data_path__"]

    with top[0]:
        if st.button("➕ Add dataset", key=key_for("dataset", "add")):
            new_index = len(datasets) + 1
            new_ds = deepcopy(templates["dataset"])
            if isinstance(new_ds, dict):
                title_val = str(new_ds.get("title") or "").strip()
                if not title_val:
                    new_ds["title"] = f"Dataset {new_index}"

            datasets.append(new_ds)
            dmp_root["dataset"] = datasets

            if "data" in st.session_state and isinstance(st.session_state["data"], dict):
                st.session_state["data"].setdefault("dmp", {})
                st.session_state["data"]["dmp"] = dmp_root

            autosave_if_changed(force_write=True)
            st.rerun()

    with top[1]:
        c_label, c_input = st.columns([0.4, 4])
        with c_label:
            st.caption("Parent Data Path")
        with c_input:
            st.text_input(
                "Parent Data Path",
                value=parent_data_path,
                key=f"parent_data_path_display_v{widget_version}",
                disabled=True,
                label_visibility="collapsed",
            )

    with top[2]:
        if st.button("Change Path", key="change_parent_data_path"):
            start_path = parent_data_path or st.session_state.get("__parent_data_path__", str(DATA_PARENT_PATH))
            chosen = browse_for_directory(start_path=start_path, title="Select parent data folder for datasets", dir_only=True)

            if chosen:
                chosen_norm = normalize_chosen_path(chosen)
                st.session_state["__parent_data_path__"] = chosen_norm

                try:
                    autosave_if_changed(force_write=True)

                    save_path_str = st.session_state.get("save_path") or str(DEFAULT_DMP_PATH)
                    save_path = Path(save_path_str).resolve()

                    write_toml(
                        data={"patterns": chosen_norm},
                        folder=str(PROJECT_ROOT),
                        json_filename=JSON_FILENAME,
                        tool_name="datasets",
                        toml_path=TOML_PATH,
                    )

                    try:
                        dataset_main(dmp_path=save_path, do_print=False, git_msg=f"Setting parent dataset path to {chosen_norm}")
                    except Exception as e:
                        st.warning(f"dataset_main failed: {e}")

                    reload_dmp_from_disk(
                        save_path,
                        clear_widget_keys=True,
                        reset_autosave_baseline=True,
                        force_widget_refresh=True,
                        rerun=True,
                    )
                except Exception as e:
                    st.error(f"Failed to save parent data path: {e}")
                else:
                    st.rerun()

    def _is_unknown(v: Any) -> bool:
        s = str(v or "").strip().lower()
        return s in {"unknown", "unkown", ""}

    def _first_access_url(ds: dict) -> str:
        dists = ds.get("distribution") or []
        if not isinstance(dists, list):
            return ""
        for dist in dists:
            if isinstance(dist, dict):
                url = (dist.get("access_url") or "").strip()
                if url:
                    return url
        return ""

    is_reused_changed = False

    for i, ds in enumerate(datasets):
        title_key = f"dmp|dataset|{i}|title|deep|prim_v{widget_version}"
        live_title = st.session_state.get(title_key, ds.get("title"))
        header_title = (live_title or ds.get("title") or "Dataset").strip() or "Dataset"

        with st.expander(f"Dataset #{i + 1}: {header_title}", expanded=False):
            prev_is_reused = is_reused(ds)

            reused_now = is_reused(ds)
            has_unknown_privacy = _is_unknown(ds.get("personal_data")) or _is_unknown(ds.get("sensitive_data"))

            override_key = f"allow_reused_{i}_v{widget_version}"
            allow_override = st.session_state.get(override_key, False)
            if not reused_now and allow_override:
                st.session_state[override_key] = False
                allow_override = False

            zen_disabled = (reused_now and not allow_override) or has_unknown_privacy

            site_choice = st.session_state.get("dataverse_site_choice", "")
            alias_effective = st.session_state.get("dataverse_alias", "") or os.environ.get("DATAVERSE_ALIAS", "") or ""
            if site_choice != "other" and is_empty_alias(alias_effective):
                _gb, _ga = guess_dataverse_defaults_from_university(st.session_state.get("data"))
                if _ga:
                    alias_effective = _ga

            alias_missing = is_empty_alias(alias_effective)
            dv_disabled = (reused_now and not allow_override) or has_unknown_privacy or alias_missing

            cols = st.columns([1, 1, 1, 2, 4])

            with cols[0]:
                if st.button("🗑️ Remove this dataset", key=f"rm_ds_{i}_v{widget_version}"):
                    del datasets[i]
                    dmp_root["dataset"] = datasets
                    if "data" in st.session_state and isinstance(st.session_state["data"], dict):
                        st.session_state["data"].setdefault("dmp", {})
                        st.session_state["data"]["dmp"] = dmp_root
                    st.session_state.pop(override_key, None)
                    autosave_if_changed(force_write=True)
                    st.rerun()

            with cols[1]:
                if st.button("Publish to Zenodo", key=f"pub_zen_{i}_v{widget_version}", disabled=zen_disabled):
                    token = get_token_from_state("zenodo")
                    if not token:
                        st.warning("Please set a Zenodo token in the sidebar and press Save.")
                        st.stop()
                    try:
                        streamlit_publish_to_zenodo(
                            dataset=ds,
                            dmp=st.session_state["data"],
                            token=token,
                            base_url=get_zenodo_api_base(),
                            community=get_zenodo_community(),
                            publish=False,
                            allow_reused=allow_override,
                        )
                    except PublishError as e:
                        st.error(str(e))

            with cols[2]:
                if st.button("Publish to DeiC Dataverse", key=f"pub_dv_{i}_v{widget_version}", disabled=dv_disabled):
                    token = get_token_from_state("dataverse")
                    if not token:
                        st.warning("Please set a Dataverse token in the sidebar and press Save.")
                        st.stop()
                    try:
                        dv_base, dv_alias = get_dataverse_config()
                        if not dv_base:
                            st.warning("Please select a Dataverse base URL in the sidebar and press Save.")
                            st.stop()
                        if is_empty_alias(dv_alias):
                            st.warning("Please enter a Dataverse collection (alias) in the sidebar and press Save.")
                            st.stop()
                        streamlit_publish_to_dataverse(
                            dataset=ds,
                            dmp=st.session_state["data"],
                            token=token,
                            base_url=dv_base,
                            alias=dv_alias,
                            publish=False,
                            release_type="major",
                            allow_reused=allow_override,
                        )
                    except PublishError as e:
                        st.error(str(e))

                if alias_missing:
                    if site_choice == "other":
                        st.caption("⚠️ Enter a Dataverse collection (alias) in the sidebar to enable publishing.")
                    else:
                        st.caption("⚠️ No collection (alias) detected. We'll try to infer it, or set one in the sidebar.")

            with cols[3]:
                st.checkbox(
                    "Override reuse restriction",
                    key=override_key,
                    value=allow_override,
                    disabled=not reused_now,
                    help="Enable publishing even when 'is_reused' is set to 'yes'. Only available when dataset is marked as reused.",
                )

            with cols[4]:
                access_url = _first_access_url(ds)
                btn_label = "Change Data Path" if access_url else "Add Data Path"

                subcol_path, subcol_btn = st.columns([3, 1])

                with subcol_path:
                    st.caption("Data path")
                    preview_key = f"dmp|dataset|{i}|data_path_preview_v{widget_version}"
                    st.text_input("Data path", value=access_url or "", key=preview_key, disabled=True, label_visibility="collapsed")

                with subcol_btn:
                    if st.button(btn_label, key=f"dmp|dataset|{i}|data_path_action_v{widget_version}"):
                        start_path = access_url or st.session_state.get("__parent_data_path__", str(DATA_PARENT_PATH))
                        chosen = browse_for_directory(
                            start_path=start_path,
                            title=f"Select data folder/files for dataset #{i + 1}",
                            dir_only=False,
                        )
                        if chosen:
                            chosen_norm = normalize_chosen_path(chosen)

                            dists = ds.setdefault("distribution", [])
                            if not dists or not isinstance(dists[0], dict):
                                if dists and not isinstance(dists[0], dict):
                                    dists.clear()
                                dists.append({})
                            dists[0]["access_url"] = chosen_norm

                            datasets[i] = ds
                            dmp_root["dataset"] = datasets

                            if "data" in st.session_state and isinstance(st.session_state["data"], dict):
                                st.session_state["data"].setdefault("dmp", {})
                                st.session_state["data"]["dmp"] = dmp_root

                            try:
                                autosave_if_changed(force_write=True)
                                save_path_str = st.session_state.get("save_path") or str(DEFAULT_DMP_PATH)
                                save_path = Path(save_path_str).resolve()

                                try:
                                    dataset_path_update(
                                        data_files=chosen_norm,
                                        dmp_path=save_path,
                                        git_msg=f"Updating dataset #{i + 1} data path to {chosen_norm}",
                                    )
                                except Exception as e:
                                    st.warning(f"dataset_path_update failed: {e}")

                                reload_dmp_from_disk(
                                    save_path,
                                    clear_widget_keys=True,
                                    reset_autosave_baseline=True,
                                    force_widget_refresh=True,
                                    rerun=True,
                                )
                            except Exception as e:
                                st.error(f"Failed to save DMP after updating data path: {e}")

            datasets[i] = edit_any(ds, path=("dmp", "dataset", i), ns=f"deep_v{widget_version}")

            new_is_reused = is_reused(datasets[i])
            if prev_is_reused != new_is_reused:
                is_reused_changed = True

            changed = False
            changed |= enforce_privacy_access(datasets[i])
            changed |= normalize_license_by_access(datasets[i])
            changed |= ensure_open_has_license(datasets[i])

    if is_reused_changed:
        st.rerun()
