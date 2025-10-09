import os
import pathlib
import re
import subprocess
import sys

# ---- Secret manager (optional) ----
try:
    import keyring
    from keyring.errors import KeyringError, NoKeyringError

    _HAS_KEYRING = True
except Exception:
    keyring = None
    KeyringError = NoKeyringError = Exception  # type: ignore
    _HAS_KEYRING = False

from .base import PROJECT_ROOT
from .paths import check_path_format

if sys.version_info < (3, 11):
    import toml

    tomli_w = None
else:
    import tomli_w
    import tomllib as toml

from dotenv import dotenv_values, load_dotenv


# --- Helpers for secret management ---
def _slugify(s: str | None) -> str:
    if not s:
        return "default"
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def _project_slug() -> str:
    # 1) explicit override
    s = os.getenv("PROJECT_SLUG") or os.getenv("RT_PROJECT_SLUG")
    if s:
        return _slugify(s)

    # 2) try git repo name
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        if r.returncode == 0:
            return _slugify(pathlib.Path(r.stdout.strip()).name)
    except Exception:
        pass

    # 3) fallback: project folder name
    return _slugify(PROJECT_ROOT.name)


def _secret_service_name() -> str:
    base = os.getenv("SECRET_SERVICE_NAME", "research-template")
    return f"{base}::{_project_slug()}"  # <-- service name is per project


def _keyring_get(name: str) -> str | None:
    """Try project-scoped key first, then global key."""
    if not _HAS_KEYRING:
        return None
    for k in (f"{_project_slug()}:{name}", name):
        try:
            v = keyring.get_password(_secret_service_name(), k)
            if v:
                return v
        except (KeyringError, NoKeyringError):
            return None
    return None


def _keyring_set(name: str, value: str) -> bool:
    """Write project-scoped key. Optionally also write a global alias."""
    if not _HAS_KEYRING:
        return False
    try:
        keyring.set_password(_secret_service_name(), f"{_project_slug()}:{name}", value)
        if os.getenv("SECRET_WRITE_GLOBAL_ALIAS", "").lower() in ("1", "true", "yes"):
            keyring.set_password(_secret_service_name(), name, value)
        return True
    except (KeyringError, NoKeyringError):
        return False


def load_from_env(
    env_name: str,
    env_file: str = ".env",
    toml_file: str = "pyproject.toml",
    use_keyring: bool = False,
) -> str | None:
    """
    Loads a value in this priority order:
      1) keyring / OS secret manager (if enabled and available)
      2) already-set environment variable (os.environ)
      3) .env file (exact path or PROJECT_ROOT/<name>)
      4) [tool.<section>] in TOML fallback (pyproject.toml)
    Returns None if not found.
    """
    if sys.version_info < (3, 11):
        open_mode = ("r", "utf-8")
    else:
        open_mode = ("rb", None)

    name_strip = env_name.strip()
    name_upper = name_strip.upper()

    # 1) Secret manager (keyring)
    if use_keyring:
        val = _keyring_get(name_upper)
        if val:
            return check_path_format(val)

    # 2) .env path resolve
    env_path = pathlib.Path(env_file)
    if not env_path.is_absolute():
        env_path = PROJECT_ROOT / env_path.name

    if env_path.exists():
        env_values = dotenv_values(env_path)
        if name_upper in env_values and env_values[name_upper]:
            return check_path_format(env_values[name_upper])  # direct read is faster

        # Load into process env and retry
        load_dotenv(env_path, override=True)
        val = os.getenv(name_upper)
        if val:
            return check_path_format(val)

    # If explicitly ".env", DO NOT fallback
    if env_path.name == ".env":
        return None

    # 4) TOML fallback
    toml_section = env_path.stem.lstrip(".")  # e.g. ".cookiecutter" -> "cookiecutter"
    toml_path = pathlib.Path(toml_file)
    if not toml_path.is_absolute():
        toml_path = PROJECT_ROOT / toml_path.name

    if toml_path.exists():
        try:
            with open(toml_path, open_mode[0], encoding=open_mode[1]) as f:
                config = toml.load(f)
            return check_path_format(config.get("tool", {}).get(toml_section, {}).get(name_strip))
        except Exception as e:
            print(f"⚠️ Could not read {toml_path}: {e}")

    return None


def save_to_env(
    env_var: str,
    env_name: str,
    env_file: str = ".env",
    toml_file: str = "pyproject.toml",
    use_keyring: bool = False,
    also_write_file_fallback: bool = True,
) -> None:
    """
    Saves/updates a single secret.
    Default behavior:
      - Try to store in OS secret manager (keyring).
      - If unavailable or disabled, fall back to .env or TOML (original behavior).
    Set also_write_file_fallback=False to avoid file writes when keyring succeeds.
    """

    def sanitize_input(s: str) -> str:
        return s.encode("utf-8", errors="surrogatepass").decode("utf-8", errors="ignore")

    if sys.version_info < (3, 11):
        load_toml = toml.load
        dump_toml = toml.dump
        read_mode = ("r", "utf-8")
        write_mode = ("w", "utf-8")
    else:

        def load_toml(f):
            return toml.load(f)

        def dump_toml(d, f):
            f.write(tomli_w.dumps(d))  # type: ignore

        read_mode = ("rb", None)
        write_mode = ("w", "utf-8")

    if env_var is None:
        return

    name_strip = env_name.strip()
    name_upper = name_strip.upper()
    env_var = check_path_format(env_var)
    env_var = sanitize_input(env_var)

    # 1) Try secret manager first
    wrote_keyring = False
    if use_keyring:
        wrote_keyring = _keyring_set(name_upper, env_var)

    # If keyring worked and we don't want file backup, we're done.
    if wrote_keyring and not also_write_file_fallback:
        return

    # 2) File-based fallbacks (your original logic)
    env_path = pathlib.Path(env_file)
    if not env_path.is_absolute():
        env_path = PROJECT_ROOT / env_path.name

    # Always write to .env if explicitly requested or if it already exists
    if env_path.name == ".env" or env_path.exists():
        lines = []
        if env_path.exists():
            with open(env_path, encoding="utf-8") as f:
                lines = f.readlines()

        updated = False
        for i, line in enumerate(lines):
            if "=" in line:
                name, _ = line.split("=", 1)
                if name.strip().upper() == name_upper:
                    lines[i] = f"{name_upper}={env_var}\n"
                    updated = True
                    break
        if not updated:
            lines.append(f"{name_upper}={env_var}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return

    # Fallback: write to [tool.<section>] in TOML
    toml_section = env_path.stem.lstrip(".")
    toml_path = pathlib.Path(toml_file)
    if not toml_path.is_absolute():
        toml_path = PROJECT_ROOT / toml_path.name

    config = {}
    if toml_path.exists():
        try:
            with open(toml_path, read_mode[0], encoding=read_mode[1]) as f:
                config = load_toml(f)
        except Exception as e:
            print(f"⚠️ Could not parse TOML: {e}")
            return

    config.setdefault("tool", {})
    config["tool"].setdefault(toml_section, {})
    config["tool"][toml_section][name_strip] = env_var

    with open(toml_path, write_mode[0], encoding=write_mode[1]) as f:
        dump_toml(config, f)
