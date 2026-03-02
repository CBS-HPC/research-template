import pathlib
import shutil
import subprocess
import sys
import os
import stat
from typing import Any

try:
    import tomllib  # py311+
except Exception:  # pragma: no cover
    tomllib = None


_DEFAULT_POLICY: dict[str, Any] = {
    "source": "local",
    "github_base": "https://github.com/CBS-HPC",
    "repokit_common_version": "0.1",
    "repokit_backup_version": "0.1",
    "repokit_dmp_version": "0.1",
    "repokit_version": "0.1",
}

_PKG_META: dict[str, dict[str, str]] = {
    "repokit-common": {"repo": "repokit-common", "wheel": "repokit_common"},
    "repokit-backup": {"repo": "repokit-backup", "wheel": "repokit_backup"},
    "repokit-dmp": {"repo": "repokit-dmp", "wheel": "repokit_dmp"},
    "repokit": {"repo": "repokit", "wheel": "repokit"},
}

_REPOKIT_GIT_URL = "https://github.com/CBS-HPC/repokit.git"


def load_install_policy(project_dir: pathlib.Path) -> dict[str, Any]:
    policy = dict(_DEFAULT_POLICY)
    pyproject = project_dir / "pyproject.toml"
    if not pyproject.exists() or tomllib is None:
        return policy
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        policy.update(((data.get("tool", {}) or {}).get("repokit_install", {}) or {}))
    except Exception:
        pass
    source = str(policy.get("source", "local")).strip().lower()
    if source not in {"local", "github", "pypi", "auto"}:
        source = "local"
    policy["source"] = source
    return policy


def source_order(source: str) -> list[str]:
    if source == "auto":
        return ["local", "github", "pypi"]
    return [source]


def local_editable_path(setup_dir: pathlib.Path, package_name: str) -> pathlib.Path:
    repokit_dir = setup_dir / "repokit"
    if package_name == "repokit":
        return repokit_dir
    meta = _PKG_META[package_name]
    return repokit_dir / "external" / meta["repo"]


def local_wheel_path(setup_dir: pathlib.Path, package_name: str) -> pathlib.Path | None:
    repokit_dir = setup_dir / "repokit"
    if package_name == "repokit":
        dist_dir = repokit_dir / "dist"
    else:
        dist_dir = repokit_dir / "external" / _PKG_META[package_name]["repo"] / "dist"
    if not dist_dir.exists():
        return None
    wheels = sorted(dist_dir.glob("*.whl"))
    return wheels[-1] if wheels else None


