import os
import pathlib
import argparse
import subprocess

from .versioning_tools import *
from .jinja_tools import *

@ensure_correct_kernel
def ci_config():
     # Ensure the working directory is the project root
  
    os.chdir(PROJECT_ROOT)

    programming_language = load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter")
    code_repo = load_from_env("CODE_REPO",".cookiecutter")

    if set_git_alis(PROJECT_ROOT):
        generate_ci_configs(programming_language, code_repo, PROJECT_ROOT)
        toggle_ci_files(enable = False, code_repo = code_repo, project_root = PROJECT_ROOT)
        if not git_push(True,f"Setups up CI at {code_repo}"):
            remove_ci_configs()

def parse_version(version_string: str, programming_language: str) -> str:
    programming_language = programming_language.lower()
    if programming_language == "python":
        return version_string.lower().replace("python", "").strip()
    elif programming_language == "r":
        return version_string.lower().replace("r version", "").strip()
    elif programming_language == "matlab":
        return version_string.split()[1]
    else:
        raise ValueError("Unsupported programming_language.")

def generate_ci_configs(programming_language, code_repo, project_root="."):
    programming_language = programming_language.lower()
    code_repo = code_repo.lower()
    version = parse_version(get_version(programming_language), programming_language)

    patch_jinja_templates("j2_templates/ci_templates")
    template_env = set_jinja_templates("j2_templates/ci_templates")

    file_map = {
        "github": pathlib.Path(project_root) / ".github" / "workflows" / "ci.yml",
        "gitlab": pathlib.Path(project_root) / ".gitlab-ci.yml",
        "codeberg": pathlib.Path(project_root) / ".woodpecker.yml",
    }

    output_path = file_map.get(code_repo)
    if not output_path:
        raise ValueError(f"Unsupported code_repo: {code_repo}")
    
    if output_path.exists() or output_path.with_suffix(output_path.suffix + ".disabled").exists():
        return

    template_name = output_path.name + ".j2"
    try:
        template = template_env.get_template(f"{programming_language}/{template_name}")
    except Exception:
        print(f"No CI template available for {programming_language} on {code_repo}")
        return

    rendered = template.render(version=version)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f: 
        f.write(rendered)

    print(f"✅ Created CI config for {programming_language} on {code_repo} using version {version}")

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

@ensure_correct_kernel
def ci_control():
    os.chdir(PROJECT_ROOT)

    parser = argparse.ArgumentParser(description="Enable or disable CI config files.")
    parser.add_argument(
        "--on",
        action="store_true",
        help="Enable CI by renaming .yml.disabled → .yml",
    )
    parser.add_argument(
        "--off",
        action="store_true",
        help="Disable CI by renaming .yml → .yml.disabled",
    )

    args = parser.parse_args()

    programming_language = load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter")
    code_repo = load_from_env("CODE_REPO",".cookiecutter")

    if code_repo.lower() == "none":
        print("No code repository has been setup.")
        return 

    generate_ci_configs(programming_language, code_repo, PROJECT_ROOT)

    if args.on and args.off:
        print("❌ You can't use --on and --off together.")
    elif args.on:
        toggle_ci_files(enable=True, code_repo=code_repo, project_root=PROJECT_ROOT)
    elif args.off:
        toggle_ci_files(enable=False, code_repo=code_repo, project_root=PROJECT_ROOT)
    else:
        print("ℹ️ Use --on or --off to toggle CI.")

if __name__ == "__main__":
    ci_config()