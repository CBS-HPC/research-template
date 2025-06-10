import pathlib
import argparse
import subprocess

from .versioning_tools import *

#@ensure_correct_kernel
def ci_config():
     # Ensure the working directory is the project root
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)

    programming_language = load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter")
    code_repo = load_from_env("CODE_REPO",".cookiecutter")

    if set_git_alis(project_root):
        generate_ci_configs(programming_language, code_repo, project_root)
        toggle_ci_files(enable = False, code_repo = code_repo, project_root = project_root)
        if not git_push(True,f"Setups up CI at {code_repo}"):
            remove_ci_configs()


# -------- CI Generator Dispatcher --------

def generate_ci_configs(programming_language: str, code_repo: str, project_root: str = "."):
    """
    Generate a CI configuration file for a given language and code hosting platform.
    """
    def parse_version(version_string: str, programming_language: str) -> str:
        programming_language = programming_language.lower()
        if programming_language == "python":
            return version_string.lower().replace("python", "").strip()
        elif programming_language == "r":
            return version_string.lower().replace("r version", "").strip()
        elif programming_language == "matlab":
            return version_string.split()[1]  # e.g., "9.11.0.2022996"
        else:
            raise ValueError("Unsupported programming_language.")

    def _ci_for_python(version: str):
        return {
          "github": f"""{% raw %}\
name: Python CI

on: [push, pull_request]

jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    runs-on: ${{{{ matrix.os }}}}
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '{version}'
      - run: pip install -r requirements.txt
      - run: pytest
{% endraw %}""",
            "gitlab": f"""{% raw %}\
image: python:{version}

stages:
  - test

run-tests:
  stage: test
  script:
    - pip install -r requirements.txt
    - pytest
{% endraw %}""",
            "codeberg": f"""{% raw %}\
pipeline:
  test:
    image: python:{version}
    commands:
      - pip install -r requirements.txt
      - pytest
{% endraw %}"""
        }

    def _ci_for_r(version: str):
        return {
          "github": f"""{% raw %}\
name: R CI

on: [push, pull_request]

jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    runs-on: ${{{{ matrix.os }}}}
    steps:
      - uses: actions/checkout@v3
      - uses: r-lib/actions/setup-r@v2
        with:
          r-version: '{version}'
      - name: Install renv
        run: Rscript -e 'install.packages("renv")'
      - name: Restore or install dependencies
        run: |
          if (file.exists("R/renv.lock")) {{
            renv::restore(project = "R")
          }} else {{
            install.packages("testthat")
          }}
      - name: Run tests
        run: Rscript -e 'testthat::test_dir("tests/testthat")'
{% endraw %}""",
            "gitlab": f"""{% raw %}\
image: rocker/r-ver:{version}

stages:
  - test

run-tests:
  stage: test
  script:
    - Rscript -e 'install.packages("renv")'
    - |
      if [ -f "R/renv.lock" ]; then
        Rscript -e 'renv::restore(project = "R")'
      else
        Rscript -e 'install.packages("testthat")'
      fi
    - Rscript -e 'testthat::test_dir("tests/testthat")'
{% endraw %}""",
            "codeberg": f"""{% raw %}\
pipeline:
  test:
    image: rocker/r-ver:{version}
    commands:
      - Rscript -e 'install.packages("renv")'
      - |
        if [ -f "R/renv.lock" ]; then
          Rscript -e 'renv::restore(project = "R")'
        else
          Rscript -e 'install.packages("testthat")'
        fi
      - Rscript -e 'testthat::test_dir("tests/testthat")'
{% endraw %}"""
        }
    
    def _ci_for_matlab(version: str):
        return {
            "github": f"""{% raw %}\
    name: MATLAB CI

    on: [push, pull_request]

    jobs:
      test:
        strategy:
          matrix:
            os: [ubuntu-latest, windows-latest, macos-latest]
        runs-on: ${{{{ matrix.os }}}}
        steps:
          - uses: actions/checkout@v3
          - uses: matlab-actions/setup-matlab@v2
            with:
              matlab-token: ${{{{ secrets.MATLAB_TOKEN }}}}
          - uses: matlab-actions/run-tests@v2
            with:
              source-folder: src
              test-folder: tests
    {% endraw %}""",
            "gitlab": f"""{% raw %}\
    # GitLab CI configuration for MATLAB using official guidance

    .matlab_defaults:
      image:
        name: mathworks/matlab:{version}
        entrypoint: [""]
      variables:
        MLM_LICENSE_FILE: 27000@MyLicenseServer  # Update with your actual license server

    run-tests:
      extends: .matlab_defaults
      stage: test
      script:
        - matlab -batch "results = runtests('IncludeSubfolders', true); assertSuccess(results);"
    {% endraw %}""",
            "codeberg": f"""{% raw %}\
    {% endraw %}"""
        }

    programming_language = programming_language.lower()
    code_repo = code_repo.lower()

    # You must define get_version() elsewhere
    version = parse_version(get_version(programming_language), programming_language)

    template_map = {
        "python": _ci_for_python,
        "r": _ci_for_r,
        "matlab": _ci_for_matlab
    }

    if programming_language not in template_map:
        raise ValueError(f"Unsupported language: {programming_language}")
  
    file_map = {
        "github": pathlib.Path(project_root) / ".github" / "workflows" / "ci.yml",
        "gitlab": pathlib.Path(project_root) / ".gitlab-ci.yml",
        "codeberg": pathlib.Path(project_root) / ".woodpecker.yml",
      }
    
    if code_repo not in file_map:
        print(f"Unsupported code_repo: {code_repo}")
        return 
    templates = template_map[programming_language](version)  
    template = templates[code_repo]

    if not template:
        print(f"CI for {programming_language} is not supported on {code_repo}")
        return 

    path = file_map[code_repo]
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        f.write(template)

    print(f"✅ CI config created for {programming_language} on {code_repo} using version {version}")

