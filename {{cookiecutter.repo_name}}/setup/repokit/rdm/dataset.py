import hashlib
import json
import os
import pathlib
from collections import defaultdict
from collections.abc import Iterable
from copy import deepcopy
from datetime import datetime
from typing import Any

import dirhash

from ..common import PROJECT_ROOT, change_dir, check_path_format, ensure_correct_kernel, read_toml
from ..vcs import git_commit, git_log_to_file
from .dmp import (
    DEFAULT_DMP_PATH,
    LICENSE_LINKS,
    create_or_update_dmp_from_schema,
    data_type_from_path,
    dmp_default_templates,
    ensure_dmp_shape,
    get_extension_payload,
    # ── functions ────────────────────────────────────────────
    load_json,
    main,
    norm_rel_urlish,
    now_iso_minute,
    save_json,
    to_bytes_mb,
)

DEFAULT_UPDATE_FIELDS = []  # top-level fields
DEFAULT_UPDATE_DIST_FIELDS = ["format", "byte_size"]  # nested fields to update


def get_hash(path, algo: str = "sha256"):
    """
    Get the hash of a file or folder.
    Uses hashlib for files and dirhash for directories.
    """
    try:
        if os.path.isfile(path):
            h = hashlib.new(algo)
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            return h.hexdigest()
        elif os.path.isdir(path):
            return dirhash(path, algo)
        else:
            raise ValueError(f"{path} does not exist or is not a valid file or directory.")
    except Exception as e:
        print(f"Error while calculating hash for {path}: {e}")
        return None


def get_file_info(file_paths):
    number_of_files = 0
    total_size = 0.0
    file_formats = set()
    individual_sizes_mb = []
    for path in file_paths:
        number_of_files += 1
        file_size_mb = os.path.getsize(path) / (1024 * 1024)
        total_size += file_size_mb
        individual_sizes_mb.append(int(round(file_size_mb)))
        file_formats.add(os.path.splitext(path)[1].lower())
    return number_of_files, total_size, file_formats, individual_sizes_mb


def get_all_files(destination):
    all_files = set()
    for root, _, files in os.walk(destination):
        for file in files:
            all_files.add(os.path.join(root, file))
    return all_files


def get_data_files(base_dir="./data", ignore=None, recursive=False):
    if ignore is None:
        ignore = {".git", ".gitignore", ".gitkeep", ".gitlog"}
    all_files = []
    try:
        subdirs = [
            name for name in os.listdir(base_dir) if name not in ignore and not name.startswith(".")
        ]
    except FileNotFoundError:
        return [], []
    subdirs = sorted(subdirs)
    for sub in subdirs:
        sub_path = os.path.join(base_dir, sub)
        if os.path.isdir(sub_path):
            iterator = os.walk(sub_path) if recursive else [(sub_path, [], os.listdir(sub_path))]
            for root, dirs, files in iterator:
                dirs[:] = [d for d in dirs if d not in ignore and not d.startswith(".")]
                for fn in files:
                    if fn not in ignore and not fn.startswith("."):
                        all_files.append(os.path.join(root, fn))
    return all_files, subdirs


