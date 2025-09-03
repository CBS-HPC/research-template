import os
import json
from datetime import datetime
import pathlib
from typing import Optional, Tuple, Dict, List, Set
from collections import defaultdict

from .readme_templates import *
from .versioning_tools import *
from .dmp_tools import *  



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

def get_data_files(base_dir='./data', ignore=None, recursive=False):
    if ignore is None:
        ignore = {'.git', '.gitignore', '.gitkeep', '.gitlog'}
    all_files = []
    try:
        subdirs = [name for name in os.listdir(base_dir)
                   if name not in ignore and not name.startswith('.')]
    except FileNotFoundError:
        return [], []
    subdirs = sorted(subdirs)
    for sub in subdirs:
        sub_path = os.path.join(base_dir, sub)
        if os.path.isdir(sub_path):
            iterator = os.walk(sub_path) if recursive else [(sub_path, [], os.listdir(sub_path))]
            for root, dirs, files in iterator:
                dirs[:] = [d for d in dirs if d not in ignore and not d.startswith('.')]
                for fn in files:
                    if fn not in ignore and not fn.startswith('.'):
                        all_files.append(os.path.join(root, fn))
    return all_files, subdirs

def datasets_to_json(json_path="./dmp.json", entry=None):
    """
    Upsert a dataset entry into {"dmp": {"dataset": [...]}}.
    Matches existing entries by the relative URL inside distribution
    (keys tried in order: 'url_acess', 'url_access', 'access_url', 'download_url').

    NOTE: This version expects/handles x_dcas under dataset.extension.
    """
    json_path = pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(json_path)
    data = load_json(json_path)
    dmp = data["dmp"]
    datasets = dmp.get("dataset", [])

    def _extract_rel_url(dist: dict) -> Optional[str]:
        for k in ("url_acess", "url_access", "access_url", "download_url"):
            v = dist.get(k)
            if v:
                return norm_rel_urlish(v)
        return None

    def _collect_rel_urls(ds: dict) -> Set[str]:
        out: Set[str] = set()
        for d in ds.get("distribution", []) or []:
            u = _extract_rel_url(d)
            if u:
                out.add(u)
        return out

    new_rel_urls = _collect_rel_urls(entry)
    idx = None
    if new_rel_urls:
        for i, ds in enumerate(datasets):
            if _collect_rel_urls(ds) & new_rel_urls:
                idx = i
                break
    else:
        for i, ds in enumerate(datasets):
            if ds.get("title") == entry.get("title"):
                idx = i
                break

    if idx is not None:
        existing = datasets[idx]
        entry["issued"] = existing.get("issued", entry.get("issued") or now_iso_minute())

        # Compare distributions and the x_dcas payload inside extension
        existing_x = get_extension_payload(existing, "x_dcas") or {}
        entry_x = get_extension_payload(entry, "x_dcas") or {}

        changed_flag = (
            json.dumps(existing.get("distribution", []), sort_keys=True) !=
            json.dumps(entry.get("distribution", []), sort_keys=True)
            or json.dumps(existing_x, sort_keys=True) != json.dumps(entry_x, sort_keys=True)
            or existing.get("description") != entry.get("description")
        )
        entry["modified"] = now_iso_minute() if changed_flag else existing.get("modified")

        merged = dict(existing)
        # Merge 'extension' carefully (keep other extensions)
        if entry.get("extension"):
            merged_ext = list(existing.get("extension") or [])
            # replace/insert x_dcas payload
            e_x = get_extension_payload(entry, "x_dcas")
            if e_x is not None:
                # remove any old x_dcas
                merged_ext = [it for it in merged_ext if not (isinstance(it, dict) and "x_dcas" in it)]
                merged_ext.append({"x_dcas": e_x})
            merged["extension"] = merged_ext

        # Shallow-merge the rest (preserve existing when entry has None)
        for k, v in entry.items():
            if k == "extension":
                continue
            if v is not None:
                merged[k] = v

        datasets[idx] = merged
        print(f"Updated DMP entry for {entry.get('title')}.")
    else:
        datasets.append(entry)
        print(f"Added DMP entry for {entry.get('title')}.")

    # Sort by x_dcas.data_type then title
    def _sort_key(ds):
        x = get_extension_payload(ds, "x_dcas") or {}
        return (x.get("data_type") or "", ds.get("title") or "")
    datasets.sort(key=_sort_key)

    dmp["dataset"] = datasets
    dmp["modified"] = now_iso_minute()
    save_json(json_path, data)

    # Validate and warn (non-fatal) so callers see problems
    try:
        errs = validate_against_schema(data, schema=fetch_schema())
        if errs:
            print("⚠️ Schema validation issues after upsert:")
            for e in errs[:50]:
                print(" -", e)
    except Exception:
        pass

    return json_path

