import os
import json
import argparse
import subprocess
from datetime import datetime
import pathlib
from collections import defaultdict

from .readme_templates import *
from .versioning_tools import *

# ──────────────────────────────
# Helpers for new JSON structure
# ──────────────────────────────

def load_json_with_metadata(json_file_path: str):
    if not os.path.exists(json_file_path):
        return {"datasets": [], "__hide_fields__": []}

    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):  # legacy fallback
        return {"datasets": data, "__hide_fields__": []}
    if "datasets" not in data:
        raise ValueError("Expected a dictionary with a 'datasets' key.")
    if "__hide_fields__" not in data:
        data["__hide_fields__"] = []
    return data

def save_json_with_metadata(json_file_path: str, data: dict):
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    #print(f"Metadata saved to {json_file_path}")

# ──────────────────────────────
# Core functions
# ──────────────────────────────

def get_file_info(file_paths):
    number_of_files = 0
    total_size = 0
    file_formats = set()
    individual_sizes = []

    for path in file_paths:
        number_of_files += 1
        file_size = os.path.getsize(path) / (1024 * 1024)
        total_size += file_size
        individual_sizes.append(int(file_size))
        file_formats.add(os.path.splitext(path)[1].lower())

    return number_of_files, total_size, file_formats, individual_sizes

def get_all_files(destination):
    all_files = set()
    for root, dirs, files in os.walk(destination):
        for file in files:
            full_path = os.path.join(root, file)
            all_files.add(full_path)
    return all_files

def add_to_json(json_file_path="./datasets.json", entry=None):
    json_file_path = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(json_file_path))
    data = load_json_with_metadata(json_file_path)
    datasets = data["datasets"]

    existing_index = next((i for i, d in enumerate(datasets) if d.get("destination") == entry.get("destination")), None)
    existing_entry = datasets[existing_index] if existing_index is not None else None

    if existing_entry:
        changed = False
        if entry.get("hash") and existing_entry.get("hash") != entry["hash"]:
            changed = True
        elif not all(existing_entry.get(k) == v for k, v in entry.items() if v is not None and k != "created"):
            changed = True

        if changed:
            entry["lastest_change"] = entry["created"]
            entry["created"] = existing_entry["created"]
            for k, v in entry.items():
                if v is not None:
                    existing_entry[k] = v
            datasets[existing_index] = existing_entry
            print(f"Updated existing dataset entry for {entry['data_name']}.")
    else:
        if not entry.get("data_name"):
            entry["data_name"] = os.path.basename(entry["destination"])
        datasets.append(entry)
        print(f"Added new dataset entry for {entry['data_name']}.")

    datasets.sort(key=lambda d: d.get("data_type", ""))
    data["datasets"] = datasets
    save_json_with_metadata(json_file_path, data)
    return json_file_path

def remove_missing_datasets(data_files, json_file_path="./datasets.json", base_data_dir="./data"):
    json_file_path = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(json_file_path))
    data = load_json_with_metadata(json_file_path)
    datasets = data["datasets"]

    current_data_files = set(data_files)
    current_data_dirs = {str(pathlib.Path(f).parent) for f in current_data_files}
    current_paths = current_data_files.union(current_data_dirs)

    original_count = len(datasets)
    retained = [ds for ds in datasets if ds.get("destination") and os.path.exists(ds["destination"])]
    removed = original_count - len(retained)

    if removed:
        print(f"Removed {removed} dataset(s) with missing destinations.")
    else:
        print("No missing dataset destinations found.")

    data["datasets"] = retained
    save_json_with_metadata(json_file_path, data)
    return json_file_path

def normalize_dataset_fields(json_file_path="./datasets.json"):
    json_file_path = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(json_file_path))
    data = load_json_with_metadata(json_file_path)
    datasets = data["datasets"]

    all_keys = set(k for entry in datasets if isinstance(entry, dict) for k in entry.keys())

    for entry in datasets:
        for key in all_keys:
            if key not in entry:
                entry[key] = None

    data["datasets"] = datasets
    save_json_with_metadata(json_file_path, data)
    return json_file_path

