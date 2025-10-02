# utils/__init__.py# common/__init__.py
"""
Explicit re-exports for helpers that used to live in one big module.
"""

# ---- common.paths ----
from .paths import (
    project_root,
    PROJECT_ROOT,
    from_root,
    check_path_format,
    get_relative_path,
    make_safe_path,
    change_dir,
)

# ---- common.secretstore ----
from .secretstore import (
    _slugify,
    _project_slug,
    _secret_service_name,
    _keyring_get,
    _keyring_set,
    load_from_env,
    save_to_env,
)

# ---- common.prompt ----
from .prompts import (
    ask_yes_no,
    split_multi,
    git_user_info,
    repo_user_info,
    remote_user_info
)

from .env import (
    install_uv,
    create_uv_project,
    write_uv_requires,
    set_packages,
    package_installer,
    exe_to_path,
    remove_from_env,
    exe_to_env,
    is_installed,
    get_version,
    set_program_path,
    run_script,
    ensure_correct_kernel
)


from .constants import (
    ext_map,
    language_dirs,
)

__all__ = (
    # paths
    "project_root",
    "PROJECT_ROOT",
    "from_root",
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
    "install_uv",
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

    # constants
    "ext_map",
    "language_dirs",
)
