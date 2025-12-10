import json
import os
import shutil
import zipfile
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import requests

from ..common import PROJECT_ROOT, language_dirs, load_from_env
from .dataset import get_data_files
from .dmp import load_default_dataset_path


DEFAULT_DATASET_PATH, _= load_default_dataset_path()

# Download Readme template:
def download_README_template(
    url: str = "https://raw.githubusercontent.com/social-science-data-editors/template_README/release-candidate/templates/README.md",
    readme_file: str = "./README_DCAS_template.md",
):
    readme_file = str(PROJECT_ROOT / readme_file)

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
        with open(readme_file, "wb") as file:
            file.write(response.content)
    else:
        print(f"Failed to download {readme_file} from {url}")


def migrate_datasets(
    dataset_json: str | Path,
    source_root: str | Path,
    dest_root: str | Path,
    zip_threshold: int = 1000,
    overwrite: bool = True,
) -> list[dict[str, Any]]:
    """
    Migrate datasets from source_root to dest_root according to dmp.json,
    preserving the subpath in each 'destination'. If number_of_files > zip_threshold,
    zip the *source* dataset folder and place '<folder>.zip' under the destination's parent.
    Also updates 'zip_file' in dmp.json with the relative zip path (or null if not zipped).
    """

    def _normalize_relpath(p: str) -> Path:
        """Normalize '.\\' / './' prefixes and separators into a relative Path."""
        if not p:
            return Path()
        p = p.strip().lstrip(".\\/")  # drop any leading ./ or .\ (and repeated)
        p = p.replace("\\", os.sep).replace("/", os.sep)
        return Path(p)

    def _rel_from_root_str(path: Path, root: Path) -> str:
        """Return a string like '.\\sub\\path' on Windows or './sub/path' elsewhere."""
        rel = path.resolve().relative_to(root.resolve())
        return f".{os.sep}{str(rel)}"

    def _zip_dir(src_dir: Path, out_zip_path: Path) -> Path:
        """Zip a directory (deflated). Returns the zip path."""
        out_zip_path.parent.mkdir(parents=True, exist_ok=True)
        mode = "w" if overwrite else ("x" if not out_zip_path.exists() else None)
        if mode is None:
            return out_zip_path  # respect overwrite=False and existing zip
        with zipfile.ZipFile(out_zip_path, mode, compression=zipfile.ZIP_DEFLATED) as zf:
            for root_dir, _, files in os.walk(src_dir):
                root_path = Path(root_dir)
                for f in files:
                    abs_fp = root_path / f
                    zf.write(abs_fp, arcname=str(abs_fp.relative_to(src_dir)))
        return out_zip_path

    # Resolve roots
    source_root = Path(source_root).resolve()
    dest_root = Path(dest_root).resolve()
    dest_root.mkdir(parents=True, exist_ok=True)

    # Resolve dmp.json sensibly
    dataset_json = Path(dataset_json)
    if not dataset_json.is_absolute():
        candidate = source_root / dataset_json
        dataset_json = candidate if candidate.exists() else dataset_json.resolve()

    with dataset_json.open("r", encoding="utf-8") as f:
        spec = json.load(f)

    results: list[dict[str, Any]] = []
    datasets: Iterable[dict[str, Any]] = spec.get("datasets", [])

    for ds in datasets:
        rel_path = _normalize_relpath(ds.get("destination", ""))
        src_path = (source_root / rel_path).resolve()
        dst_path = dest_root / rel_path

        number_of_files = int(ds.get("number_of_files", 0))
        ds["zip_file"] = None  # default; becomes a string if we create/use a zip
        action: dict[str, Any] = {
            "data_name": ds.get("data_name"),
            "source": str(src_path),
            "status": "pending",
        }

        if not src_path.exists():
            action["status"] = "error"
            action["error"] = f"Source path not found: {src_path}"
            results.append(action)
            continue

        try:
            if number_of_files > zip_threshold:
                # Prefer zipping the dataset *folder* when the destination points to a folder.
                if src_path.is_dir():
                    dst_zip_dir = dst_path.parent
                    zip_name = f"{src_path.name}.zip"
                    dst_zip_path = dst_zip_dir / zip_name

                    if dst_zip_path.exists() and overwrite:
                        dst_zip_path.unlink()

                    made_zip = _zip_dir(src_path, dst_zip_path)
                    if made_zip.exists():
                        ds["zip_file"] = _rel_from_root_str(made_zip, dest_root)
                        action["status"] = (
                            "zipped_and_copied"
                            if overwrite or not dst_zip_path.exists()
                            else "zip_exists_skipped"
                        )
                        action["dest"] = str(made_zip.resolve())
                    else:
                        action["status"] = "zip_exists_skipped"
                        ds["zip_file"] = _rel_from_root_str(dst_zip_path, dest_root)
                        action["dest"] = str(dst_zip_path.resolve())

                else:
                    # Fallback: destination points at a file -> just copy file
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    if dst_path.exists():
                        if overwrite:
                            if dst_path.is_dir():
                                shutil.rmtree(dst_path)
                            else:
                                dst_path.unlink()
                        else:
                            action["status"] = "skipped_exists"
                            action["dest"] = str(dst_path.resolve())
                            results.append(action)
                            continue
                    shutil.copy2(src_path, dst_path)
                    action["status"] = "copied_file_fallback"
                    action["dest"] = str(dst_path.resolve())

            else:
                # Below threshold: copy as-is
                if src_path.is_file():
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    if dst_path.exists():
                        if overwrite:
                            if dst_path.is_dir():
                                shutil.rmtree(dst_path)
                            else:
                                dst_path.unlink()
                        else:
                            action["status"] = "skipped_exists"
                            action["dest"] = str(dst_path.resolve())
                            results.append(action)
                            continue
                    shutil.copy2(src_path, dst_path)
                    action["status"] = "copied_file"
                    action["dest"] = str(dst_path.resolve())
                else:
                    # Directory copy
                    if dst_path.exists():
                        if overwrite:
                            if dst_path.is_file():
                                dst_path.unlink()
                            else:
                                shutil.rmtree(dst_path)
                        else:
                            action["status"] = "skipped_exists"
                            action["dest"] = str(dst_path.resolve())
                            results.append(action)
                            continue
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(src_path, dst_path)
                    action["status"] = "copied_folder"
                    action["dest"] = str(dst_path.resolve())

        except Exception as e:
            action["status"] = "error"
            action["error"] = f"{type(e).__name__}: {e}"

        results.append(action)

    # Write back updated 'zip_file' fields (and any other untouched metadata)
    with dataset_json.open("w", encoding="utf-8") as f:
        json.dump(spec, f, indent=4, ensure_ascii=False)

    return results