def datasets_to_json(
    json_path=DEFAULT_DMP_PATH,
    entry=None,
    update_fields: list[str] | None = None,
    update_distribution_fields: list[str] | None = None,
    bump_modified_on_distribution_updates: bool = False,
):
    """
    Upsert a dataset entry into {"dmp": {"dataset": [...]}}.

    Matching:
      - prefer by distribution rel URL (url_acess/url_access/access_url/download_url)
      - else by title

    Update policy (when a match is found):
      - changed_flag := (existing.x_dcas.hash != entry.x_dcas.hash)
      - overwrite ONLY:
          * x_dcas payload in `extension` (if provided)
          * top-level fields in `update_fields`
          * nested distribution fields in `update_distribution_fields`, matched by rel URL
      - modified := now_iso_minute() iff changed_flag
        (or also when distribution fields changed, if bump_modified_on_distribution_updates=True)
    """
    if update_fields is None:
        update_fields = DEFAULT_UPDATE_FIELDS
    if update_distribution_fields is None:
        update_distribution_fields = DEFAULT_UPDATE_DIST_FIELDS

    json_path = PROJECT_ROOT / pathlib.Path(json_path)
    data = load_json(json_path)
    dmp = data["dmp"]
    datasets = dmp.get("dataset", [])

    any_change_flag = False

    def _extract_rel_url(dist: dict) -> str | None:
        for k in ("url_acess", "url_access", "access_url", "download_url"):
            v = (dist or {}).get(k)
            if v:
                return norm_rel_urlish(v)
        return None

    def _collect_rel_urls(ds: dict) -> set[str]:
        out: set[str] = set()
        for d in (ds or {}).get("distribution", []) or []:
            u = _extract_rel_url(d)
            if u:
                out.add(u)
        return out

    new_rel_urls = _collect_rel_urls(entry or {})
    idx = None
    if new_rel_urls:
        for i, ds in enumerate(datasets):
            if _collect_rel_urls(ds) & new_rel_urls:
                idx = i
                break
    else:
        for i, ds in enumerate(datasets):
            if (ds or {}).get("title") == (entry or {}).get("title"):
                idx = i
                break

    if idx is not None:
        existing = datasets[idx]
        merged = deepcopy(existing)

        # --- 1) changed_flag from x_dcas.hash only ---
        existing_x = get_extension_payload(existing, "x_dcas") or {}
        entry_x = get_extension_payload(entry or {}, "x_dcas") or {}
        existing_hash = existing_x.get("hash")
        entry_hash = entry_x.get("hash")
        changed_flag = existing_hash != entry_hash

        # --- 2) optionally replace/insert x_dcas payload ---
        if entry_x:
            merged_ext = list(existing.get("extension") or [])
            merged_ext = [it for it in merged_ext if not (isinstance(it, dict) and "x_dcas" in it)]
            merged_ext.append({"x_dcas": entry_x})
            merged["extension"] = merged_ext

        # --- 3) overwrite ONLY whitelisted top-level fields ---
        for k in update_fields:
            if k in (entry or {}) and (entry[k] is not None):
                merged[k] = entry[k]

        # --- 4) overwrite ONLY whitelisted nested fields in distribution (URL-matched) ---
        dist_changed = False
        if "distribution" in (entry or {}):
            incoming_list = entry.get("distribution") or []
            existing_list = list(merged.get("distribution") or [])
            # map existing distributions by rel URL
            existing_by_u = {}
            for d in existing_list:
                u = _extract_rel_url(d or {})
                if u:
                    existing_by_u[u] = d
            # apply field updates for matched items
            for s in incoming_list:
                u = _extract_rel_url(s or {})
                if not u or u not in existing_by_u:
                    continue
                tgt = existing_by_u[u]
                for f in update_distribution_fields:
                    if f in s and s[f] is not None and s[f] != tgt.get(f):
                        tgt[f] = s[f]
                        dist_changed = True
            if dist_changed:
                merged["distribution"] = existing_list

        # --- 5) modified policy ---
        if changed_flag or (bump_modified_on_distribution_updates and dist_changed):
            merged["modified"] = now_iso_minute()
        else:
            merged["modified"] = existing.get("modified")

        datasets[idx] = merged
        if changed_flag:
            print(f"Updated DMP entry for {merged.get('title')}.")
            any_change_flag = True
        else:
            print(f"No changes detected for DMP entry: {merged.get('title')}.")

    else:
        datasets.append(entry)
        print(f"Added DMP entry for {entry.get('title')}.")
        any_change_flag = True

    # Sort by x_dcas.data_type then title
    def _sort_key(ds):
        x = get_extension_payload(ds, "x_dcas") or {}
        return (x.get("data_type") or "", ds.get("title") or "")

    datasets.sort(key=_sort_key)

    dmp["dataset"] = datasets
    dmp["modified"] = now_iso_minute()
    save_json(json_path, data)

    return any_change_flag, json_path


