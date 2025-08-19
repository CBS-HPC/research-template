import sys
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional
import streamlit as st
from streamlit.web.cli import main as st_main

from .dmp_tools import (
        ensure_dmp_shape,
        reorder_dmp_keys,
        make_dataset_id,
        data_type_from_path,
        now_iso_minute,
        DEFAULT_DMP_PATH,
        RDA_DMP_SCHEMA_URL,
        _get_extension_payload,
        _set_extension_payload,
    )

def find_default_dmp_path(start: Optional[Path] = None) -> Path:
    start = start or Path.cwd()
    candidates = [start] + list(start.parents)
    for base in candidates:
        p = base / "datasets.json"
        if p.exists():
            return p
    return Path(DEFAULT_DMP_PATH)

# ──────────────────────────────────────────────────────────────────────────────
# Local-only UI helpers
# ──────────────────────────────────────────────────────────────────────────────
def editable_text(label: str, value: Optional[str], key: str, help: str | None = None) -> Optional[str]:
    return st.text_input(label, value or "", key=key, help=help) or None

def editable_textarea(label: str, value: Optional[str], key: str) -> Optional[str]:
    return st.text_area(label, value or "", key=key) or None

def editable_select(label: str, value: Optional[str], options: List[str], key: str) -> Optional[str]:
    cur = value if value in options else options[0]
    sel = st.selectbox(label, options, index=options.index(cur), key=key)
    return sel

def editable_list(label: str, values: List[str] | None, key: str, help: str = "Comma-separated") -> List[str]:
    txt = st.text_input(label, ", ".join(values or []), key=key, help=help)
    parts = [p.strip() for p in txt.split(",") if p.strip()]
    return parts

# ──────────────────────────────────────────────────────────────────────────────
# Editors (root / projects / datasets)
# ──────────────────────────────────────────────────────────────────────────────
def draw_root_editor(dmp: Dict[str, Any]) -> None:
    st.subheader("DMP (root)")
    col1, col2 = st.columns(2)
    with col1:
        dmp["title"] = editable_text("Title", dmp.get("title"), "title")
        dmp["language"] = editable_text("Language (ISO 639-3)", dmp.get("language"), "language")
        dmp["created"] = editable_text("Created (ISO8601)", dmp.get("created"), "created")
    with col2:
        dmp["schema"] = editable_text("Schema (fixed)", dmp.get("schema") or RDA_DMP_SCHEMA_URL, "schema")
        dmp["modified"] = editable_text("Modified (ISO8601)", dmp.get("modified"), "modified")

    dmp["description"] = editable_textarea("Description (HTML/plain OK)", dmp.get("description"), "desc")

    dmp["ethical_issues_exist"] = editable_select(
        "Ethical issues exist",
        dmp.get("ethical_issues_exist") or "unknown",
        ["unknown", "yes", "no"],
        key="eth_exist"
    )
    dmp["ethical_issues_description"] = editable_textarea(
        "Ethical issues description", dmp.get("ethical_issues_description"), "eth_desc"
    )
    dmp["ethical_issues_report"] = editable_text(
        "Ethical issues report URL", dmp.get("ethical_issues_report"), "eth_url"
    )

    with st.expander("DMP Identifier"):
        dmp_id = dmp.get("dmp_id") or {}
        dmp_id["type"] = editable_select(
            "Type", dmp_id.get("type") or "url", ["url", "doi", "handle", "other"], "dmpid_type"
        )
        dmp_id["identifier"] = editable_text("Identifier", dmp_id.get("identifier"), "dmpid_id")
        dmp["dmp_id"] = dmp_id

    with st.expander("Contact (person or org)"):
        contact = dmp.get("contact") or {}
        contact["name"] = editable_text("Name", contact.get("name"), "contact_name")
        contact["mbox"] = editable_text("Email", contact.get("mbox"), "contact_email")
        cid = (contact.get("contact_id") or {})
        cid["type"] = editable_select("Contact ID Type", cid.get("type") or "orcid",
                                      ["orcid", "isni", "openid", "other"], "cid_type")
        cid["identifier"] = editable_text("Contact ID", cid.get("identifier"), "cid_id")
        contact["contact_id"] = cid
        dmp["contact"] = contact

    with st.expander("Root Extensions"):
        xui = _get_extension_payload(dmp, "x_ui") or {"hide_fields": []}
        xui["hide_fields"] = editable_list("x_ui.hide_fields", xui.get("hide_fields") or [], "xui_hide")
        _set_extension_payload(dmp, "x_ui", xui)

        xproj = _get_extension_payload(dmp, "x_project") or {}
        xproj_json = st.text_area("x_project (raw JSON)", json.dumps(xproj, indent=2), key="xproj_raw")
        try:
            _set_extension_payload(dmp, "x_project", json.loads(xproj_json))
        except Exception:
            st.warning("x_project JSON invalid; keeping previous value.")