def ensure_local_repokit_sources(setup_dir: pathlib.Path) -> bool:
    repokit_dir = setup_dir / "repokit"
    repokit_common_path = repokit_dir / "external" / "repokit-common" / "src" / "repokit_common"
    if repokit_common_path.exists():
        return True
    if not shutil.which("git"):
        return False
    if repokit_dir.exists():
        try:
            if not any(repokit_dir.iterdir()):
                shutil.rmtree(repokit_dir, ignore_errors=True)
        except OSError:
            pass
    if not repokit_dir.exists():
        subprocess.run(
            ["git", "clone", _REPOKIT_GIT_URL, str(repokit_dir)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    if repokit_dir.exists():
        subprocess.run(
            ["git", "-C", str(repokit_dir), "submodule", "update", "--init", "--recursive"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    return repokit_common_path.exists()


def _on_rm_error(func, path, exc_info):
    try:
        os.chmod(path, stat.S_IWRITE)
    except Exception:
        pass
    func(path)


def remove_embedded_git_dirs(setup_dir: pathlib.Path) -> None:
    repokit_dir = setup_dir / "repokit"
    packages = [
        repokit_dir,
        repokit_dir / "external" / "repokit-common",
        repokit_dir / "external" / "repokit-backup",
        repokit_dir / "external" / "repokit-dmp",
    ]
    for package_path in packages:
        git_dir = package_path / ".git"
        if git_dir.exists() and git_dir.is_dir():
            shutil.rmtree(git_dir, onerror=_on_rm_error)


def github_wheel_url(policy: dict[str, Any], package_name: str) -> str:
    meta = _PKG_META[package_name]
    version_key = meta["wheel"] + "_version"
    version = str(policy.get(version_key, _DEFAULT_POLICY.get(version_key, "0.1"))).strip()
    base = str(policy.get("github_base", _DEFAULT_POLICY["github_base"])).rstrip("/")
    return f"{base}/{meta['repo']}/raw/main/dist/{meta['wheel']}-{version}-py3-none-any.whl"


def pypi_spec(policy: dict[str, Any], package_name: str) -> str:
    meta = _PKG_META[package_name]
    version_key = meta["wheel"] + "_version"
    version = str(policy.get(version_key, _DEFAULT_POLICY.get(version_key, "0.1"))).strip()
    return f"{package_name}=={version}"


def _run_install(target: str, editable: bool = False, refresh: bool = False) -> bool:
    if editable:
        uv_cmd = [
            sys.executable,
            "-m",
            "uv",
            "pip",
            "install",
            "--python",
            sys.executable,
            "-e",
            target,
        ]
        pip_cmd = [sys.executable, "-m", "pip", "install", "-e", target]
    else:
        uv_cmd = [
            sys.executable,
            "-m",
            "uv",
            "pip",
            "install",
            "--python",
            sys.executable,
            target,
        ]
        pip_cmd = [sys.executable, "-m", "pip", "install", target]
    if refresh:
        uv_cmd.insert(-1, "--refresh")
        pip_cmd.insert(-1, "--no-cache-dir")
    # Default to uv, but pin to current interpreter via --python.
    uv_res = subprocess.run(uv_cmd, capture_output=True, text=True)
    if uv_res.returncode == 0:
        return True
    pip_res = subprocess.run(pip_cmd, capture_output=True, text=True)
    return pip_res.returncode == 0


def install_repokit_packages(
    package_names: list[str],
    project_dir: pathlib.Path,
    setup_dir: pathlib.Path,
    verbose: bool = True,
) -> bool:
    policy = load_install_policy(project_dir)
    order = source_order(policy["source"])
    local_prepared = False
    local_source_available = True
    for package_name in package_names:
        installed = False
        for source in order:
            if source == "local":
                if not local_source_available:
                    continue
                if not local_prepared:
                    remove_embedded_git_dirs(setup_dir)
                    local_prepared = True
                wheel = local_wheel_path(setup_dir, package_name)
                if wheel and _run_install(str(wheel.resolve()), editable=False):
                    if verbose:
                        print(f"Installed {package_name} from local wheel: {wheel}")
                    installed = True
                    break
                editable = local_editable_path(setup_dir, package_name)
                if editable.exists() and _run_install(str(editable.resolve()), editable=True):
                    if verbose:
                        print(f"Installed {package_name} from local editable path: {editable}")
                    installed = True
                    break
                # Local fallback: bootstrap repokit sources if missing, then retry.
                if ensure_local_repokit_sources(setup_dir):
                    wheel = local_wheel_path(setup_dir, package_name)
                    if wheel and _run_install(str(wheel.resolve()), editable=False):
                        if verbose:
                            print(f"Installed {package_name} from bootstrapped local wheel: {wheel}")
                        installed = True
                        break
                    editable = local_editable_path(setup_dir, package_name)
                    if editable.exists() and _run_install(str(editable.resolve()), editable=True):
                        if verbose:
                            print(
                                f"Installed {package_name} from bootstrapped local editable path: {editable}"
                            )
                        installed = True
                        break
                elif verbose:
                    print("Local source bootstrap failed (git clone/submodule unavailable).")
                    # Avoid mixing local/non-local installs when local source tree is incomplete.
                    local_source_available = False
            elif source == "github":
                url = github_wheel_url(policy, package_name)
                if _run_install(url, editable=False, refresh=True):
                    if verbose:
                        print(f"Installed {package_name} from GitHub wheel URL.")
                    installed = True
                    break
                elif verbose:
                    print(f"GitHub wheel install failed for {package_name}: {url}")
            elif source == "pypi":
                spec = pypi_spec(policy, package_name)
                if _run_install(spec, editable=False, refresh=True):
                    if verbose:
                        print(f"Installed {package_name} from PyPI.")
                    installed = True
                    break
                elif verbose:
                    print(f"PyPI install failed for {package_name}: {spec}")
        if not installed:
            print(
                f"Failed to install {package_name} using source policy: {policy['source']} "
                f"(tried: {', '.join(order)})."
            )
            return False
    return True