def remove_missing_datasets(json_path: str | os.PathLike = DEFAULT_DMP_PATH):
    """
    Ensure the DMP file exists and is shaped. For any dataset whose
    access/download URL (or extension.x_dcas.destination) no longer exists on disk,
    DO NOT delete the dataset; instead set:
      - extension.x_dcas = {}  (as {"x_dcas": {}} in a list-shaped extension)
      - distribution[*].access_url = ""

    Returns the absolute Path to the JSON file.
    """
    # Resolve path relative to project root (3 levels up from this file)
    root = PROJECT_ROOT
    json_path = (root / pathlib.Path(json_path)).resolve()

    # ---- Load & shape ----
    data = load_json(json_path) or {}
    if not isinstance(data, dict):
        data = {}

    dmp = data.get("dmp") or {}
    data["dmp"] = dmp  # reattach so mutations persist
    datasets = dmp.get("dataset")
    if not isinstance(datasets, list):
        datasets = []
    dmp["dataset"] = datasets  # ensure list exists

    # ---- Helpers ----
    def _exists_on_disk(ds: dict) -> bool:
        # any distribution URL that resolves on local FS
        for dist in ds.get("distribution") or []:
            if not isinstance(dist, dict):
                continue
            p = dist.get("access_url") or dist.get("download_url")
            if p and (os.path.exists(p) or os.path.exists(p.replace("/", os.sep))):
                return True
        # extension.x_dcas.destination
        x = get_extension_payload(ds, "x_dcas") or {}
        dest = x.get("destination")
        return bool(dest and os.path.exists(dest))

    def _set_x_dcas_to_empty(ds: dict) -> None:
        """
        Ensure extension has exactly ONE x_dcas entry formed as {"x_dcas": {}}.
        - If extension is a dict: extension["x_dcas"] = {}
        - If extension is a list: remove any x_dcas variants and append {"x_dcas": {}}
          Variants removed: {"x_dcas": ...}, {"name":"x_dcas",...}, {"extension":"x_dcas",...}
        """
        exts = ds.get("extension")

        # Dict-shaped extension
        if isinstance(exts, dict):
            exts["x_dcas"] = {}
            return

        # List-shaped (or missing): normalize to list and enforce single {"x_dcas": {}}
        if not isinstance(exts, list):
            ds["extension"] = [{"x_dcas": {}}]
            return

        new_exts = []
        for ext in exts:
            if not isinstance(ext, dict):
                new_exts.append(ext)
                continue
            # Drop any prior x_dcas in any known shape
            if "x_dcas" in ext or ext.get("name") == "x_dcas" or ext.get("extension") == "x_dcas":
                continue
            new_exts.append(ext)

        new_exts.append({"x_dcas": {}})
        ds["extension"] = new_exts

    # ---- Main pass ----
    updated = 0
    for ds in datasets:
        if not _exists_on_disk(ds):
            _set_x_dcas_to_empty(ds)
            # Clear access_url in all distributions
            for dist in ds.get("distribution") or []:
                if isinstance(dist, dict):
                    dist["access_url"] = ""
            updated += 1

    if updated:
        dmp["modified"] = now_iso_minute()
        print(f"Updated {updated} dataset(s).")
        save_json(json_path, data)

    return json_path


