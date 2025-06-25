import os
from subprocess import DEVNULL
import sys
import pathlib
import json

from .general_tools import package_installer

install_packages = ['python-dotenv','pathspec']

if sys.version_info < (3, 11):
    install_packages.append('toml')
else:
    install_packages.append('tomli-w')

package_installer(required_libraries = install_packages)

from dotenv import dotenv_values, load_dotenv

if sys.version_info < (3, 11):
    import toml
else:
    import tomllib as toml
    import tomli_w

import pathspec

def read_toml_ignore(folder: str = None, ignore_filename: str = None, tool_name: str = None, toml_path: str = "pyproject.toml", toml_key: str = "patterns"):
    """
    Load ignore patterns from a file or from a TOML tool config section.

    Returns:
        Tuple[PathSpec | None, List[str]]: A PathSpec matcher and raw pattern list
    """
    if sys.version_info < (3, 11):
        open_mode = ("r", "utf-8")
    else:
        open_mode = ("rb", None)

    if not folder:
        folder = str(pathlib.Path(__file__).resolve().parent.parent.parent)

    ignore_path = ignore_filename if os.path.isabs(ignore_filename or "") else os.path.join(folder, ignore_filename or "")

    if ignore_filename and os.path.exists(ignore_path):
        with open(ignore_path, "r", encoding="utf-8") as f:
            patterns = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)
        return spec, patterns

    toml_full_path = toml_path if os.path.isabs(toml_path) else os.path.join(folder, toml_path)
    if os.path.exists(toml_full_path):
        try:
            with open(toml_full_path, open_mode[0], encoding=open_mode[1]) as f:
                config = toml.load(f)
            patterns = config.get("tool", {}).get(tool_name) or config.get(tool_name)
            if isinstance(patterns, dict):
                patterns = patterns.get(toml_key, [])
            if isinstance(patterns, list):
                patterns = [p.strip() for p in patterns if isinstance(p, str)]
                spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)
                return spec, patterns
        except Exception as e:
            print(f"❌ Error reading [{tool_name}] from {toml_full_path}: {e}")

    return None, []

def read_toml_json(folder: str = None, json_filename: str = None, tool_name: str = None, toml_path: str = "pyproject.toml"):
    """
    Load a dictionary from a JSON file, or fall back to a tool-specific section
    in a TOML file (either under [tool.<tool_name>] or [<tool_name>]).

    Args:
        folder (str): Directory containing config files.
        json_filename (str): Name of the JSON file to load (e.g., 'platform_rules.json').
        tool_name (str): Tool name to look for in TOML (e.g., 'platform_rules').
        toml_path (str): Name of the TOML file to read from.

    Returns:
        dict | None: Dictionary loaded from JSON or TOML, or None if both fail.
    """
    
    if sys.version_info < (3, 11):
        open_mode = ("r", "utf-8")
    else:
        open_mode = ("rb", None)

    if not folder:
        folder = str(pathlib.Path(__file__).resolve().parent.parent.parent)

    json_path = json_filename if os.path.isabs(json_filename or "") else os.path.join(folder, json_filename or "")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading {json_filename}: {e}")

    toml_path_full = toml_path if os.path.isabs(toml_path) else os.path.join(folder, toml_path)
    if os.path.exists(toml_path_full):
        try:
            with open(toml_path_full, open_mode[0], encoding=open_mode[1]) as f:
                config = toml.load(f)
            return config.get("tool", {}).get(tool_name) or config.get(tool_name)
        except Exception as e:
            print(f"Error reading [{tool_name}] from {toml_path_full}: {e}")

    return None

def write_toml_json(data: dict = None, folder: str = None, json_filename: str = None, tool_name: str = None, toml_path: str = "pyproject.toml"):
        if sys.version_info < (3, 11):
            load_toml = toml.load
            dump_toml = toml.dump
            open_read = ("r", "utf-8")
            open_write = ("w", "utf-8")
        else:
            def load_toml(f): return toml.load(f)
            def dump_toml(d, f): f.write(tomli_w.dumps(d))
            open_read = ("rb", None)
            open_write = ("w", "utf-8")

        if not folder:
            folder = str(pathlib.Path(__file__).resolve().parent.parent.parent)
        if not tool_name:
            raise ValueError("tool_name is required")

        toml_file_path = toml_path if os.path.isabs(toml_path) else os.path.join(folder, toml_path)
        json_file_path = json_filename if json_filename and os.path.isabs(json_filename) else os.path.join(folder, json_filename) if json_filename else None

        if data is None and json_file_path and os.path.exists(json_file_path):
            try:
                with open(json_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"❌ Failed to read {json_filename}: {e}")

        if not isinstance(data, dict):
            print("❌ No valid dictionary to write.")
            return

        toml_data = {}
        if os.path.exists(toml_file_path):
            with open(toml_file_path, open_read[0], encoding=open_read[1]) as f:
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

        with open(toml_file_path, open_write[0], encoding=open_write[1]) as f:
            dump_toml(toml_data, f)