def draw_projects_editor(dmp: Dict[str, Any]) -> None:
    st.subheader("Projects")
    projects: List[Dict[str, Any]] = dmp.setdefault("project", [])
    if st.button("➕ Add Project"):
        projects.append({
            "title": dmp.get("title") or "Project",
            "description": None,
            "start": None,
            "end": None,
            "funding": [],
        })

    for i, pr in enumerate(projects):
        with st.expander(f"Project #{i+1}: {pr.get('title') or 'Untitled'}", expanded=False):
            pr["title"] = editable_text("Title", pr.get("title"), f"pr_title_{i}")
            pr["description"] = editable_textarea("Description", pr.get("description"), f"pr_desc_{i}")
            cols = st.columns(2)
            with cols[0]:
                pr["start"] = editable_text("Start (ISO8601)", pr.get("start"), f"pr_start_{i}")
            with cols[1]:
                pr["end"] = editable_text("End (ISO8601)", pr.get("end"), f"pr_end_{i}")

            pr.setdefault("funding", [])
            if st.button(f"➕ Add Funding to Project #{i+1}", key=f"add_fund_{i}"):
                pr["funding"].append({
                    "name": None,
                    "grant_id": {"type": "other", "identifier": None},
                    "funding_status": "granted",
                    "dmproadmap_funding_opportunity_id": {"type": "other", "identifier": None},
                    "dmproadmap_funded_affiliations": []
                })
            for j, fu in enumerate(pr["funding"]):
                st.markdown(f"**Funding #{j+1}**")
                fu["name"] = editable_text("Name", fu.get("name"), f"fu_name_{i}_{j}")
                gid = fu.get("grant_id") or {}
                gid["type"] = editable_select("Grant ID Type", gid.get("type") or "other",
                                              ["other", "doi", "handle"], f"fu_gid_type_{i}_{j}")
                gid["identifier"] = editable_text("Grant Identifier", gid.get("identifier"),
                                                  f"fu_gid_id_{i}_{j}")
                fu["grant_id"] = gid
                fu["funding_status"] = editable_select("Funding Status",
                                                       fu.get("funding_status") or "granted",
                                                       ["granted", "application", "rejected"],
                                                       f"fu_status_{i}_{j}")
                opp = fu.get("dmproadmap_funding_opportunity_id") or {}
                opp["type"] = editable_select("Opportunity ID Type",
                                              opp.get("type") or "other",
                                              ["other", "url", "doi"], f"fu_opp_type_{i}_{j}")
                opp["identifier"] = editable_text("Opportunity Identifier",
                                                  opp.get("identifier"), f"fu_opp_id_{i}_{j}")
                fu["dmproadmap_funding_opportunity_id"] = opp