def dataset(destination, json_path=DEFAULT_DMP_PATH):
    def make_dataset_entry(name, distribution, x_dcas_payload):
        templates = dmp_default_templates()

        # Start from a deep copy so the global template isn't mutated
        entry = deepcopy(templates["dataset"])

        # Simple overlays
        entry["title"] = name
        entry["issued"] = now_iso_minute()
        entry["modified"] = now_iso_minute()

        # distribution must be a list with one object; merge with its template
        dist = deepcopy(templates["distribution"])
        if isinstance(distribution, dict):
            dist.update(distribution)  # shallow overlay
        entry["distribution"] = [dist]

        # x_dcas lives under dataset.extension as a single item: {"x_dcas": {...}}
        xdcas = deepcopy(templates["x_dcas"])
        if isinstance(x_dcas_payload, dict):
            xdcas.update(x_dcas_payload)
        entry["extension"] = [{"x_dcas": xdcas}]

        return entry

    def make_x_dcas_payload(
        *,
        data_type: str | None = None,
        destination: str | None = None,
        number_of_files: int | None = None,
        total_size_mb: float | None = None,
        file_formats: Iterable[str] | None = None,
        data_files: Iterable[str] | None = None,
        data_size_mb: Iterable[float] | None = None,
        hash_value: str | None = None,  # 'hash' is a builtin, so use hash_value
    ) -> dict[str, Any]:
        """
        Build x_dcas by loading templates['x_dcas'] and only updating fields
        that already exist in the template.
        """
        templates = dmp_default_templates()
        x = deepcopy(templates["x_dcas"])

        # Prepare candidate updates (normalize types lightly)
        updates: dict[str, Any] = {
            "data_type": data_type,
            "destination": norm_rel_urlish(destination) if destination is not None else None,
            "number_of_files": int(number_of_files) if number_of_files is not None else None,
            "total_size_mb": int(round(total_size_mb)) if total_size_mb is not None else None,
            "file_formats": list(file_formats) if file_formats is not None else None,
            "data_files": list(data_files) if data_files is not None else None,
            "data_size_mb": list(data_size_mb) if data_size_mb is not None else None,
            "hash": hash_value,
        }

        # Only update keys that already exist in the template AND have a non-None value
        for k, v in updates.items():
            if v is not None and k in x:
                x[k] = v

        return x

    cookie = (
        read_toml(
            folder=str(PROJECT_ROOT),
            json_filename="cookiecutter.json",
            tool_name="cookiecutter",
            toml_path="pyproject.toml",
        )
        or {}
    )

    destination = check_path_format(destination)

    if os.path.isfile(destination):
        data_files = [destination]
    else:
        os.makedirs(destination, exist_ok=True)
        data_files = sorted(get_all_files(destination))

    number_of_files, total_size_mb, file_formats, individual_sizes_mb = get_file_info(data_files)

    name = os.path.basename(destination)
    data_type = data_type_from_path(destination)

    # distribution (complete RDA-DMP shape with defaults; 1.2-compliant)
    distribution = {
        # "title": name,
        "access_url": norm_rel_urlish(destination),
        # "download_url": "",
        "format": [ext.strip(".") for ext in sorted(file_formats)],
        "byte_size": to_bytes_mb(total_size_mb),
        "data_access": "open" if data_files else "closed",
        # "host": {"title": "Project repository", "url": ""},
        "available_until": "",
        # "description": "",
        "license": [
            {
                "license_ref": LICENSE_LINKS.get(cookie.get("DATA_LICENSE"), ""),
                "start_date": datetime.now().strftime("%Y-%m-%d"),
            }
        ],
    }

    # DCAS payload wrapped under dataset.extension
    x_dcas_payload = make_x_dcas_payload(
        data_type=data_type,
        destination=destination,
        number_of_files=number_of_files,
        total_size_mb=int(round(total_size_mb)),
        file_formats=sorted(list(file_formats)),
        data_files=data_files,
        data_size_mb=individual_sizes_mb,
        hash_value=get_hash(destination),
    )

    entry = make_dataset_entry(name, distribution, x_dcas_payload)

    change_flag, json_path = datasets_to_json(json_path=json_path, entry=entry)

    return change_flag, json_path