def copy_items(
    items: Iterable[str],
    dest_root: os.PathLike | str,
    source_root: os.PathLike | str,
    base: os.PathLike | str | None = None,
    overwrite: bool = True,
    ignore_patterns: Iterable[str] | None = None,
):
    """
    Copy a list of files/directories into dest_root.

    - items: iterable of paths to copy (files and/or directories). Relative items are resolved under source_root.
    - dest_root: new project root to copy into.
    - source_root: base folder used to resolve relative `items`.
    - base: if provided, preserve each item's path relative to this folder
            (otherwise preserve relative to source_root when possible).
            e.g. base="C:/src", item="C:/src/data/00_raw/x.pkl"
            -> copied to "<dest_root>/data/00_raw/x.pkl"
            If item is not under base/source_root, falls back to basename.
    - overwrite: if True, replaces existing files/dirs at the destination.
    - ignore_patterns: optional globs passed to shutil.ignore_patterns for directories.

    Returns a list of per-item results: {"src", "dest", "status", "error?"}.
    """

    def _resolve_src(item: str, source_root: Path) -> Path:
        p = Path(item)
        if p.is_absolute():
            return p
        # Treat any relative path as relative to source_root
        return (source_root / p).resolve()

    def _rel_dest_for(
        src: Path, dest_root: Path, base: Path | None, fallback_root: Path | None
    ) -> Path:
        # Prefer explicit base; otherwise try relative to fallback_root (source_root)
        for root in [base, fallback_root]:
            if root:
                try:
                    rel = src.resolve().relative_to(root.resolve())
                    return dest_root / rel
                except Exception:
                    pass
        return dest_root / src.name

    def _is_subpath(path: Path, parent: Path) -> bool:
        try:
            path.resolve().relative_to(parent.resolve())
            return True
        except Exception:
            return False

    source_root = Path(source_root).resolve()
    dest_root = Path(dest_root).resolve()
    dest_root.mkdir(parents=True, exist_ok=True)
    base_path = Path(base).resolve() if base else None
    ignore = shutil.ignore_patterns(*ignore_patterns) if ignore_patterns else None

    results: list[dict[str, Any]] = []

    for item in items:
        try:
            src = _resolve_src(item, source_root)
        except Exception as e:
            results.append(
                {"src": str(item), "status": "error", "error": f"{type(e).__name__}: {e}"}
            )
            continue

        rec: dict[str, Any] = {"src": str(src), "status": "pending"}

        if not src.exists():
            rec.update(status="error", error=f"Not found: {src}")
            results.append(rec)
            continue

        dest = _rel_dest_for(src, dest_root, base_path, source_root)
        rec["dest"] = str(dest)

        try:
            # Guard: don't copy a folder into itself (or inside itself)
            if src.is_dir() and (_is_subpath(dest_root, src) or _is_subpath(dest, src)):
                raise ValueError(f"Destination lies inside source directory: {dest}")

            if src.is_file():
                dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.exists():
                    if overwrite:
                        if dest.is_dir():
                            shutil.rmtree(dest)
                        else:
                            dest.unlink()
                    else:
                        rec["status"] = "skipped_exists"
                        results.append(rec)
                        continue
                shutil.copy2(src, dest)
                rec["status"] = "copied_file"

            else:  # directory
                if dest.exists():
                    if overwrite:
                        if dest.is_file():
                            dest.unlink()
                        else:
                            shutil.rmtree(dest)
                    else:
                        rec["status"] = "skipped_exists"
                        results.append(rec)
                        continue
                shutil.copytree(src, dest, ignore=ignore)
                rec["status"] = "copied_dir"

        except Exception as e:
            rec["status"] = "error"
            rec["error"] = f"{type(e).__name__}: {e}"

        results.append(rec)

    return results