def draw_datasets_editor(dmp: Dict[str, Any]) -> None:
    st.subheader("Datasets")
    datasets: List[Dict[str, Any]] = dmp.setdefault("dataset", [])

    if st.button("➕ Add Dataset"):
        datasets.append({
            "title": "Dataset",
            "description": None,
            "issued": now_iso_minute(),
            "modified": None,
            "language": None,
            "keyword": [],
            "type": None,
            "is_reused": None,
            "personal_data": "unknown",
            "sensitive_data": "unknown",
            "preservation_statement": None,
            "data_quality_assurance": [],
            "metadata": [],
            "security_and_privacy": [],
            "technical_resource": [],
            "dataset_id": make_dataset_id("Dataset", None),
            "distribution": [{"title": "Dataset"}],
            "extension": [{"x_dcas": {
                "data_type": "Uncategorised",
                "destination": None,
                "number_of_files": None,
                "total_size_mb": None,
                "file_formats": [],
                "data_files": [],
                "data_size_mb": [],
                "hash": None,
            }}],
        })

    for i, ds in enumerate(datasets):
        with st.expander(f"Dataset #{i+1}: {ds.get('title') or 'Untitled'}", expanded=False):
            cols = st.columns(2)
            ds["title"] = editable_text("Title", ds.get("title"), f"ds_title_{i}")
            ds["description"] = editable_textarea("Description", ds.get("description"), f"ds_desc_{i}")
            with cols[0]:
                ds["issued"] = editable_text("Issued (ISO8601)", ds.get("issued"), f"ds_issued_{i}")
                ds["language"] = editable_text("Language (ISO 639-3)", ds.get("language"), f"ds_lang_{i}")
                ds["type"] = editable_text("Type (COAR/DataCite/common name)", ds.get("type"), f"ds_type_{i}")
            with cols[1]:
                ds["modified"] = editable_text("Modified (ISO8601)", ds.get("modified"), f"ds_mod_{i}")
                ds["is_reused"] = st.selectbox("Is reused?", ["", "true", "false"],
                                               index=["", "true", "false"].index(
                                                   "true" if ds.get("is_reused") is True
                                                   else "false" if ds.get("is_reused") is False else ""
                                               ), key=f"ds_reused_{i}")
                ds["is_reused"] = None if ds["is_reused"] == "" else (ds["is_reused"] == "true")

            pd = st.selectbox("Contains personal data?", ["unknown", "yes", "no"],
                              index=["unknown", "yes", "no"].index(ds.get("personal_data") or "unknown"),
                              key=f"ds_pd_{i}")
            ds["personal_data"] = pd
            sd = st.selectbox("Contains sensitive data?", ["unknown", "yes", "no"],
                              index=["unknown", "yes", "no"].index(ds.get("sensitive_data") or "unknown"),
                              key=f"ds_sd_{i}")
            ds["sensitive_data"] = sd

            ds["keyword"] = editable_list("Keywords", ds.get("keyword"), f"ds_kw_{i}")
            ds["preservation_statement"] = editable_textarea(
                "Preservation statement", ds.get("preservation_statement"), f"ds_ps_{i}"
            )
            ds["data_quality_assurance"] = editable_list(
                "Data quality assurance (list)", ds.get("data_quality_assurance"), f"dqa_{i}"
            )

            # dataset_id
            with st.expander("Dataset ID"):
                did = ds.get("dataset_id") or {}
                did["type"] = st.selectbox("ID Type", ["other", "handle", "doi", "ark", "url"],
                                           index=["other", "handle", "doi", "ark", "url"].index(did.get("type") or "other"),
                                           key=f"dsid_type_{i}")
                did["identifier"] = editable_text("Identifier", did.get("identifier"), f"dsid_id_{i}")
                ds["dataset_id"] = did

            # Distributions
            st.markdown("**Distributions**")
            if st.button(f"➕ Add Distribution to #{i+1}", key=f"dist_add_{i}"):
                ds.setdefault("distribution", [])
                ds["distribution"].append({
                    "title": ds.get("title") or "Dataset",
                    "access_url": None,
                    "download_url": None,
                    "format": [],
                    "byte_size": None,
                    "data_access": "open",
                    "host": {"title": "Project repository"},
                    "available_until": None,
                    "description": None,
                    "license": [],
                })

            for j, dist in enumerate(ds.get("distribution") or []):
                st.markdown(f"Distribution #{j+1}")
                dcols = st.columns(2)
                with dcols[0]:
                    dist["title"] = editable_text("Title", dist.get("title"), f"dist_title_{i}_{j}")
                    dist["access_url"] = editable_text("Access URL", dist.get("access_url"), f"dist_acc_{i}_{j}")
                    dist["download_url"] = editable_text("Download URL", dist.get("download_url"), f"dist_dl_{i}_{j}")
                    dist["format"] = editable_list("Formats (IANA/common)", dist.get("format"), f"dist_fmt_{i}_{j}")
                with dcols[1]:
                    dist["byte_size"] = editable_text("Byte size (int)", str(dist.get("byte_size") or ""), f"dist_bs_{i}_{j}")
                    dist["data_access"] = st.selectbox("Data access", ["open", "shared", "closed"],
                                                       index=["open", "shared", "closed"].index(dist.get("data_access") or "open"),
                                                       key=f"dist_da_{i}_{j}")
                    host = dist.get("host") or {}
                    host["title"] = editable_text("Host title", host.get("title") or "Project repository",
                                                  f"dist_host_{i}_{j}")
                    dist["host"] = host
                lic_txt = st.text_input(
                    "License refs (comma)",
                    ", ".join([l.get("license_ref") for l in (dist.get("license") or []) if l.get("license_ref")]),
                    key=f"dist_lic_{i}_{j}"
                )
                dist["license"] = [{"license_ref": s.strip()} for s in lic_txt.split(",") if s.strip()]

            # x_dcas in dataset.extension
            with st.expander("Extension: x_dcas"):
                x = _get_extension_payload(ds, "x_dcas") or {}
                x["data_type"] = editable_text("data_type", x.get("data_type") or data_type_from_path(""), f"xdt_{i}")
                x["destination"] = editable_text("destination", x.get("destination"), f"xdest_{i}")
                x["number_of_files"] = editable_text("number_of_files", str(x.get("number_of_files") or ""), f"xnof_{i}")
                x["total_size_mb"] = editable_text("total_size_mb", str(x.get("total_size_mb") or ""), f"xtot_{i}")
                x["file_formats"] = editable_list("file_formats (extensions)", x.get("file_formats") or [], f"xff_{i}")
                x["data_files"] = editable_list("data_files (paths)", x.get("data_files") or [], f"xfiles_{i}",
                                                help="Comma-separated paths")
                x["data_size_mb"] = editable_list(
                    "data_size_mb (numbers)",
                    [str(v) for v in (x.get("data_size_mb") or [])],
                    f"xfsz_{i}",
                    help="Comma-separated numbers",
                )
                x["hash"] = editable_text("hash", x.get("hash"), f"xhash_{i}")
                # coerce some ints
                try:
                    x["number_of_files"] = int(x["number_of_files"]) if x.get("number_of_files") not in (None, "",) else None
                except Exception:
                    pass
                try:
                    x["total_size_mb"] = int(x["total_size_mb"]) if x.get("total_size_mb") not in (None, "",) else None
                except Exception:
                    pass
                try:
                    x["data_size_mb"] = [int(v) for v in x.get("data_size_mb") or []]
                except Exception:
                    pass
                _set_extension_payload(ds, "x_dcas", x)