def remove_missing_datasets(json_path: str | os.PathLike = "./dmp.json",
                            base_data_dir: str | os.PathLike = "./data",
                            autocreate: bool = True):
    """
    Ensure the DMP file exists and is shaped, then remove datasets whose
    access/download URL (or extension.x_dcas.destination) no longer exists on disk.
    Returns the absolute Path to the JSON file.
    """
    root = pathlib.Path(__file__).resolve().parent.parent.parent
    json_path = root / pathlib.Path(json_path)

    # 1) Ensure file exists + minimal DMP shape
    if not json_path.exists():
        if not autocreate:
            return json_path
        shaped = ensure_dmp_shape({})
        save_json(json_path, shaped)

    # 2) Load (already shaped by loader)
    data = load_json(json_path)
    dmp = data.get("dmp") or {}
    datasets = dmp.get("dataset")
    if not isinstance(datasets, list):
        dmp["dataset"] = []
        save_json(json_path, data)
        return json_path

    # 3) Helper: check existence on disk
    def _exists_on_disk(ds: dict) -> bool:
        # any distribution URL that resolves on local FS
        for dist in ds.get("distribution") or []:
            p = dist.get("access_url") or dist.get("download_url")
            if not p:
                continue
            if os.path.exists(p) or os.path.exists(p.replace("/", os.sep)):
                return True

        # extension.x_dcas.destination
        x = get_extension_payload(ds, "x_dcas") or {}
        dest = x.get("destination")
        if dest and os.path.exists(dest):
            return True

        return False

    # 4) Filter + save
    retained = [ds for ds in datasets if _exists_on_disk(ds)]
    removed = len(datasets) - len(retained)
    if removed:
        print(f"Removed {removed} dataset(s) with missing paths).")
    else:
        print("No missing dataset paths found.")

    dmp["dataset"] = retained
    dmp["modified"] = now_iso_minute()
    save_json(json_path, data)
    return json_path

def set_dataset(destination, json_path="./dmp.json"):
    
    project_root = Path(__file__).resolve().parent.parent.parent

    cookie = read_toml_json(
        folder=str(project_root),
        json_filename="cookiecutter.json",
        tool_name="cookiecutter",
        toml_path="pyproject.toml",
    ) or {}

 
    destination = check_path_format(destination)

    if os.path.isfile(destination):
        data_files = [destination]
    else:
        os.makedirs(destination, exist_ok=True)
        data_files = sorted(get_all_files(destination))

    number_of_files, total_size_mb, file_formats, individual_sizes_mb = get_file_info(data_files)
    if number_of_files > 1000:
        print("WARNING: Consider zipping datasets >1000 files.")

    created = now_iso_minute() 
    name = os.path.basename(destination)
    data_type = data_type_from_path(destination)

    # distribution (complete RDA-DMP shape with defaults; 1.2-compliant)
    distribution = {
        "title": name,
        "access_url": norm_rel_urlish(destination),
        "download_url": "",
        "format": [ext.strip(".") for ext in sorted(file_formats)],
        "byte_size": to_bytes_mb(total_size_mb),
        "data_access": "open" if data_files else "closed",
        "host": {"title": "Project repository", "url": ""},
        "available_until": "",
        "description": "",
        "license": [{
            "license_ref": LICENSE_LINKS.get(cookie.get("DATA_LICENSE"), ""),
            "start_date": datetime.now().strftime("%Y-%m-%d")
        }],
    }

    # required dataset_id (local, stable)
    dataset_id = make_dataset_id(name, distribution["access_url"])

    # DCAS payload wrapped under dataset.extension
    x_dcas_payload = {
        "data_type": data_type,
        "destination": destination,
        "number_of_files": number_of_files,
        "total_size_mb": int(round(total_size_mb)),
        "file_formats": sorted(list(file_formats)),
        "data_files": data_files,
        "data_size_mb": individual_sizes_mb,
        "hash": get_git_hash(destination),
    }

    entry = {
        # RDA-DMP dataset
        "title": name,
        "description": "",
        "issued": created,
        "modified": created,
        "language": "eng",               # ISO 639-3 code like "eng"
        "keyword": [],
        "type": "",
        "is_reused": False,
        "personal_data": "unknown",
        "sensitive_data": "unknown",
        "preservation_statement": "",
        "data_quality_assurance": [],
        "metadata": [{
            "language": "eng",
            "metadata_standard_id": {
                "identifier": "http://www.dublincore.org/specifications/dublin-core/dcmi-terms/",
                "type": "url"
            },
            "description": ""
        }],
        "security_and_privacy":  [{"title": "Security & Privacy", "description": ""}],
        "technical_resource": [{"name": "", "description": ""}],
        "dataset_id": dataset_id,
        "distribution": [distribution],

        # Extensions: x_dcas lives under dataset.extension
        "extension": [
            {"x_dcas": x_dcas_payload}
        ],
    }

    return datasets_to_json(json_path=json_path, entry=entry)

