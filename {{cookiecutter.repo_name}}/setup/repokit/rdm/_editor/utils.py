from __future__ import annotations

from pathlib import Path
from typing import Any

from .deps import LICENSE_LINKS, PROJECT_ROOT, today_iso


ZENODO_API_CHOICES = [
    ("https://sandbox.zenodo.org/api", "Sandbox (highly recommended)"),
    ("https://zenodo.org/api", "Production"),
]

DATAVERSE_SITE_CHOICES = [
    ("https://demo.dataverse.deic.dk", "DeiC Demo (recommended)"),
    ("https://dataverse.deic.dk", "DeiC Production"),
    ("other", "Other…"),
]


def has_privacy_flags(ds: dict) -> bool:
    return (
        str(ds.get("personal_data", "")).lower() == "yes"
        or str(ds.get("sensitive_data", "")).lower() == "yes"
    )


def normalize_chosen_path(chosen: str) -> str:
    """
    If `chosen` is under PROJECT_ROOT, return a path relative to PROJECT_ROOT.
    Otherwise, return an absolute POSIX-style path.
    """
    s = (chosen or "").strip()
    if not s:
        return s

    p = Path(s)

    if not p.is_absolute():
        return p.as_posix()

    try:
        root = PROJECT_ROOT.resolve()
    except Exception:
        return p.resolve().as_posix()

    try:
        rel = p.resolve().relative_to(root)
        return rel.as_posix()
    except ValueError:
        return p.resolve().as_posix()


def enforce_privacy_access(ds: dict) -> bool:
    """If personal/sensitive == yes, force all distributions to closed."""
    changed = False
    for dist in ds.get("distribution", []) or []:
        if has_privacy_flags(ds) and dist.get("data_access") != "closed":
            dist["data_access"] = "closed"
            changed = True
    return changed


def normalize_license_by_access(ds: dict) -> bool:
    """If data_access is shared/closed, remove CC license URLs (misleading for non-open)."""
    changed = False
    for dist in ds.get("distribution", []) or []:
        access = (dist.get("data_access") or "").lower()
        if access in {"shared", "closed"}:
            for lic in dist.get("license", []) or []:
                ref = (lic or {}).get("license_ref") or ""
                if "creativecommons.org" in ref:
                    lic["license_ref"] = ""
                    changed = True
    return changed


def ensure_open_has_license(ds: dict) -> bool:
    """If open and license empty, set default CC-BY-4.0."""
    changed = False
    default_ref = LICENSE_LINKS.get("CC-BY-4.0", "")
    for dist in ds.get("distribution", []) or []:
        if (dist.get("data_access") or "").lower() == "open":
            lics = dist.get("license") or []
            if not lics:
                dist["license"] = [{"license_ref": default_ref, "start_date": today_iso()}]
                changed = True
            else:
                for lic in lics:
                    if not (lic or {}).get("license_ref"):
                        lic["license_ref"] = default_ref
                        changed = True
    return changed


def is_reused(ds: dict) -> bool:
    v = ds.get("is_reused")
    return str(v).strip().lower() in {"true", "1", "yes"}


def is_empty_alias(v: Any) -> bool:
    return v is None or (isinstance(v, str) and v.strip() == "")


def key_for(*parts: Any) -> str:
    return "|".join(str(p) for p in parts if p is not None)
