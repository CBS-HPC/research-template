import json
import os
import shutil
import zipfile
from pathlib import Path
from typing import Union, Iterable, Dict, Any, List

from .general_tools import *

package_installer(required_libraries =  ['requests'])

import requests


# Download Readme template:
def download_README_template(url:str = "https://raw.githubusercontent.com/social-science-data-editors/template_README/release-candidate/templates/README.md", readme_file:str = "./README_DCAS_template.md"):
    
    readme_file= str(Path(__file__).resolve().parent.parent.parent / Path(readme_file))

     # Check if the local file already exists
    if os.path.exists(readme_file):
        return
    
    # Ensure the parent directory exists
    folder_path = os.path.dirname(readme_file)
    os.makedirs(folder_path, exist_ok=True)

    # Send GET request to the raw file URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Save the content to a file
        with open(readme_file, 'wb') as file:
            file.write(response.content)
    else:
        print(f"Failed to download {readme_file} from {url}")

def _normalize_relpath(p: str) -> Path:
    """Normalize '.\\' / './' prefixes and separators into a relative Path."""
    p = p.strip().lstrip(".\\/")
    p = p.replace("\\", os.sep).replace("/", os.sep)
    return Path(p)

def _rel_from_root_str(path: Path, root: Path) -> str:
    """Return a string like '.\\sub\\path' on Windows or './sub/path' elsewhere."""
    rel = path.resolve().relative_to(root.resolve())
    return f".{os.sep}{str(rel)}"

def _zip_dir(src_dir: Path, out_zip_path: Path) -> Path:
    """Zip a directory (deflated). Returns the zip path."""
    out_zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(src_dir):
            root_path = Path(root)
            for f in files:
                abs_fp = root_path / f
                zf.write(abs_fp, arcname=str(abs_fp.relative_to(src_dir)))
    return out_zip_path

def migrate_datasets(
    dataset_json_path: Union[str, Path],
    source_root: Union[str, Path],
    dest_root: Union[str, Path],
    zip_threshold: int = 1000,
    overwrite: bool = True,
) -> List[Dict[str, Any]]:
    """
    Migrate datasets from source_root to dest_root according to datasets.json,
    preserving the subpath in each 'destination'. If number_of_files > zip_threshold,
    zip the *source* dataset folder and place '<folder>.zip' under the destination's parent.
    Also updates 'zip_file' in datasets.json with the relative zip path (or null if not zipped).
    """
    dataset_json_path = Path(dataset_json_path)
    source_root = Path(source_root).resolve()
    dest_root = Path(dest_root).resolve()

    with dataset_json_path.open("r", encoding="utf-8") as f:
        spec = json.load(f)

    results: List[Dict[str, Any]] = []
    datasets: Iterable[Dict[str, Any]] = spec.get("datasets", [])

    for ds in datasets:
        rel_path = _normalize_relpath(ds.get("destination", ""))
        src_path = (source_root / rel_path).resolve()
        dst_path = dest_root / rel_path

        number_of_files = int(ds.get("number_of_files", 0))
        ds["zip_file"] = None  # default; becomes a string if we create a zip
        action = {"data_name": ds.get("data_name"), "source": str(src_path), "status": "pending"}

        if not src_path.exists():
            action["status"] = "error"
            action["error"] = f"Source path not found: {src_path}"
            results.append(action)
            continue

        try:
            if number_of_files > zip_threshold:
                # Prefer zipping the dataset *folder*.
                if src_path.is_dir():
                    dst_zip_dir = dst_path.parent
                    zip_name = f"{src_path.name}.zip"
                    dst_zip_path = dst_zip_dir / zip_name

                    if dst_zip_path.exists() and overwrite:
                        dst_zip_path.unlink()

                    _zip_dir(src_path, dst_zip_path)
                    ds["zip_file"] = _rel_from_root_str(dst_zip_path, dest_root)
                    action["status"] = "zipped_and_copied"
                    action["dest"] = str(dst_zip_path.resolve())
                else:
                    # Fallback: if 'destination' points to a file, just copy it
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    if dst_path.exists() and overwrite:
                        dst_path.unlink()
                    shutil.copy2(src_path, dst_path)
                    # No zip created -> leave zip_file as None
                    action["status"] = "copied_file_fallback"
                    action["dest"] = str(dst_path.resolve())

            else:
                # Below threshold: copy as-is
                if src_path.is_file():
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    if dst_path.exists() and overwrite:
                        dst_path.unlink()
                    shutil.copy2(src_path, dst_path)
                    action["status"] = "copied_file"
                    action["dest"] = str(dst_path.resolve())
                else:
                    if dst_path.exists() and overwrite:
                        shutil.rmtree(dst_path)
                    shutil.copytree(src_path, dst_path)
                    action["status"] = "copied_folder"
                    action["dest"] = str(dst_path.resolve())

        except Exception as e:
            action["status"] = "error"
            action["error"] = f"{type(e).__name__}: {e}"

        results.append(action)

    # Write back updated 'zip_file' fields (and any other untouched metadata)
    with dataset_json_path.open("w", encoding="utf-8") as f:
        json.dump(spec, f, indent=4, ensure_ascii=False)

    return results


# Example:
# results = migrate_datasets(
#     dataset_json_path="datasets.json",
#     source_root="C:/path/to/original/project",
#     dest_root="D:/path/to/new/project",
#     zip_threshold=1000,
# )
# for r in results:
#     print(r)


def main():
    download_README_template(readme_file = "./DCAS template/README.md")

if __name__ == "__main__":
    
    # Change to project root directory
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)
    
    main()
