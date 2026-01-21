"""RDA maDMP helpers + cookiecutter sync + schema-aware normalization.

Refactored from a monolithic `dmp.py` into a small module tree.
"""

from .config import (
    JSON_FILENAME,
    TOOL_NAME,
    TOML_PATH,
    SCHEMA_DOWNLOAD_URLS,
    SCHEMA_CACHE_FILES,
    SCHEMA_URLS,
    DEFAULT_DMP_PATH,
    LICENSE_LINKS,
    EXTRA_ENUMS,
    LOCAL_FALLBACK_ENUMS,
    DK_UNI_MAP,
    DMP_KEY_ORDER,
    DATASET_KEY_ORDER,
    DISTRIBUTION_KEY_ORDER,
    DATASET_ID_KEY_ORDER,
    METADATA_ITEM_KEY_ORDER,
    SEC_PRIV_ITEM_KEY_ORDER,
    TECH_RES_ITEM_KEY_ORDER,
    HOST_KEY_ORDER,
    LICENSE_ITEM_KEY_ORDER,
)

from .io import load_json, save_json
from .schema import fetch_schema, validate_against_schema, schema_version_from_url
from .paths import load_default_dataset_path, data_type_from_path, norm_rel_urlish, to_bytes_mb
from .defaults import (
    now_iso_minute,
    today_iso,
    dmp_default_templates,
    apply_defaults_in_place,
    ensure_required_by_schema,
    repair_empty_enums,
)
from .extensions import get_extension_payload, set_extension_payload
from .normalize import (
    ensure_dmp_shape,
    normalize_root_in_place,
    normalize_datasets_in_place,
    reorder_dmp_keys,
    create_or_update_dmp_from_schema,
)
from .cookiecutter_sync import (
    update_cookiecutter_from_dmp,
)

__all__ = [
    # config
    "JSON_FILENAME","TOOL_NAME","TOML_PATH","SCHEMA_DOWNLOAD_URLS","SCHEMA_CACHE_FILES","SCHEMA_URLS",
    "DEFAULT_DMP_PATH","LICENSE_LINKS","EXTRA_ENUMS","LOCAL_FALLBACK_ENUMS","DK_UNI_MAP",
    "DMP_KEY_ORDER","DATASET_KEY_ORDER","DISTRIBUTION_KEY_ORDER","DATASET_ID_KEY_ORDER",
    "METADATA_ITEM_KEY_ORDER","SEC_PRIV_ITEM_KEY_ORDER","TECH_RES_ITEM_KEY_ORDER","HOST_KEY_ORDER","LICENSE_ITEM_KEY_ORDER",
    # io
    "load_json","save_json",
    # schema
    "fetch_schema","validate_against_schema","schema_version_from_url",
    # paths
    "load_default_dataset_path","data_type_from_path","norm_rel_urlish","to_bytes_mb",
    # defaults
    "now_iso_minute","today_iso","dmp_default_templates","apply_defaults_in_place","ensure_required_by_schema","repair_empty_enums",
    # extensions
    "get_extension_payload","set_extension_payload",
    # normalize
    "ensure_dmp_shape","normalize_root_in_place","normalize_datasets_in_place","reorder_dmp_keys","create_or_update_dmp_from_schema",
    # cookie sync
    "update_cookiecutter_from_dmp",
]
