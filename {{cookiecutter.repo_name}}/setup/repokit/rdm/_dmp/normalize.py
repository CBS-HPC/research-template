from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from .config import (
    SCHEMA_URLS,
    DMP_KEY_ORDER,
    DATASET_KEY_ORDER,
    DISTRIBUTION_KEY_ORDER,
    DATASET_ID_KEY_ORDER,
    METADATA_ITEM_KEY_ORDER,
    SEC_PRIV_ITEM_KEY_ORDER,
    TECH_RES_ITEM_KEY_ORDER,
    HOST_KEY_ORDER,
    LICENSE_ITEM_KEY_ORDER,
    DEFAULT_DMP_PATH,
)
from .schema import _resolve_first, _deref, fetch_schema
from .defaults import (
    now_iso_minute,
    dmp_default_templates,
    apply_defaults_in_place,
    ensure_required_by_schema,
    repair_empty_enums,
)
from .extensions import get_extension_payload, set_extension_payload
from .cookiecutter_sync import apply_cookiecutter_meta
from .compat import PROJECT_ROOT
from .paths import data_type_from_path

def ensure_dmp_shape(data: dict[str, Any], schema_url: str) -> dict[str, Any]:
    templates = dmp_default_templates(schema_url=schema_url)
    if isinstance(data.get("dmp"), dict):
        dmp = data["dmp"]
        apply_defaults_in_place(dmp, templates["root"])
        dmp["schema"] = schema_url
        if not isinstance(dmp.get("project"), list):
            dmp["project"] = []
        for ds in dmp.get("dataset", []):
            if isinstance(ds.get("x_dcas"), dict):
                set_extension_payload(ds, "x_dcas", ds.pop("x_dcas"))
        return {"dmp": dmp}
    root = deepcopy(templates["root"])
    return {"dmp": root}

def _ensure_object_fields_from_schema(
    target: dict[str, Any],
    schema: dict[str, Any],
    obj_schema: dict[str, Any],
    prefill: dict[str, Any] | None = None,
    path: str | None = None,
) -> None:
    obj_schema = _deref(schema, obj_schema)
    props = obj_schema.get("properties", {})
    for key, prop_schema in props.items():
        if key not in target:
            # conservative: leave as None if we don't know; defaults module handles requireds.
            typ = _deref(schema, prop_schema).get("type")
            if typ == "object":
                target[key] = {}
            elif typ == "array":
                target[key] = []
            elif typ == "integer":
                target[key] = 0
            elif typ == "number":
                target[key] = 0.0
            elif typ == "boolean":
                target[key] = False
            else:
                target[key] = ""
    for key in obj_schema.get("required", []):
        if key not in target:
            target[key] = ""
    if prefill:
        for k, v in prefill.items():
            target.setdefault(k, v)

def normalize_root_in_place(data: dict[str, Any], schema: dict[str, Any] | None, schema_url: str) -> None:
    templates = dmp_default_templates(schema_url=schema_url)
    dmp = data.setdefault("dmp", {})
    apply_defaults_in_place(dmp, templates["root"])
    dmp["schema"] = schema_url

    projects: list[dict[str, Any]] = dmp.setdefault("project", [])
    if not isinstance(projects, list):
        projects = []
        dmp["project"] = projects
    if not projects:
        prj = deepcopy(templates["project"])
        prj["title"] = dmp.get("title") or "Project"
        projects.append(prj)

    if schema:
        proj_schema = _resolve_first(schema, ["#/definitions/Project", "#/definitions/project"]) or None
        if proj_schema:
            for prj in projects:
                _ensure_object_fields_from_schema(prj, schema, proj_schema, path="dmp.project[]")
                apply_defaults_in_place(prj, templates["project"])
        else:
            for prj in projects:
                apply_defaults_in_place(prj, templates["project"])
    else:
        for prj in projects:
            apply_defaults_in_place(prj, templates["project"])

def normalize_datasets_in_place(data: dict[str, Any], schema: dict[str, Any] | None, schema_url: str) -> None:
    templates = dmp_default_templates(schema_url=schema_url)
    dmp = data.setdefault("dmp", {})
    datasets: list[dict[str, Any]] = dmp.setdefault("dataset", [])
    if not isinstance(datasets, list):
        dmp["dataset"] = datasets = []

    ds_schema = dist_schema = None
    if schema:
        ds_schema = _resolve_first(schema, ["#/definitions/Dataset", "#/definitions/dataset"]) or None
        dist_schema = _resolve_first(schema, ["#/definitions/Distribution", "#/definitions/distribution"]) or None

    for ds in datasets:
        if isinstance(ds.get("x_dcas"), dict):
            set_extension_payload(ds, "x_dcas", ds.pop("x_dcas"))

        apply_defaults_in_place(ds, templates["dataset"])
        if ds_schema:
            _ensure_object_fields_from_schema(ds, schema, ds_schema, path="dmp.dataset[]")

        ds.setdefault("distribution", [])
        if not ds["distribution"]:
            dist = deepcopy(templates["distribution"])
            ds["distribution"].append(dist)

        for dist in ds["distribution"]:
            apply_defaults_in_place(dist, templates["distribution"])
            if dist_schema:
                _ensure_object_fields_from_schema(dist, schema, dist_schema, path="dmp.dataset[].distribution[]")

        x = get_extension_payload(ds, "x_dcas") or {}
        apply_defaults_in_place(x, templates["x_dcas"])
        if not x.get("data_type"):
            hint = (ds.get("distribution") or [{}])[0].get("access_url") or ""
            x["data_type"] = data_type_from_path(hint) if isinstance(hint, str) else "Uncategorised"
        set_extension_payload(ds, "x_dcas", x)

