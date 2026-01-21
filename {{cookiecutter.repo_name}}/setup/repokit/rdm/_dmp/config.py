from __future__ import annotations

from pathlib import Path

JSON_FILENAME = "cookiecutter.json"
TOOL_NAME = "cookiecutter"
TOML_PATH = "pyproject.toml"

# ──────────────────────────────────────────────────────────────────────────────
# Config (RDA-DMP 1.)
# ──────────────────────────────────────────────────────────────────────────────

SCHEMA_DOWNLOAD_URLS: dict[str, str] = {
    "1.0": (
        "https://raw.githubusercontent.com/RDA-DMP-Common/"
        "RDA-DMP-Common-Standard/master/examples/JSON/JSON-schema/"
        "1.0/maDMP-schema-1.0.json"
    ),
    "1.1": (
        "https://raw.githubusercontent.com/RDA-DMP-Common/"
        "RDA-DMP-Common-Standard/master/examples/JSON/JSON-schema/"
        "1.1/maDMP-schema-1.1.json"
    ),
    "1.2": (
        "https://raw.githubusercontent.com/RDA-DMP-Common/"
        "RDA-DMP-Common-Standard/master/examples/JSON/JSON-schema/"
        "1.2/maDMP-schema-1.2.json"
    ),
}

SCHEMA_CACHE_FILES: dict[str, Path] = {
    "1.0": Path("./bin/maDMP-schema-1.0.json"),
    "1.1": Path("./bin/maDMP-schema-1.1.json"),
    "1.2": Path("./bin/maDMP-schema-1.2.json"),
}

# Always store this exact value in dmp["schema"]
SCHEMA_URLS: dict[str, str] = {
    "1.0": (
        "https://github.com/RDA-DMP-Common/RDA-DMP-Common-Standard/"
        "tree/master/examples/JSON/JSON-schema/1.0"
    ),
    "1.1": (
        "https://github.com/RDA-DMP-Common/RDA-DMP-Common-Standard/"
        "tree/master/examples/JSON/JSON-schema/1.1"
    ),
    "1.2": (
        "https://github.com/RDA-DMP-Common/RDA-DMP-Common-Standard/"
        "tree/master/examples/JSON/JSON-schema/1.2"
    ),
}

DEFAULT_DMP_PATH = Path("./dmp.json")

DMP_KEY_ORDER = [
    "schema",
    "title",
    "description",
    "language",
    "created",
    "modified",
    "ethical_issues_exist",
    "ethical_issues_description",
    "ethical_issues_report",
    "dmp_id",
    "contact",
    "contributor",
    "project",
    "dataset",
    "extension",
]

DATASET_KEY_ORDER: list[str] = [
    "title",
    "description",
    "issued",
    "modified",
    "language",
    "keyword",
    "is_reused",
    "personal_data",
    "sensitive_data",
    "type",
    "preservation_statement",
    "dataset_id",
    "distribution",
    "data_quality_assurance",
    "metadata",
    "security_and_privacy",
    "technical_resource",
    "extension",
]

DISTRIBUTION_KEY_ORDER: list[str] = [
    "access_url",
    "format",
    "byte_size",
    "data_access",
    "host",
    "available_until",
    "license",
]

DATASET_ID_KEY_ORDER = ["identifier", "type"]
METADATA_ITEM_KEY_ORDER = ["language", "metadata_standard_id", "description"]
SEC_PRIV_ITEM_KEY_ORDER = ["title", "description"]
TECH_RES_ITEM_KEY_ORDER = ["name", "description"]
HOST_KEY_ORDER = ["title", "url"]
LICENSE_ITEM_KEY_ORDER = ["license_ref", "start_date"]

LICENSE_LINKS: dict[str, str] = {
    "CC-BY-4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC0-1.0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "None": "",
}

EXTRA_ENUMS: dict[str, list[str]] = {
    "dmp.dataset[].distribution[].license[].license_ref": list(LICENSE_LINKS.values()),
}

LOCAL_FALLBACK_ENUMS: dict[str, list[str]] = {
    "dmp.dataset[].personal_data": ["yes", "no", "unknown"],
    "dmp.dataset[].sensitive_data": ["yes", "no", "unknown"],
}

DK_UNI_MAP = {
    "cbs.dk": {
        "name": "Copenhagen Business School",
        "abbreviation": "CBS",
        "ror": "https://ror.org/04sppb023",
        "dataverse_alias": "cbs",
        "dataverse_default_base_url": "https://demo.dataverse.deic.dk",
    },
    "ku.dk": {
        "name": "University of Copenhagen",
        "abbreviation": "KU",
        "ror": "https://ror.org/035b05819",
        "dataverse_alias": "ku",
        "dataverse_default_base_url": "https://dataverse.deic.dk",
    },
    "sdu.dk": {
        "name": "University of Southern Denmark",
        "abbreviation": "SDU",
        "ror": "https://ror.org/03yrrjy16",
        "dataverse_alias": "sdu",
        "dataverse_default_base_url": "https://demo.dataverse.deic.dk",
    },
    "au.dk": {
        "name": "Aarhus University",
        "abbreviation": "AU",
        "ror": "https://ror.org/01aj84f44",
        "dataverse_alias": "au",
        "dataverse_default_base_url": "https://demo.dataverse.deic.dk",
    },
    "dtu.dk": {
        "name": "Technical University of Denmark",
        "abbreviation": "DTU",
        "ror": "https://ror.org/04qtj9h94",
        "dataverse_alias": "dtu",
        "dataverse_default_base_url": "https://demo.dataverse.deic.dk",
    },
    "aau.dk": {
        "name": "Aalborg University",
        "abbreviation": "AAU",
        "ror": "https://ror.org/04m5j1k67",
        "dataverse_alias": "aau",
        "dataverse_default_base_url": "https://demo.dataverse.deic.dk",
    },
    "ruc.dk": {
        "name": "Roskilde University",
        "abbreviation": "RUC",
        "ror": "https://ror.org/014axpa37",
        "dataverse_alias": "ruc",
        "dataverse_default_base_url": "https://demo.dataverse.deic.dk",
    },
    "itu.dk": {
        "name": "IT University of Copenhagen",
        "abbreviation": "ITU",
        "ror": "https://ror.org/02309jg23",
        "dataverse_alias": "itu",
        "dataverse_default_base_url": "https://demo.dataverse.deic.dk",
    },
}
