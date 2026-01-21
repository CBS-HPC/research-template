from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from .compat import PROJECT_ROOT, read_toml, write_toml, split_multi
from .config import JSON_FILENAME, TOOL_NAME, TOML_PATH, LICENSE_LINKS
from .defaults import apply_defaults_in_place, dmp_default_templates, affiliation_from_email

def _set_contacts(dmp: dict, cookie: dict, overwrite: bool = False):
    authors = split_multi(cookie.get("AUTHORS"))
    emails = split_multi(cookie.get("EMAIL"))
    orcids = split_multi(cookie.get("ORCIDS"))

    name = authors[0] if authors else None
    mbox = emails[0] if emails else None
    orcid = orcids[0] if orcids else None

    if overwrite or ((name or mbox or orcid) and not dmp.get("contact")):
        info: dict[str, Any] = {}
        if name:
            info["name"] = name
        if mbox:
            info["mbox"] = mbox
        if orcid:
            info["contact_id"] = {"type": "orcid", "identifier": orcid}
        if mbox:
            info["affiliation"] = affiliation_from_email(mbox)
        dmp["contact"] = info

    contributors = []
    max_len = max(len(authors), len(emails), len(orcids)) if (authors or emails or orcids) else 0
    for i in range(1, max_len):
        name = authors[i] if i < len(authors) else None
        mbox = emails[i] if i < len(emails) else None
        orcid = orcids[i] if i < len(orcids) else None
        if not (name or mbox or orcid):
            continue
        info: dict[str, Any] = {}
        if name:
            info["name"] = name
        if mbox:
            info["mbox"] = mbox
            info["affiliation"] = affiliation_from_email(mbox)
        if orcid:
            info["contributor_id"] = {"type": "orcid", "identifier": orcid}
        contributors.append(info)

    if overwrite or (contributors and not dmp.get("contributor")):
        if not contributors:
            dmp.pop("contributor", None)
        else:
            dmp["contributor"] = contributors

    return dmp

def apply_cookiecutter_meta(project_root: Path, data: dict[str, Any], schema_url: str, overwrite: bool = False) -> None:
    cookie = (
        read_toml(
            folder=str(project_root),
            json_filename=JSON_FILENAME,
            tool_name=TOOL_NAME,
            toml_path=TOML_PATH,
        )
        or {}
    )

    dmp = data.setdefault("dmp", {})
    templates = dmp_default_templates(schema_url=schema_url)

    apply_defaults_in_place(dmp, templates["root"])

    proj_title = cookie.get("PROJECT_NAME") or cookie.get("REPO_NAME")
    if proj_title:
        dmp["title"] = proj_title if overwrite else (dmp.get("title") or proj_title)

    proj_desc = cookie.get("PROJECT_DESCRIPTION")
    if proj_desc:
        dmp["description"] = proj_desc if overwrite else (dmp.get("description") or proj_desc)

    dmp = _set_contacts(dmp, cookie, overwrite)

    projects: list[dict[str, Any]] = dmp.setdefault("project", [])
    if not projects:
        projects.append(deepcopy(templates["project"]))
    prj0 = projects[0]
    if proj_title and not prj0.get("title"):
        prj0["title"] = proj_title
    if proj_desc and not prj0.get("description"):
        prj0["description"] = proj_desc
    apply_defaults_in_place(prj0, templates["project"])

def _cookie_meta_from_dmp(data: dict[str, Any]) -> dict[str, str]:
    dmp = (data or {}).get("dmp") or {}
    out: dict[str, str] = {}

    title = (dmp.get("title") or "").strip()
    desc = (dmp.get("description") or "").strip()
    if title:
        out["PROJECT_NAME"] = title
        out.setdefault("REPO_NAME", title)
    if desc:
        out["PROJECT_DESCRIPTION"] = desc

    authors: list[str] = []
    emails: list[str] = []
    orcids: list[str] = []

    def _add_person(name: Any, mbox: Any, id_obj: Any, id_key: str) -> None:
        if isinstance(name, str) and name.strip():
            authors.append(name.strip())
        if isinstance(mbox, str) and mbox.strip():
            emails.append(mbox.strip())
        if isinstance(id_obj, dict):
            ident = id_obj.get("identifier")
            id_type = (id_obj.get("type") or "").lower()
            if isinstance(ident, str) and ident.strip():
                if not id_type or id_type == id_key:
                    orcids.append(ident.strip())

    contact = dmp.get("contact") or {}
    _add_person(contact.get("name"), contact.get("mbox"), contact.get("contact_id"), "orcid")

    for c in dmp.get("contributor") or []:
        if not isinstance(c, dict):
            continue
        _add_person(c.get("name"), c.get("mbox"), c.get("contributor_id"), "orcid")

    if authors:
        out["AUTHORS"] = "; ".join(authors)
    if emails:
        out["EMAIL"] = "; ".join(emails)
    if orcids:
        out["ORCIDS"] = "; ".join(orcids)

    license_ref: str | None = None
    for ds in dmp.get("dataset") or []:
        if not isinstance(ds, dict):
            continue
        for dist in ds.get("distribution") or []:
            if not isinstance(dist, dict):
                continue
            for lic in dist.get("license") or []:
                if not isinstance(lic, dict):
                    continue
                ref = (lic.get("license_ref") or "").strip()
                if ref:
                    license_ref = ref
                    break
            if license_ref:
                break
        if license_ref:
            break

    if license_ref:
        inverse = {v: k for k, v in LICENSE_LINKS.items()}
        code = inverse.get(license_ref)
        if code:
            out["DATA_LICENSE"] = code

    return out

def update_cookiecutter_from_dmp(dmp_data: dict[str, Any], overwrite: bool = True) -> None:
    new_fields = _cookie_meta_from_dmp(dmp_data)
    if not new_fields:
        return
    cookie = read_toml(
        folder=str(PROJECT_ROOT),
        json_filename=JSON_FILENAME,
        tool_name=TOOL_NAME,
        toml_path=TOML_PATH,
    ) or {}
    for key, value in new_fields.items():
        if overwrite or not cookie.get(key):
            cookie[key] = value
    write_toml(
        data=cookie,
        folder=str(PROJECT_ROOT),
        json_filename=JSON_FILENAME,
        tool_name=TOOL_NAME,
        toml_path=TOML_PATH,
    )
