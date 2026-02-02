"""
Backup module - Unified interface for rclone-based backups.

Public API:
    - main()           : CLI entry point
    - push_rclone()    : Push backup to remote
    - pull_rclone()    : Pull backup from remote
    - setup_rclone()   : Configure remote
    - list_remotes()   : List configured remotes
    - delete_remote()  : Remove remote
"""

from .cli import main
from .rclone import push_rclone, pull_rclone, install_rclone
from .remotes import setup_rclone, list_remotes, delete_remote, list_supported_remote_types,set_host_port, _ensure_repo_suffix

__all__ = [
    "main",
    "push_rclone",
    "pull_rclone",
    "setup_rclone",
    "list_remotes",
    "delete_remote",
    "list_supported_remote_types",
    "set_host_port",
    "_ensure_repo_suffix",
    "install_rclone",
]