def generate_dataset_table(
    json_path: str,
    file_descriptions: dict[str, str] | None = None,
    include_hash: bool = False,
) -> tuple[str | None, str | None]:
    if not os.path.exists(json_path):
        return None, None

    with open(json_path, encoding="utf-8") as fh:
        json_data = json.load(fh)

    dmp = ensure_dmp_shape(json_data)["dmp"]
    datasets = dmp.get("dataset", [])

    hidden_fields = set()
    if not include_hash:
        hidden_fields.add("hash")

    def is_nonempty(val):
        return val not in (None, "", [], {}, "N/A", "Not provided")

    def safe_str(val):
        return "N/A" if val in (None, "", [], {}, "Not provided") else str(val)

    rows = []
    dynamic_id_fields: set[str] = set()  # <-- collect dynamic keys from dataset_id.type

    for ds in datasets:
        x = get_extension_payload(ds, "x_dcas") or {}
        dist = (ds.get("distribution") or [{}])[0]

        # Build the row (unchanged fields kept as-is)
        # Normalize file formats to a list for safe rendering
        fmts = dist.get("format")
        if isinstance(fmts, str):
            fmts_list = [fmts]
        elif isinstance(fmts, (list, set, tuple)):
            fmts_list = list(fmts)
        else:
            fmts_list = []
        fmts_list = sorted(list(set(fmts_list)))

        row = {
            "data_name": ds.get("title"),
            "destination": dist.get("download_url")
            or dist.get("access_url")
            or x.get("destination"),
            "created": ds.get("issued"),
            "lastest_change": ds.get("modified"),
            "hash": x.get("hash"),
            "provided": "Provided" if x.get("data_files") else "Can be re-created",
            "number_of_files": x.get("number_of_files"),
            "total_size_mb": x.get("total_size_mb")
            if x.get("total_size_mb") is not None
            else int(round((dist.get("byte_size") or 0) / (1024 * 1024))),
            "file_formats": fmts_list,
            "zip_file": None,
            "description": ds.get("description"),
            "_dtype": x.get("data_type") or data_type_from_path(x.get("destination") or ""),
            "_files": x.get("data_files") or [],
            "_sizes": x.get("data_size_mb") or [],
        }

        # --- Dynamic identifier field ---
        ds_id = ds.get("dataset_id") or {}
        if isinstance(ds_id, list) and ds_id:
            ds_id = ds_id[0]

        # Coerce empty/whitespace strings to None
        raw_identifier = ds_id.get("identifier")
        if isinstance(raw_identifier, str):
            ds_id_identifier = raw_identifier.strip() or None
        else:
            ds_id_identifier = raw_identifier

        raw_type = ds_id.get("type")
        ds_id_type = (raw_type.strip() if isinstance(raw_type, str) else raw_type) or None

        # Add a dynamic field named by the identifier type, with value = identifier (possibly None)
        if ds_id_type:
            row[str(ds_id_type)] = ds_id_identifier
            dynamic_id_fields.add(str(ds_id_type))

        rows.append(row)

    grouped = defaultdict(list)
    for r in rows:
        grouped[r["_dtype"]].append(r)

    # Standard (fixed) columns
    standard_fields = {
        "data_name": "Name",
        "destination": "Location",
        "created": "Created",
        "lastest_change": "Lastest Change",
        "hash": "Hash",
        "provided": "Provided",
        "number_of_files": "Number of Files",
        "total_size_mb": "Total Size (MB)",
        "file_formats": "File Formats",
        "zip_file": "Zip File",
        "description": "Description",
    }
    if not include_hash:
        standard_fields.pop("hash", None)

    # Add dynamic identifier columns (header = key itself)
    for dyn in sorted(dynamic_id_fields):
        standard_fields[dyn] = dyn

    # Pick the active columns to show (non-empty in at least one row)
    active_fields = [
        k
        for k in standard_fields
        if k not in hidden_fields and any(is_nonempty(r.get(k)) for r in rows)
    ]

    summary_header = "| " + " | ".join([standard_fields[k] for k in active_fields]) + " |\n"
    summary_divider = (
        "| " + " | ".join(["-" * len(standard_fields[k]) for k in active_fields]) + " |\n"
    )

    base_detail = [
        "data_name",
        "data_files",
        "destination",
        "created",
        "lastest_change",
        "provided",
        "data_size",
    ]
    if (
        include_hash
        and "hash" not in hidden_fields
        and any(is_nonempty(r.get("hash")) for r in rows)
    ):
        base_detail.insert(5, "hash")

    # Include dynamic identifier fields in the detail table as well
    base_detail = base_detail + sorted(dynamic_id_fields)

    detail_header = "| " + " | ".join([f.replace("_", " ").title() for f in base_detail]) + " |\n"
    detail_divider = "| " + " | ".join(["-" * len(f) for f in base_detail]) + " |\n"

    summary_blocks: list[str] = []
    detail_blocks: list[str] = []

    for dtype, entries in sorted(grouped.items()):
        desc = (
            f" <- {file_descriptions.get(dtype, '')}"
            if (file_descriptions and dtype in file_descriptions)
            else None
        )
        header = f"### {dtype} {desc}\n" if desc else f"### {dtype}\n"
        summary_blocks.append(header + summary_header + summary_divider)

        need_detail = any(len(r["_files"]) > 1 for r in entries)
        if need_detail:
            detail_blocks.append(header + detail_header + detail_divider)

        for r in entries:
            # Summary row
            vals = []
            for k in active_fields:
                if k == "file_formats":
                    fmts = r.get(k) or []
                    if isinstance(fmts, (list, tuple, set)):
                        val = "; ".join("." + f for f in fmts) or "N/A"
                    else:
                        val = "." + str(fmts) if fmts else "N/A"
                else:
                    val = r.get(k, "N/A")
                vals.append(safe_str(val))
            summary_blocks.append("| " + " | ".join(vals) + " |\n")

            # Detail rows
            if need_detail:
                files = r["_files"]
                sizes = r["_sizes"]
                if len(sizes) < len(files):
                    sizes += ["?"] * (len(files) - len(sizes))
                for f, sz in zip(files, sizes, strict=False):
                    detail_vals = []
                    for k in base_detail:
                        if k == "data_files":
                            detail_vals.append(safe_str(f))
                        elif k == "data_size":
                            detail_vals.append(safe_str(sz))
                        else:
                            detail_vals.append(safe_str(r.get(k)))
                    detail_blocks.append("| " + " | ".join(detail_vals) + " |\n")

        summary_blocks.append("\n")
        if need_detail:
            detail_blocks.append("\n")

    return "".join(summary_blocks), "".join(detail_blocks)


