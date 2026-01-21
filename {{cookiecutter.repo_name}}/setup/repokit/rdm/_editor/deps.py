#!/usr/bin/env python3
"""
Dependency bridge for the Streamlit RDA-DMP JSON editor.

This module centralizes "robust imports" so the editor can run:
- as part of a package (e.g. repokit.rdm.editor)
- or directly (e.g. streamlit run ...)

It re-exports the names used by the editor submodules.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import requests
import streamlit as st

# --- Robust imports whether run as a package (CLI) or directly via `streamlit run` ---
try:
    from ...common import load_from_env, save_to_env, PROJECT_ROOT, write_toml
    from ..dataverse import PublishError, streamlit_publish_to_dataverse
    from ..dataset import dataset_path_update, main as dataset_main
    from ..dmp import (
        DEFAULT_DMP_PATH,
        DK_UNI_MAP,
        EXTRA_ENUMS,
        LICENSE_LINKS,
        SCHEMA_URLS,
        SCHEMA_VERSION,
        dmp_default_templates,
        ensure_dmp_shape,
        ensure_required_by_schema,
        fetch_schema,
        normalize_datasets_in_place,
        normalize_root_in_place,
        now_iso_minute,
        reorder_dmp_keys,
        repair_empty_enums,
        today_iso,
        update_cookiecutter_from_dmp,
        load_default_dataset_path,
        JSON_FILENAME,
        TOOL_NAME,
        TOML_PATH,
    )
    from ..zenodo import streamlit_publish_to_zenodo
except ImportError:
    # Fallback: assume running from repo root where "setup/repokit" is importable
    pkg_root = Path(__file__).resolve().parent.parent.parent / "setup"
    sys.path.insert(0, str(pkg_root))

    from repokit.common import load_from_env, save_to_env, PROJECT_ROOT, write_toml
    from repokit.rdm.dataverse import PublishError, streamlit_publish_to_dataverse
    from repokit.rdm.dataset import dataset_path_update, main as dataset_main
    from repokit.rdm.dmp import (
        DEFAULT_DMP_PATH,
        DK_UNI_MAP,
        EXTRA_ENUMS,
        LICENSE_LINKS,
        SCHEMA_URLS,
        SCHEMA_VERSION,
        dmp_default_templates,
        ensure_dmp_shape,
        ensure_required_by_schema,
        fetch_schema,
        normalize_datasets_in_place,
        normalize_root_in_place,
        now_iso_minute,
        reorder_dmp_keys,
        repair_empty_enums,
        today_iso,
        update_cookiecutter_from_dmp,
        load_default_dataset_path,
        JSON_FILENAME,
        TOOL_NAME,
        TOML_PATH,
    )
    from repokit.rdm.zenodo import streamlit_publish_to_zenodo

# Default dataset parent path (used by datasets UI)
_, DATA_PARENT_PATH = load_default_dataset_path()
