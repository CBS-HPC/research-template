# utils/__init__.py# common/__init__.py
"""
Explicit re-exports for helpers that used to live in one big module.
"""

# ---- common.bases ----
from .base import (
    PROJECT_ROOT,
    install_uv,
    project_root,
)
from .constants import (
    ext_map,
    language_dirs,
)
from .env import (
    create_uv_project,
    ensure_correct_kernel,
    exe_to_env,
    exe_to_path,
    get_version,
    is_installed,
    package_installer,
    remove_from_env,
    run_script,
    set_packages,
    set_program_path,
    write_uv_requires,
)

# ---- common.paths ----
from .paths import (
    change_dir,
    check_path_format,
    get_relative_path,
    make_safe_path,
)

# ---- common.prompt ----
from .prompts import ask_yes_no, git_user_info, remote_user_info, repo_user_info, split_multi

# ---- common.secretstore ----
from .secretstore import (
    _keyring_get,
    _keyring_set,
    _project_slug,
    _secret_service_name,
    _slugify,
    load_from_env,
    save_to_env,
)
from .tomlutils import read_toml, toml_ignore, write_toml

__all__ = (
    # base
    "project_root",
    "PROJECT_ROOT",
    "install_uv",
    # paths
    "check_path_format",
    "get_relative_path",
    "make_safe_path",
    "change_dir",
    # secretstore
    "_slugify",
    "_project_slug",
    "_secret_service_name",
    "_keyring_get",
    "_keyring_set",
    "load_from_env",
    "save_to_env",
    # prompts
    "ask_yes_no",
    "split_multi",
    "git_user_info",
    "repo_user_info",
    "remote_user_info",
    # env (topic module)
    "create_uv_project",
    "write_uv_requires",
    "set_packages",
    "package_installer",
    "exe_to_path",
    "remove_from_env",
    "exe_to_env",
    "is_installed",
    "get_version",
    "set_program_path",
    "run_script",
    "ensure_correct_kernel",
    # tomlutils
    "toml_ignore",
    "read_toml",
    "write_toml",
    # constants
    "ext_map",
    "language_dirs",
)