def set_dataset(data_name, destination, source=None, run_command=None, json_file_path="./datasets.json", doi=None, citation=None, license=None):
    destination = check_path_format(destination)

    if os.path.isfile(destination):
        data_files = [destination]
    else:
        os.makedirs(destination, exist_ok=True)
        initial_files = get_all_files(destination)

        if run_command:
            command_parts = run_command.split()
            command_list = command_parts + [source, destination]

            if is_installed(command_parts[0]):
                try:
                    result = subprocess.run(command_list, check=True, text=True, capture_output=True)
                    print(f"Command output:\n{result.stdout}")
                except subprocess.CalledProcessError as e:
                    print(f"Error executing command: {e}")
                    print(f"Command output:\n{e.output}")
                    return
            else:
                raise FileNotFoundError(f"The executable '{command_parts[0]}' was not found in the PATH.")
            updated_files = get_all_files(destination)
            data_files = list(updated_files - initial_files)
        else:
            data_files = list(initial_files)
        data_files = sorted(data_files)

    number_of_files, total_size, file_formats, individual_sizes = get_file_info(data_files)
    if number_of_files > 1000:
        print("WARNING: Consider zipping datasets >1000 files.")

    hash = get_git_hash(destination)
    created = datetime.now().strftime("%Y-%m-%dT%H:%M")

    entry = {
        "data_name": data_name or os.path.basename(destination),
        "data_type": os.path.basename(os.path.dirname(destination)),
        "destination": destination,
        "zip_file": license,
        "hash": hash,
        "number_of_files": number_of_files,
        "total_size_mb": int(total_size),
        "file_formats": list(file_formats),
        "created": created,
        "lastest_change": None,
        "data_files": data_files,
        "data_size": individual_sizes,
        "source": source,
        "run_command": " ".join(run_command.split()) if run_command else None,
        "DOI": doi,
        "citation": citation,
        "license": license
    }

    return add_to_json(json_file_path=json_file_path, entry=entry)

def generate_dataset_table(json_file_path: str):
    import json, os
    from collections import defaultdict

    if not os.path.exists(json_file_path):
        raise FileNotFoundError(f"The file {json_file_path} does not exist.")

    with open(json_file_path, "r", encoding="utf-8") as fh:
        json_data = json.load(fh)

    datasets = json_data["datasets"]
    hidden_fields = set(json_data.get("__hide_fields__", []))

    def is_nonempty(val):
        return val not in (None, "", [], {}, "N/A", "Not provided")

    def safe_str(val):
        return "N/A" if val in (None, "", [], {}, "Not provided") else str(val)

    grouped = defaultdict(list)
    for ds in datasets:
        dtype = ds.get("data_type", "Uncategorised")
        grouped[dtype].append(ds)

    standard_fields = {
        "data_name": "Name",
        "destination": "Location",
        "created": "Created",
        "lastest_change": "Lastest Change",
        "hash":"Hash",
        "provided": "Provided",
        "run_command": "Run Command",
        "number_of_files": "Number of Files",
        "total_size_mb": "Total Size (MB)",
        "file_formats": "File Formats",
        "source": "Source",
        "DOI": "DOI",
        "citation": "Citation",
        "license": "License",
        "notes": "Notes"
    }

    fixed_detail_fields = [
        "data_name", "data_files", "destination", "created", "lastest_change",
        "hash", "provided", "data_size", "run_command", "source",
        "DOI", "citation", "license", "notes"
    ]

    def get_field_label(key):
        return standard_fields.get(key, key.replace("_", " ").title())

    active_fields = [
        k for k in standard_fields
        if k not in hidden_fields and any(is_nonempty(ds.get(k)) for ds in datasets)
    ]

    all_seen_keys = {k for ds in datasets for k in ds.keys()}
    excluded_keys = set(standard_fields) | {"data_type", "data_files", "data_size", "hash"}
    extra_fields = sorted(all_seen_keys - excluded_keys - hidden_fields)

    all_summary_keys = active_fields + extra_fields
    summary_header = "| " + " | ".join([get_field_label(k) for k in all_summary_keys]) + " |\n"
    summary_divider = "| " + " | ".join(["-" * len(get_field_label(k)) for k in all_summary_keys]) + " |\n"

    extra_detail_keys = sorted(
        set(k for ds in datasets for k in ds.keys())
        - set(fixed_detail_fields)
        - {"data_type"} - hidden_fields
    )
    all_detail_keys = fixed_detail_fields + extra_detail_keys
    detail_header = "| " + " | ".join([k.replace("_", " ").title() for k in all_detail_keys]) + " |\n"
    detail_divider = "| " + " | ".join(["-" * len(k) for k in all_detail_keys]) + " |\n"

    summary_blocks = []
    detail_blocks = []

    for dtype, entries in sorted(grouped.items()):
        summary_blocks.append(f"### {dtype}\n{summary_header}{summary_divider}")
        need_detail = any(len(ds.get("data_files", [])) > 1 for ds in entries)
        if need_detail:
            detail_blocks.append(f"### {dtype}\n{detail_header}{detail_divider}")

        for ds in entries:
            row = []
            for k in all_summary_keys:
                if k == "provided":
                    val = "Provided" if ds.get("data_files") else "Can be re-created"
                elif k == "file_formats":
                    val = "; ".join(ds.get("file_formats", [])) or "N/A"
                else:
                    val = ds.get(k, "N/A")
                row.append(safe_str(val))
            summary_blocks.append("| " + " | ".join(row) + " |\n")

            if need_detail:
                files = ds.get("data_files", [])
                sizes = ds.get("data_size", [])
                if len(sizes) < len(files):
                    sizes += ["?"] * (len(files) - len(sizes))
                for f, sz in zip(files, sizes):
                    detail_row = []
                    for k in all_detail_keys:
                        if k == "data_files":
                            detail_row.append(safe_str(f))
                        elif k == "data_size":
                            detail_row.append(safe_str(sz))
                        elif k == "provided":
                            detail_row.append("Provided" if ds.get("data_files") else "Can be re-created")
                        else:
                            detail_row.append(safe_str(ds.get(k)))
                    detail_blocks.append("| " + " | ".join(detail_row) + " |\n")

        summary_blocks.append("\n")
        if need_detail:
            detail_blocks.append("\n")

    return "".join(summary_blocks), "".join(detail_blocks)