def dataset_to_readme(markdown_table: str, readme_file: str = "./README.md"):
    section_title = "**The following datasets are included in the project:**"
    readme_path = PROJECT_ROOT / pathlib.Path(readme_file)
    new_section = f"{section_title}\n\n{markdown_table.strip()}\n</details>"
    try:
        content = readme_path.read_text(encoding="utf-8")
        if section_title in content:
            start = content.find(section_title)
            closing_tag = "</details>"
            close_idx = content.find(closing_tag, start)
            if close_idx != -1:
                end = close_idx + len(closing_tag)
            else:
                end = content.find("\n## ", start + len(section_title))
                end = end if end != -1 else len(content)
            updated = content[:start] + new_section + content[end:]
        else:
            updated = content.rstrip() + "\n\n" + new_section
    except FileNotFoundError:
        updated = new_section

    readme_path.parent.mkdir(parents=True, exist_ok=True)
    readme_path.write_text(updated.strip(), encoding="utf-8")
    print(f"{readme_path} successfully updated with dataset section.")


@ensure_correct_kernel
def main():
    os.chdir(PROJECT_ROOT)

    data_files, _ = get_data_files()

    create_or_update_dmp_from_schema(dmp_path=DEFAULT_DMP_PATH)

    json_path = remove_missing_datasets(json_path=DEFAULT_DMP_PATH)

    file_descriptions = read_toml(
        folder=PROJECT_ROOT,
        json_filename="./file_descriptions.json",
        tool_name="file_descriptions",
        toml_path="pyproject.toml",
    )

    for f in data_files:
        change_flag, json_path = dataset(destination=f, json_path=json_path)

    try:
        markdown_table, _ = generate_dataset_table(json_path, file_descriptions)
        if markdown_table:
            dataset_to_readme(markdown_table)
    except Exception as e:
        print(f"Error: {e}")


    if change_flag:
        if os.path.exists(".datalad") or os.path.exists(".dvc"):
            _ = git_commit(msg="Running 'set-dataset'", path=os.getcwd())
        elif os.path.exists(".git"):
            with change_dir("./data"):
                _ = git_commit(msg="Running 'set-dataset'", path=os.getcwd())
                git_log_to_file(os.path.join(".gitlog"))


if __name__ == "__main__":
    main()