# ──────────────────────────────────────────────────────────────────────────────
# Main app entry
# ──────────────────────────────────────────────────────────────────────────────
def main() -> None:
    st.set_page_config(page_title="RDA-DMP 1.0 Editor", layout="wide")
    st.title("RDA-DMP 1.0 JSON Editor")

    # Determine default path by searching upward for datasets.json
    DEFAULT_PATH = find_default_dmp_path()

    # Sidebar: load/create
    with st.sidebar:
        st.header("Load / Save")
        default_path_str = st.text_input("Default file path", str(DEFAULT_PATH))
        default_path = Path(default_path_str)

        uploaded = st.file_uploader("Open JSON (optional)", type=["json"])
        btn_new = st.button("New empty DMP")
        btn_load_disk = st.button("Load from disk")

    # Initialize session data:
    if "data" not in st.session_state:
        # Try to auto-load datasets.json from project root if present
        if DEFAULT_PATH.exists():
            try:
                with DEFAULT_PATH.open("r", encoding="utf-8") as f:
                    st.session_state["data"] = ensure_dmp_shape(json.load(f))
                st.success(f"Loaded default DMP from {DEFAULT_PATH.resolve()}")
            except Exception as e:
                st.session_state["data"] = ensure_dmp_shape({})
                st.warning(f"Failed to load default DMP. Started empty. Error: {e}")
        else:
            st.session_state["data"] = ensure_dmp_shape({})

    # "New" button supersedes
    if btn_new:
        st.session_state["data"] = ensure_dmp_shape({})

    # Upload overrides
    if uploaded is not None:
        try:
            data = json.loads(uploaded.getvalue().decode("utf-8"))
            st.session_state["data"] = ensure_dmp_shape(data)
            st.success("Loaded from upload.")
        except Exception as e:
            st.error(f"Failed to load uploaded JSON: {e}")

    # Manual load button
    if btn_load_disk:
        try:
            if default_path.exists():
                with default_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                st.session_state["data"] = ensure_dmp_shape(data)
                st.success(f"Loaded from {default_path}")
            else:
                st.warning(f"{default_path} not found, created new structure.")
                st.session_state["data"] = ensure_dmp_shape({})
        except Exception as e:
            st.error(f"Failed to load: {e}")

    # Work copy & harmonize
    data = ensure_dmp_shape(st.session_state["data"])

    # Editors
    draw_root_editor(data["dmp"])
    draw_projects_editor(data["dmp"])
    draw_datasets_editor(data["dmp"])

    # Footer: export/save
    st.markdown("---")
    colA, colB, colC = st.columns([1, 1, 2])

    with colA:
        if st.button("Reorder keys & Update modified"):
            data["dmp"]["modified"] = now_iso_minute()
            st.session_state["data"] = reorder_dmp_keys(deepcopy(data))
            st.success("Key order applied.")

    with colB:
        target_path_str = st.text_input("Save to path", str(DEFAULT_PATH), key="save_path")
        if st.button("Save to disk"):
            try:
                out = reorder_dmp_keys(deepcopy(st.session_state["data"]))
                p = Path(target_path_str)
                p.parent.mkdir(parents=True, exist_ok=True)
                with p.open("w", encoding="utf-8") as f:
                    json.dump(out, f, indent=4, ensure_ascii=False)
                st.success(f"Saved to {p.resolve()}")
            except Exception as e:
                st.error(f"Failed to save: {e}")

    with colC:
        out = reorder_dmp_keys(deepcopy(st.session_state["data"]))
        st.download_button(
            "⬇️ Download JSON",
            data=json.dumps(out, indent=4, ensure_ascii=False).encode("utf-8"),
            file_name="dmp.json",
            mime="application/json",
        )

def cli() -> None:
    """
    Launch the Streamlit editor app as a CLI: `dmp-editor`.
    This wraps `streamlit run <path-to-utils/dmp_editor.py>` and forwards any
    extra CLI args to Streamlit (e.g. --server.port 8502).
    """

    app_path = Path(__file__).resolve()

    # Rebuild argv for Streamlit: ["streamlit", "run", app.py, ...passthrough...]
    sys.argv = ["streamlit", "run", str(app_path), *sys.argv[1:]]
    sys.exit(st_main())


if __name__ == "__main__":
    main()
