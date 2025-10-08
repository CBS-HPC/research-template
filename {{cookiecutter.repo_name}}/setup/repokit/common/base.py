# repokit/common/base.py  (stdlib only)
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

BASE_DEPS = [
    "python-dotenv>=1.0",
    "pathspec>=0.12",
    'toml>=0.10 ; python_version < "3.11"',
    'tomli-w>=1.0 ; python_version >= "3.11"',
]


def install_uv():
    try:
        import uv  # noqa: F401

        return True
    except ImportError:
        try:
            print("Installing 'uv' package into current Python environment...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "uv"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            print("'uv' installed successfully.")

            import uv  # noqa: F401

            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to install 'uv' via pip: {e}")
            return False


def install_base_deps(deps: list[str] = BASE_DEPS) -> None:
    # best-effort installer; fine to call early from project_setup.py
    if install_uv():
        try:
            env = os.environ.copy()
            env["UV_LINK_MODE"] = "copy"
            subprocess.run(
                [sys.executable, "-m", "uv", "pip", "install", "--system", *deps],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
            )
            return
        except Exception:
            pass
    # fallback to pip
    for dep in deps:
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", dep],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            # keep going: some users may be offline; libs will be required lazily later
            pass


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent


# Convenience constant + helper
PROJECT_ROOT = project_root()
