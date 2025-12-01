import argparse
import os

from ..common import PROJECT_ROOT, ensure_correct_kernel, ext_map, language_dirs, load_from_env
from .jinja import set_jinja_templates
from .code import create_script_from_template

template_env = set_jinja_templates("j2/code")


def create_tests(programming_language, scripts_folder=None):
    """
    Create test files for all scripts in the given language folder.

    Parameters
    ----------
    programming_language : str
        Language key used in ext_map and language_dirs (e.g. 'python', 'r').
    scripts_folder : str or None
        Optional path to the folder containing the source scripts.
        If None, the default from language_dirs[programming_language] is used.

    Raises
    ------
    ValueError
        If the language is unsupported, no default folder exists,
        or the resolved scripts_folder does not exist.
    """
    programming_language = programming_language.lower()

    # Determine script extension
    script_ext = ext_map.get(programming_language)
    if script_ext is None:
        raise ValueError(f"Unsupported language: {programming_language}")

    # Resolve scripts folder: parameter overrides default
    if scripts_folder is None:
        scripts_folder = language_dirs.get(programming_language)

    if not scripts_folder:
        raise ValueError(
            f"No scripts folder configured for language: {programming_language}"
        )

    # If the scripts folder does not exist, raise an error (do NOT create it)
    if not os.path.isdir(scripts_folder):
        raise ValueError(
            f"Scripts folder does not exist: {os.path.abspath(scripts_folder)}"
        )

    # Map of where tests should go + test file extension (for the template name)
    tests_map = {
        "python": ("./tests", "py"),
        "r": ("./tests/testthat", "R"),
        "matlab": ("./tests", "m"),
        "stata": ("./tests", "do"),
    }

    if programming_language not in tests_map:
        raise ValueError(f"No test configuration for language: {programming_language}")

    tests_folder, test_ext = tests_map[programming_language]
    template_name = f"test_template.{test_ext}.j2"

    # Ensure test directory exists
    os.makedirs(tests_folder, exist_ok=True)

    # Discover scripts in scripts_folder
    scripts = []
    for fname in os.listdir(scripts_folder):
        # Only consider files with the correct script extension
        if not fname.endswith(f".{script_ext}"):
            continue

        base, _ = os.path.splitext(fname)

        # Skip files that are already tests or special files
        if base.startswith("test_") or base == "__init__":
            continue

        scripts.append(base)

    # Create test files from template for each discovered script
    for base in scripts:
        create_script_from_template(
            programming_language,
            tests_folder,
            template_name,
            f"test_{base}",
            {"base": base},
        )


@ensure_correct_kernel
def main():
    # Set up CLI parser
    parser = argparse.ArgumentParser(description="Create test files for scripts.")
    parser.add_argument(
        "--scripts-folder",
        type=str,
        default=None,
        help="Optional path to the folder containing source scripts. "
             "If omitted, the default language folder is used.",
    )
    parser.add_argument(
        "--language",
        type=str,
        default=None,
        help="Programming language (overrides PROGRAMMING_LANGUAGE env variable).",
    )

    args = parser.parse_args()

    # Ensure working directory is project root
    os.chdir(PROJECT_ROOT)

    # Resolve programming language
    programming_language = (
        args.language or load_from_env("PROGRAMMING_LANGUAGE", ".cookiecutter")
    )

    create_tests(
        programming_language=programming_language,
        scripts_folder=args.scripts_folder,
    )

if __name__ == "__main__":
    main()