def _order_dict(d: dict[str, Any], order: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k in order:
        if k in d:
            out[k] = d[k]
    for k, v in d.items():
        if k not in out:
            out[k] = v
    return out

def reorder_dmp_keys(data: dict[str, Any]) -> dict[str, Any]:
    dmp = data.get("dmp", {})
    ordered_root: dict[str, Any] = _order_dict(dmp, DMP_KEY_ORDER)

    ds_list = ordered_root.get("dataset", [])
    new_ds_list: list[dict[str, Any]] = []
    if isinstance(ds_list, list):
        for ds in ds_list:
            if not isinstance(ds, dict):
                new_ds_list.append(ds)
                continue
            ds2 = _order_dict(ds, DATASET_KEY_ORDER)
            if isinstance(ds2.get("dataset_id"), dict):
                ds2["dataset_id"] = _order_dict(ds2["dataset_id"], DATASET_ID_KEY_ORDER)
            if isinstance(ds2.get("metadata"), list):
                ds2["metadata"] = [
                    _order_dict(m, METADATA_ITEM_KEY_ORDER) if isinstance(m, dict) else m
                    for m in ds2["metadata"]
                ]
            if isinstance(ds2.get("security_and_privacy"), list):
                ds2["security_and_privacy"] = [
                    _order_dict(x, SEC_PRIV_ITEM_KEY_ORDER) if isinstance(x, dict) else x
                    for x in ds2["security_and_privacy"]
                ]
            if isinstance(ds2.get("technical_resource"), list):
                ds2["technical_resource"] = [
                    _order_dict(x, TECH_RES_ITEM_KEY_ORDER) if isinstance(x, dict) else x
                    for x in ds2["technical_resource"]
                ]
            if isinstance(ds2.get("distribution"), list):
                new_dists: list[dict[str, Any]] = []
                for dist in ds2["distribution"]:
                    if not isinstance(dist, dict):
                        new_dists.append(dist)
                        continue
                    dist2 = _order_dict(dist, DISTRIBUTION_KEY_ORDER)
                    if isinstance(dist2.get("host"), dict):
                        dist2["host"] = _order_dict(dist2["host"], HOST_KEY_ORDER)
                    if isinstance(dist2.get("license"), list):
                        dist2["license"] = [
                            _order_dict(lic, LICENSE_ITEM_KEY_ORDER) if isinstance(lic, dict) else lic
                            for lic in dist2["license"]
                        ]
                    new_dists.append(dist2)
                ds2["distribution"] = new_dists
            new_ds_list.append(ds2)

    ordered_root["dataset"] = new_ds_list
    return {"dmp": ordered_root}

def create_or_update_dmp_from_schema(
    dmp_path: Path = DEFAULT_DMP_PATH,
    schema_version: str = "1.2",
    overwrite_cookie_meta_on_create: bool = True,
) -> Path:
    """Create or normalize a DMP JSON file using the selected maDMP schema.

    - Creates a fresh scaffold when `dmp_path` does not exist.
    - Otherwise loads existing JSON and normalizes root/project/datasets while preserving values.
    - Enforces `dmp.schema` to the canonical GitHub *tree* URL for the selected schema version.
    - Ensures required fields based on the schema and repairs empty enums.
    - Reorders keys for stable diffs.
    """
    from .config import SCHEMA_DOWNLOAD_URLS, SCHEMA_CACHE_FILES
    from .io import load_json, save_json

    schema_url = SCHEMA_URLS[schema_version]
    schema = fetch_schema(
        schema_url=SCHEMA_DOWNLOAD_URLS[schema_version],
        cache_path=SCHEMA_CACHE_FILES[schema_version],
        force=False,
    )

    if not dmp_path.exists():
        shaped = ensure_dmp_shape({}, schema_url=schema_url)
        apply_cookiecutter_meta(
            project_root=PROJECT_ROOT,
            data=shaped,
            schema_url=schema_url,
            overwrite=overwrite_cookie_meta_on_create,
        )
        normalize_root_in_place(shaped, schema=schema, schema_url=schema_url)
        normalize_datasets_in_place(shaped, schema=schema, schema_url=schema_url)

        ensure_required_by_schema(shaped, schema)
        repair_empty_enums(
            shaped.get("dmp", {}),
            schema,
            schema.get("properties", {}).get("dmp", {}),
            path="dmp",
        )

        shaped = reorder_dmp_keys(shaped)
        save_json(dmp_path, shaped)
        return dmp_path

    data = load_json(dmp_path)
    data = ensure_dmp_shape(data, schema_url=schema_url)
    normalize_root_in_place(data, schema=schema, schema_url=schema_url)
    normalize_datasets_in_place(data, schema=schema, schema_url=schema_url)
    apply_cookiecutter_meta(project_root=PROJECT_ROOT, data=data, schema_url=schema_url, overwrite=False)

    data["dmp"]["schema"] = schema_url
    data["dmp"]["modified"] = now_iso_minute()

    ensure_required_by_schema(data, schema)
    repair_empty_enums(
        data.get("dmp", {}),
        schema,
        schema.get("properties", {}).get("dmp", {}),
        path="dmp",
    )

    data = reorder_dmp_keys(data)
    save_json(dmp_path, data)
    return dmp_path
