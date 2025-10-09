import os
import pathlib
import platform
from contextlib import contextmanager

from .base import PROJECT_ROOT


def from_root(*parts: str | os.PathLike) -> pathlib.Path:
    """Join paths relative to the detected project root."""
    return PROJECT_ROOT.joinpath(*map(str, parts))


def check_path_format(path, project_root=None):
    if not path:
        return path

    if any(sep in path for sep in ["/", "\\", ":"]) and os.path.exists(
        path
    ):  # ":" for Windows drive letters
        # Set default project root if not provided
        if project_root is None:
            project_root = PROJECT_ROOT

        # Resolve both paths fully
        project_root = pathlib.Path(project_root).resolve()

        # Now adjust slashes depending on platform
        system_name = platform.system()
        if system_name == "Windows":
            path = r"{}".format(path.replace("/", "\\"))
            # path = r"{}".format(path.replace("\\", r"\\"))
        else:  # Linux/macOS
            # path = r"{}".format(path.replace("\\", r"\\"))
            path = r"{}".format(path.replace("\\", "/"))

    return path


def get_relative_path(target_path):
    if target_path:
        current_dir = os.getcwd()
        absolute_target_path = os.path.abspath(target_path)

        # Check if target_path is a subpath of current_dir
        if os.path.commonpath([current_dir, absolute_target_path]) == current_dir:
            # Create a relative path if it is a subpath
            relative_path = os.path.relpath(absolute_target_path, current_dir)

            if relative_path:
                return relative_path
    return target_path


def make_safe_path(path: str, language: str = "python") -> str:
    """
    Convert a file path to a language-safe format for Python, R, MATLAB, or Stata.

    Args:
        path (str): The input file path.
        language (str): One of 'python', 'r', 'matlab', 'stata'.

    Returns
    -------
        str: A properly formatted path string.
    """
    language = language.lower()
    path = os.path.abspath(path)

    is_windows = platform.system() == "Windows"

    # Standard form: forward slashes for everything except MATLAB on Windows
    normalized = path.replace("\\", "/") if is_windows else path

    if language == "python":
        return normalized  # Python is tolerant of forward slashes

    elif language == "r":
        return normalized  # R is happy with forward slashes even on Windows

    elif language == "matlab":
        # MATLAB prefers backslashes on Windows, forward slashes on Linux/macOS
        matlab_path = path.replace("/", "\\") if is_windows else path
        return f"'{matlab_path}'"  # Single quotes for MATLAB string

    elif language == "stata":
        return f'"{normalized}"'  # Stata do-files expect double-quoted paths

    else:
        raise ValueError(f"Unsupported language: {language}")


@contextmanager
def change_dir(destination):
    cur_dir = os.getcwd()
    destination = str(PROJECT_ROOT / pathlib.Path(destination))
    try:
        os.chdir(destination)
        yield
    finally:
        os.chdir(cur_dir)