def remove_ci_configs(code_repo: str = None, project_root: str = "."):
    """
    Remove CI configuration files created by generate_ci_configs,
    including both enabled (.yml) and disabled (.yml.disabled) versions.

    Parameters:
        code_repo (str): 'github', 'gitlab', 'codeberg', or 'all'
        project_root (str): Root path to the project directory
    """
    code_repo = code_repo.lower() if code_repo else "all"
    project_root = pathlib.Path(project_root)

    ci_files = {
        "github": project_root / pathlib.Path(".github/workflows/ci.yml"),
        "gitlab": project_root / pathlib.Path(".gitlab-ci.yml"),
        "codeberg": project_root / pathlib.Path(".woodpecker.yml"),
    }
    if code_repo == "all":
        targets = ci_files.items()
    elif code_repo in ci_files:
        targets = [(code_repo, ci_files[code_repo])]
    else:
        raise ValueError(f"Unsupported code_repo: {code_repo}")

    for name, path in targets:
        for variant in [path, path.with_suffix(path.suffix + ".disabled")]:
            if variant.exists():
                try:
                    variant.unlink()
                    print(f"🗑️  Removed {name} CI config: {variant}")
                except Exception as e:
                    print(f"⚠️ Failed to remove {variant}: {e}")

        # Optional: Clean up empty GitHub workflow folder
        if name == "github":
            workflow_dir = path.parent
            try:
                if workflow_dir.exists() and not any(workflow_dir.iterdir()):
                    workflow_dir.rmdir()
                    print("🧹 Removed empty .github/workflows/ folder")
            except Exception as e:
                print(f"⚠️ Could not remove workflows folder: {e}")

def toggle_ci_files(enable: bool = True, code_repo: str = "all", project_root: str = "."):
    """
    Enables or disables CI by renaming .yml files (to .disabled) for GitHub, GitLab, and Codeberg.
    
    Parameters:
        enable (bool): True to enable CI, False to disable it.
        code_repo (str): 'github', 'gitlab', 'codeberg', or 'all'.
        project_root (str): project_root directory of the project.
    """
    code_repo = code_repo.lower()

    ci_files = {
        "github": project_root / pathlib.Path(".github/workflows/ci.yml"),
        "gitlab": project_root / pathlib.Path(".gitlab-ci.yml"),
        "codeberg": project_root / pathlib.Path(".woodpecker.yml"),
    }

    if code_repo == "all":
        targets = ci_files
    else:
        if code_repo not in ci_files:
            raise ValueError(f"Unsupported code_repo: {code_repo}")
        targets = {code_repo: ci_files[code_repo]}

    for name, path in targets.items():
        if enable:
            disabled = path.with_suffix(path.suffix + ".disabled")
            if disabled.exists():
                disabled.rename(path)
                print(f"✅ Re-enabled CI for {name}")
            else:
                print(f"ℹ️  CI for {name} is already enabled or missing.")
        else:
            if path.exists():
                disabled = path.with_suffix(path.suffix + ".disabled")
                path.rename(disabled)
                print(f"🚫 Disabled CI for {name}")
            else:
                print(f"ℹ️  CI for {name} is already disabled or not found.")

def set_git_alis(project_root: str = "."):

    git_folder = project_root/ pathlib.Path(".git")

    # Git alias setup (only if .git exists)
    if git_folder.exists() and git_folder.is_dir():
        try:
            subprocess.run(
                [
                    "git", "config", "--global",
                    "alias.commit-skip",
                    "!f() { git commit -m \"$1 [skip ci]\"; }; f"
                ],
                check=True
            )
            print("✅ Git alias 'commit-skip' added.")
            return True
        except Exception as e:
            print(f"⚠️ Could not add Git alias: {e}")
            return False
    else:
        print("ℹ️ Skipped Git alias setup: .git folder not found in project root.")
        return False

#@ensure_correct_kernel
def ci_control():
 
  # Ensure we're in the project root
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)

    parser = argparse.ArgumentParser(description="Enable or disable CI config files.")
    parser.add_argument(
        "--enable",
        action="store_true",
        help="Enable CI by renaming .yml.disabled → .yml",
    )
    parser.add_argument(
        "--disable",
        action="store_true",
        help="Disable CI by renaming .yml → .yml.disabled",
    )

    args = parser.parse_args()

    code_repo = load_from_env("CODE_REPO",".cookiecutter")

    if args.enable and args.disable:
        print("❌ You can't use --enable and --disable together.")
    elif args.enable:
        toggle_ci_files(enable=True, code_repo=code_repo, project_root=project_root)
    elif args.disable:
        toggle_ci_files(enable=False, code_repo=code_repo, project_root=project_root)
    else:
        print("ℹ️ Use --enable or --disable to toggle CI.")


if __name__ == "__main__":
    ci_config()