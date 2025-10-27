import json
import os
import sys

import pathspec
from pathspec.patterns import GitWildMatchPattern

if sys.version_info < (3, 11):
    import toml

    tomli_w = None
    OPEN_MODE = ("r", "utf-8")
    load_toml = toml.load
    dump_toml = toml.dump
    READ_MODE = ("r", "utf-8")
    WRITE_MODE = ("w", "utf-8")
else:
    import tomli_w
    import tomllib as toml

    OPEN_MODE = ("rb", None)

    def load_toml(f):
        return toml.load(f)

    def dump_toml(d, f):
        f.write(tomli_w.dumps(d))

    READ_MODE = ("rb", None)
    WRITE_MODE = ("w", "utf-8")

from .base import PROJECT_ROOT


def toml_ignore(
    folder: str = None,
    ignore_filename: str = None,
    tool_name: str = None,
    toml_path: str = "pyproject.toml",
    toml_key: str = "patterns",
):
    """
    Load ignore patterns from a file or from a TOML tool config section.

    Returns
    -------
        Tuple[PathSpec | None, List[str]]: A PathSpec matcher and raw pattern list
    """
    if not folder:
        folder = str(PROJECT_ROOT)

    ignore_path = (
        ignore_filename
        if os.path.isabs(ignore_filename or "")
        else os.path.join(folder, ignore_filename or "")
    )

    if ignore_filename and os.path.exists(ignore_path):
        with open(ignore_path, encoding="utf-8") as f:
            patterns = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        spec = pathspec.PathSpec.from_lines(GitWildMatchPattern, patterns)
        return spec, patterns

    toml_full_path = toml_path if os.path.isabs(toml_path) else os.path.join(folder, toml_path)
    if os.path.exists(toml_full_path):
        try:
            with open(toml_full_path, OPEN_MODE[0], encoding=OPEN_MODE[1]) as f:
                config = toml.load(f)
            patterns = config.get("tool", {}).get(tool_name) or config.get(tool_name)
            if isinstance(patterns, dict):
                patterns = patterns.get(toml_key, [])
            if isinstance(patterns, list):
                patterns = [p.strip() for p in patterns if isinstance(p, str)]
                spec = pathspec.PathSpec.from_lines(GitWildMatchPattern, patterns)
                return spec, patterns
        except Exception as e:
            print(f"❌ Error reading [{tool_name}] from {toml_full_path}: {e}")

    return None, []


def read_toml(
    folder: str = None,
    json_filename: str = None,
    tool_name: str = None,
    toml_path: str = "pyproject.toml",
):
    """
    Load a dictionary from a JSON file, or fall back to a tool-specific section
    in a TOML file (either under [tool.<tool_name>] or [<tool_name>]).

    Args:
        folder (str): Directory containing config files.
        json_filename (str): Name of the JSON file to load (e.g., 'platform_rules.json').
        tool_name (str): Tool name to look for in TOML (e.g., 'platform_rules').
        toml_path (str): Name of the TOML file to read from.

    Returns
    -------
        dict | None: Dictionary loaded from JSON or TOML, or None if both fail.
    """
    if not folder:
        folder = str(PROJECT_ROOT)

    json_path = (
        json_filename
        if os.path.isabs(json_filename or "")
        else os.path.join(folder, json_filename or "")
    )
    if os.path.exists(json_path):
        try:
            with open(json_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading {json_filename}: {e}")

    toml_path_full = toml_path if os.path.isabs(toml_path) else os.path.join(folder, toml_path)
    if os.path.exists(toml_path_full):
        try:
            with open(toml_path_full, OPEN_MODE[0], encoding=OPEN_MODE[1]) as f:
                config = toml.load(f)
            return config.get("tool", {}).get(tool_name) or config.get(tool_name)
        except Exception as e:
            print(f"Error reading [{tool_name}] from {toml_path_full}: {e}")

    return None


def write_toml(
    data: dict = None,
    folder: str = None,
    json_filename: str = None,
    tool_name: str = None,
    toml_path: str = "pyproject.toml",
):
    if not folder:
        folder = str(PROJECT_ROOT)
    if not tool_name:
        raise ValueError("tool_name is required")

    toml_file_path = toml_path if os.path.isabs(toml_path) else os.path.join(folder, toml_path)
    json_file_path = (
        json_filename
        if json_filename and os.path.isabs(json_filename)
        else os.path.join(folder, json_filename)
        if json_filename
        else None
    )

    if data is None and json_file_path and os.path.exists(json_file_path):
        try:
            with open(json_file_path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ Failed to read {json_filename}: {e}")

    if not isinstance(data, dict):
        print("❌ No valid dictionary to write.")
        return

    toml_data = {}
    if os.path.exists(toml_file_path):
        with open(toml_file_path, READ_MODE[0], encoding=READ_MODE[1]) as f:
            try:
                toml_data = load_toml(f)
            except Exception as e:
                print(f"❌ Failed to parse existing TOML: {e}")
                return

    if "tool" not in toml_data:
        toml_data["tool"] = {}
    if tool_name not in toml_data["tool"] or not isinstance(toml_data["tool"][tool_name], dict):
        toml_data["tool"][tool_name] = {}

    toml_data["tool"][tool_name].update(data)

    with open(toml_file_path, WRITE_MODE[0], encoding=WRITE_MODE[1]) as f:
        dump_toml(toml_data, f)