def generate_dataset_table(
    json_path: str,
    file_descriptions: Optional[Dict[str, str]] = None,
    include_hash: bool = False,
) -> Tuple[Optional[str], Optional[str]]:
    if not os.path.exists(json_path):
        return None, None

    with open(json_path, "r", encoding="utf-8") as fh:
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
    for ds in datasets:
        x = get_extension_payload(ds, "x_dcas") or {}
        dist = (ds.get("distribution") or [{}])[0]
        rows.append({
            "data_name": ds.get("title"),
            "destination": dist.get("download_url") or dist.get("access_url") or x.get("destination"),
            "created": ds.get("issued"),
            "lastest_change": ds.get("modified"),
            "hash": x.get("hash"),
            "provided": "Provided" if x.get("data_files") else "Can be re-created",
            "number_of_files": x.get("number_of_files"),
            "total_size_mb": x.get("total_size_mb") if x.get("total_size_mb") is not None
                             else int(round((dist.get("byte_size") or 0) / (1024 * 1024))),
            "file_formats": sorted(list(set((dist.get("format") or [])))),
            "zip_file": dist.get("download_url"),
            "description": ds.get("description"),
            "_dtype": x.get("data_type") or data_type_from_path(x.get("destination") or ""),
            "_files": x.get("data_files") or [],
            "_sizes": x.get("data_size_mb") or [],
        })

    grouped = defaultdict(list)
    for r in rows:
        grouped[r["_dtype"]].append(r)

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

    active_fields = [
        k for k in standard_fields
        if k not in hidden_fields and any(is_nonempty(r.get(k)) for r in rows)
    ]

    summary_header = "| " + " | ".join([standard_fields[k] for k in active_fields]) + " |\n"
    summary_divider = "| " + " | ".join(["-" * len(standard_fields[k]) for k in active_fields]) + " |\n"

    base_detail = ["data_name", "data_files", "destination", "created", "lastest_change",
                   "provided", "data_size"]
    if include_hash and "hash" not in hidden_fields and any(is_nonempty(r.get("hash")) for r in rows):
        base_detail.insert(5, "hash")

    detail_header = "| " + " | ".join([f.replace("_", " ").title() for f in base_detail]) + " |\n"
    detail_divider = "| " + " | ".join(["-" * len(f) for f in base_detail]) + " |\n"

    summary_blocks: List[str] = []
    detail_blocks: List[str] = []

    for dtype, entries in sorted(grouped.items()):
        desc = f" <- {file_descriptions.get(dtype, '')}" if (file_descriptions and dtype in file_descriptions) else None
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
                    val = "; ".join("." + f for f in (r.get(k) or [])) or "N/A"
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
                for f, sz in zip(files, sizes):
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
    readme_path = (pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(readme_file))
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
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)

    data_files, _ = get_data_files()

    create_or_update_dmp_from_schema(
        dmp_path=DEFAULT_DMP_PATH,
        schema_url=SCHEMA_URL,
        schema_cache=DEFAULT_SCHEMA_CACHE,
        force_schema_refresh=False,
    )
    print(f"DMP ensured at {DEFAULT_DMP_PATH.resolve()} using maDMP 1.2 schema (ordered).")

    json_path = remove_missing_datasets(json_path="./dmp.json")

    file_descriptions = read_toml_json(
        folder=project_root,
        json_filename="./file_descriptions.json",
        tool_name="file_descriptions",
        toml_path="pyproject.toml"
    )

    for f in data_files:
        json_path = set_dataset(destination=f, json_path=json_path)

    try:
        markdown_table, _ = generate_dataset_table(json_path, file_descriptions)
        if markdown_table:
            dataset_to_readme(markdown_table)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
