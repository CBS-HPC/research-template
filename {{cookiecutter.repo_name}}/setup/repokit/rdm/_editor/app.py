#!/usr/bin/env python3
"""
Streamlit RDA-DMP JSON editor (module form).

Entry points:
- main(): the Streamlit app
- cli():  helper for `python -m editor ...` style launches
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import streamlit as st
from streamlit.web.cli import main as st_main

from .autosave import autosave_if_changed, schema_fixups_in_place
from .deps import (
    DEFAULT_DMP_PATH,
    SCHEMA_URLS,
    SCHEMA_VERSION,
    ensure_dmp_shape,
    now_iso_minute,
    reorder_dmp_keys,
    update_cookiecutter_from_dmp,
)
from .publish_sidebar import render_token_controls
from .sections import draw_datasets_section, draw_projects_section, draw_root_section
from .schema_editors import safe_fetch_schema


def find_default_dmp_path(start: Path | None = None) -> Path:
    start = start or Path(__file__).resolve().parent
    candidates = ["dmp.json"]
    for base in [start, *start.parents]:
        for name in candidates:
            p = base / name
            if p.exists():
                return p
    return Path("./dmp.json") if not Path(DEFAULT_DMP_PATH).exists() else Path(DEFAULT_DMP_PATH)


def _ensure_data_initialized(default_path: Path) -> None:
    st.session_state.setdefault("__loaded_from__", "")
    st.session_state.setdefault("__last_upload_hash__", None)
    st.session_state.setdefault("__load_message__", "")
    st.session_state.setdefault("save_path", str(default_path))

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
    st.session_state["save_path"] = str(default_path)


def main() -> None:
    st.set_page_config(page_title=f"RDA-DMP {SCHEMA_VERSION} JSON Editor", layout="wide")
    st.title(f"RDA-DMP {SCHEMA_VERSION} JSON Editor")

    if st.session_state.get("__autosave_feedback__"):
        st.caption(st.session_state["__autosave_feedback__"])

    st.session_state.setdefault("__loaded_from__", "")
    st.session_state.setdefault("__load_message__", "")
    st.session_state.setdefault("__last_upload_hash__", None)
    st.session_state.setdefault("__uploader_ver__", 0)
    st.session_state.setdefault("save_path", "")

    schema_now = safe_fetch_schema()
    default_path = find_default_dmp_path()

    _ensure_data_initialized(default_path)

    render_token_controls()

    if st.session_state.get("__load_message__"):
        st.info(st.session_state["__load_message__"])

    def _current_ordered_output() -> dict[str, Any]:
        st.session_state["data"]["dmp"]["modified"] = now_iso_minute()
        return reorder_dmp_keys(schema_fixups_in_place(deepcopy(st.session_state["data"])))

    working_folder: Path = (
        Path(st.session_state["save_path"]).resolve().parent
        if st.session_state.get("save_path")
        else default_path.parent
    )

    with st.sidebar:
        st.header("Load / Save")
        st.caption(f"Schema: {'✅ loaded' if schema_now else '⚠️ unavailable (fallbacks)'}")

        uploader_key = f"open_json_uploader_{st.session_state['__uploader_ver__']}"
        uploaded = st.file_uploader(
            "Open JSON",
            type=["json"],
            help=f"Uploads are saved to: {working_folder.resolve()}",
            key=uploader_key,
        )

        if uploaded is not None:
            payload = uploaded.getvalue()
            h = hashlib.sha256(payload).hexdigest()
            if st.session_state.get("__last_upload_hash__") != h:
                try:
                    working_folder.mkdir(parents=True, exist_ok=True)
                    dst_path = (working_folder / uploaded.name).resolve()
                    dst_path.write_bytes(payload)

                    data = json.loads(payload.decode("utf-8"))
                    st.session_state["data"] = ensure_dmp_shape(data)
                    st.session_state["__last_upload_hash__"] = h
                    st.session_state["__loaded_from__"] = str(dst_path)
                    st.session_state["__load_message__"] = f"✅ Loaded DMP from {dst_path}"
                    st.session_state["save_path"] = str(dst_path)
                    st.session_state.pop("ds_selected", None)
                    st.session_state.pop("__autosave_last_hash__", None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to load uploaded JSON: {e}")

        elif st.session_state.get("__last_upload_hash__"):
            st.session_state["__last_upload_hash__"] = None
            try:
                if default_path.exists():
                    with default_path.open("r", encoding="utf-8") as f:
                        st.session_state["data"] = ensure_dmp_shape(json.load(f))
                    st.session_state["__loaded_from__"] = str(default_path.resolve())
                    st.session_state["__load_message__"] = f"✅ Loaded default DMP from {default_path.resolve()}"
                    st.session_state["save_path"] = str(default_path.resolve())
                else:
                    new_path = (working_folder / "new_dmp.json").resolve()
                    st.session_state["data"] = ensure_dmp_shape({})
                    st.session_state["__loaded_from__"] = "new"
                    st.session_state["__load_message__"] = f"⚠️ Default DMP not found. Started a new DMP (will save to {new_path})"
                    st.session_state["save_path"] = str(new_path)
                st.session_state.pop("ds_selected", None)
                st.session_state.pop("__autosave_last_hash__", None)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to reload default DMP: {e}")

        if st.button("➕ Create New DMP"):
            st.session_state["data"] = ensure_dmp_shape({})
            new_path = (working_folder / "new_dmp.json").resolve()
            st.session_state["__loaded_from__"] = "new"
            st.session_state["__load_message__"] = f"✅ Started a new DMP (will save to {new_path})"
            st.session_state["save_path"] = str(new_path)
            st.session_state["__last_upload_hash__"] = None
            st.session_state.pop("ds_selected", None)
            st.session_state["__uploader_ver__"] += 1
            st.session_state.pop("__autosave_last_hash__", None)
            st.rerun()

        out_for_dl = _current_ordered_output()

        download_clicked = st.download_button(
            "⬇️ Download JSON",
            data=json.dumps(out_for_dl, indent=4, ensure_ascii=False).encode("utf-8"),
            file_name=Path(st.session_state["save_path"]).name or "dmp.json",
            mime="application/json",
            key="download",
        )

        if download_clicked:
            try:
                save_path = Path(st.session_state["save_path"]).resolve()
                save_path.write_text(json.dumps(out_for_dl, indent=4, ensure_ascii=False), encoding="utf-8")
                update_cookiecutter_from_dmp(dmp_path=save_path)
                st.caption("✅ cookiecutter.json updated from downloaded DMP")
            except Exception as e:
                st.warning(f"cookiecutter.json could not be updated: {e}")

    data = ensure_dmp_shape(st.session_state["data"])
    dmp_root = data["dmp"]

    draw_root_section(dmp_root, schema_url=SCHEMA_URLS[SCHEMA_VERSION])
    draw_projects_section(dmp_root)
    draw_datasets_section(dmp_root)

    autosave_if_changed()


def cli() -> None:
    app_path = Path(__file__).resolve()
    ssh_mode = len(sys.argv) > 1 and sys.argv[1] == "ssh"
    if ssh_mode:
        sys.argv.pop(1)
        app_port = int(os.environ.get("DMP_PORT", "8501"))
        cmd = f"ssh -N -L {app_port}:localhost:{app_port} example@host.dk -p PORT (The host and port you have connected)"
        print("\n=== SSH port forwarding ===")
        print("Run this on your LOCAL machine, then open the URL below:")
        print(f"  {cmd}\n")
        sys.argv = [
            "streamlit",
            "run",
            str(app_path),
            "--server.headless",
            "true",
            "--server.address",
            "localhost",
            "--server.port",
            str(app_port),
            *sys.argv[1:],
        ]
    else:
        sys.argv = ["streamlit", "run", str(app_path), *sys.argv[1:]]
    sys.exit(st_main())


if __name__ == "__main__":
    main()