def dataset_to_readme(markdown_table: str, readme_file: str = "./README.md"):
    section_title = "**The following datasets are included in the project:**"
    readme_path = (pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(readme_file))

    new_section = f"{section_title}\n\n{markdown_table.strip()}\n"
    new_section += "</details>"
    try:
        content = readme_path.read_text(encoding="utf-8")
        if section_title in content:
            start = content.find(section_title)

            # NEW: end is the first "</details>" after the section title (inclusive)
            closing_tag = "</details>"
            close_idx = content.find(closing_tag, start)
            if close_idx != -1:
                end = close_idx + len(closing_tag)
            else:
                # Fallbacks if there's no closing tag
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
    def get_data_files(base_dir='./data', ignore=None, recursive=False):
        if ignore is None:
            ignore = {'.git', '.gitignore', '.gitkeep', '.gitlog'}
        all_files = []
        try:
            subdirs = [name for name in os.listdir(base_dir)
                       if os.path.isdir(os.path.join(base_dir, name))
                       and name not in ignore and not name.startswith('.')]
        except FileNotFoundError:
            return []
        for sub in sorted(subdirs):
            sub_path = os.path.join(base_dir, sub)
            for root, dirs, files in os.walk(sub_path) if recursive else [(sub_path, [], os.listdir(sub_path))]:
                dirs[:] = [d for d in dirs if d not in ignore and not d.startswith('.')]
                for fn in files:
                    if fn not in ignore and not fn.startswith('.'):
                        all_files.append(os.path.join(root, fn))
        return all_files

    json_file_path = "./datasets.json"
    data_files = get_data_files()
    json_file_path = remove_missing_datasets(data_files, json_file_path=json_file_path)

    for f in data_files:
        json_file_path = set_dataset(data_name=None, destination=f, source=None,
                                     run_command=None, json_file_path=json_file_path,
                                     doi=None, citation=None, license=None)

    try:
        normalize_dataset_fields(json_file_path)
        markdown_table, full_table = generate_dataset_table(json_file_path)
        dataset_to_readme(markdown_table)
        #dcas_path = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path("./DCAS template/dataset_list.md"))
        #with open(dcas_path, 'w') as out_md:
        #    out_md.write(full_table)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)
    main()