def copy_data_items(
    items: Iterable[str | Path],
    current_base: str | Path = DEFAULT_DATASET_PATH["parent_path"],
    dest_base: str | Path = "./DCAS template/data",
    overwrite: bool = True,
    create_missing_dirs: bool = True,
) -> list[dict[str, str]]:
    """
    For each path in `items`:
      - If it's a directory: create the corresponding directory under `dest_base`
        (does NOT copy contents).
      - If it's a file: copy the file under `dest_base`, preserving its path
        relative to `current_base` if possible.
      - If the source path does not exist and `create_missing_dirs` is True AND
        the item looks like a directory (trailing slash or no extension),
        create the destination directory anyway.

    Returns a list of {"src","dst","status",("error")} per item.
    """

    cur_base = Path(current_base)

    def _rel_under_base(p: Path) -> Path:
        """
        Path of `p` relative to `current_base`, if possible.

        - If `p` is inside `current_base`, return p.relative_to(current_base).
        - Otherwise:
            * if p is relative, keep it as-is
            * if p is absolute, fall back to basename only
        """
        try:
            # Works for both relative ("data/x.csv") and absolute paths
            return p.relative_to(cur_base)
        except ValueError:
            # Not under current_base
            return p if not p.is_absolute() else Path(p.name)

    def _looks_like_dir(raw: str | Path) -> bool:
        s = str(raw)
        # Treat as directory if it ends with a path separator, or has no suffix
        return s.endswith(("/", "\\")) or (Path(s).suffix == "")

    base = Path(dest_base)
    base.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, str]] = []

    for item in items:
        src = Path(item)
        rec: dict[str, str] = {"src": str(src), "status": "pending"}

        rel = _rel_under_base(src)
        dst = base / rel
        rec["dst"] = str(dst)

        # Handle missing sources first (optionally create dir)
        if not src.exists():
            if create_missing_dirs and _looks_like_dir(item):
                try:
                    dst.mkdir(parents=True, exist_ok=True)
                    rec["status"] = "dir_created_missing_src"
                except Exception as e:
                    rec["status"] = "error"
                    rec["error"] = f"{type(e).__name__}: {e}"
            else:
                rec.update(status="missing", error=f"Not found: {src}")
            results.append(rec)
            continue

        try:
            if src.is_dir():
                # Create the directory (no content copy)
                dst.mkdir(parents=True, exist_ok=True)
                rec["status"] = "dir_created"
            else:
                # It's a file -> copy
                dst.parent.mkdir(parents=True, exist_ok=True)
                if dst.exists():
                    if not overwrite:
                        rec["status"] = "skipped_exists"
                        results.append(rec)
                        continue
                    if dst.is_dir():
                        shutil.rmtree(dst)
                    else:
                        dst.unlink()
                shutil.copy2(src, dst)
                rec["status"] = "file_copied"

        except Exception as e:
            rec["status"] = "error"
            rec["error"] = f"{type(e).__name__}: {e}"

        results.append(rec)

    return results


def main():
    # Change to project root directory
    os.chdir(PROJECT_ROOT)

    download_README_template(readme_file="./DCAS template/README_template.md")

    _ = migrate_datasets(
        dataset_json="./dmp.json",
        source_root=PROJECT_ROOT,
        dest_root="./DCAS template",
        zip_threshold=1000,
        overwrite=True,
    )
    programming_language = load_from_env("PROGRAMMING_LANGUAGE", ".cookiecutter")
    code_path = language_dirs.get(programming_language.lower())

    items, _ = get_data_files()  # second value is the mixed list of dirs/files

    print(items)
    copy_data_items(items = items, dest_base = "./DCAS template/data", overwrite=True)

    _ = copy_items(
        items=[
            "./README.md",
            code_path,
            "./docs",
            "./results",
            "./uv.lock",
            "./environment.yml",
            "./requirements.txt",
            "./dmp.json",
        ],
        dest_root="./DCAS template",
        source_root=PROJECT_ROOT,
        base=None,
        overwrite=True,
        ignore_patterns=None,
    )


if __name__ == "__main__":
    main()
