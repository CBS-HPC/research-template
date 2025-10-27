#!/usr/bin/env python3

from __future__ import annotations

import multiprocessing
import os
import stat
import tempfile
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from ..common import PROJECT_ROOT

# ========= Exceptions / constants =========


class PublishError(RuntimeError):
    pass


RETRY_STATUS = {429, 500, 502, 503, 504}
DEFAULT_TIMEOUT = 60

UPLOAD_WORKERS = int(os.environ.get("UPLOAD_WORKERS", "8"))

# Zenodo defaults (decimal GB)
ZENODO_MAX_FILES = 100
ZENODO_MAX_TOTAL = 50_000_000_000  # 50 GB
ZENODO_ROLE_MAP = {
    "creator": "Researcher",
    "author": "Researcher",
    "rights_holder": "RightsHolder",
    "data_manager": "DataManager",
    "data curator": "DataCurator",
    "curator": "DataCurator",
    "editor": "Editor",
    "contact person": "ContactPerson",
    "supervisor": "Supervisor",
    "project manager": "ProjectManager",
    "sponsor": "Sponsor",
    "workpackage leader": "WorkPackageLeader",
}

# Dataverse upload constraints (as given)
DATAVERSE_MAX_FILES_TOTAL: int = 100
DATAVERSE_MAX_FILE_SIZE_BYTES: int = int(953.7 * 1_000_000)  # 953.7 MB (decimal)
DATAVERS_SUBJECTS: dict[str, str] = {
    "agricultural sciences": "Agricultural Sciences",
    "arts and humanities": "Arts and Humanities",
    "astronomy and astrophysics": "Astronomy and Astrophysics",
    "business and management": "Business and Management",
    "chemistry": "Chemistry",
    "computer and information science": "Computer and Information Science",
    "earth and environmental sciences": "Earth and Environmental Sciences",
    "engineering": "Engineering",
    "law": "Law",
    "mathematics": "Mathematics",
    "medicine, health and life sciences": "Medicine, Health and Life Sciences",
    "medicine": "Medicine, Health and Life Sciences",
    "health and life sciences": "Medicine, Health and Life Sciences",
    "physics": "Physics",
    "social sciences": "Social Sciences",
    "other": "Other",
}


# Compression heuristics
_COMPRESSIBLE = {
    ".txt",
    ".csv",
    ".tsv",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".md",
    ".log",
    ".fastq",
    ".fasta",
    ".sam",
}
_INCOMPRESSIBLE = {
    ".zip",
    ".gz",
    ".bz2",
    ".xz",
    ".zst",
    ".7z",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".mp3",
    ".mp4",
    ".mov",
    ".avi",
    ".pdf",
    ".parquet",
    ".feather",
    ".orc",
}

# ========= maDMP utilities =========


def _get(d: dict, path: list[str], default=None):
    cur = d
    for p in path:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return default
    return cur


def _norm_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def _guess_dataset(dmp: dict, dataset_id: str | None) -> dict:
    datasets = _get(dmp, ["dmp", "dataset"], []) or dmp.get("dataset", [])
    if not datasets:
        raise PublishError(
            "No datasets found in the DMP (expected 'dmp.dataset' or top-level 'dataset')."
        )
    if dataset_id:
        for ds in datasets:
            if ds.get("dataset_id") == dataset_id or ds.get("title") == dataset_id:
                return ds
            for ident in _norm_list(ds.get("identifier")) + _norm_list(ds.get("dataset_id")):
                if isinstance(ident, dict) and ident.get("identifier") == dataset_id:
                    return ds
                if ident == dataset_id:
                    return ds
    return datasets[0]


def _keywords_from_madmp(ds: dict) -> list[str]:
    kws = []
    kws += [kw for kw in _norm_list(ds.get("keyword", [])) if isinstance(kw, str)]
    for subj in _norm_list(ds.get("subject", [])):
        term = subj.get("term") or subj.get("value") if isinstance(subj, dict) else None
        if term:
            kws.append(term)
    seen = set()
    out = []
    for k in (k.strip() for k in kws if isinstance(k, str)):
        if k and k.lower() not in seen:
            seen.add(k.lower())
            out.append(k)
    return out[:50]


def _has_personal_or_sensitive(ds: dict) -> bool:
    def _yes(x):
        return isinstance(x, str) and x.strip().lower() == "yes"

    return _yes(ds.get("personal_data")) or _yes(ds.get("sensitive_data"))


# ========= x_dcas file resolution =========


def files_from_x_dcas(ds: dict) -> list[str]:
    """
    Authoritative list from extension[].x_dcas.data_files. Normalize/resolve paths.
    """
    out: list[str] = []

    for ext in _norm_list(ds.get("extension", [])):
        if not isinstance(ext, dict):
            continue
        x = ext.get("x_dcas") or {}
        for p in _norm_list(x.get("data_files", [])):
            if not isinstance(p, str):
                continue
            pp = os.path.normpath(p.replace("\\", "/"))
            if not os.path.isabs(pp):
                pp = os.path.normpath(os.path.join(PROJECT_ROOT, pp))
            out.append(pp)
    # unique, preserve order
    seen, uniq = set(), []
    for p in out:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq



def regular_files_existing(paths: list[str]) -> list[str]:
    """Keep only existing regular files; skip dirs/symlinks/unreadable."""
    out = []
    for p in paths:
        try:
            st = os.stat(p)
            if stat.S_ISREG(st.st_mode):
                out.append(p)
        except Exception:
            pass
    return out


def sizes_bytes(files: list[str]) -> tuple[int, dict]:
    """Return (total_bytes, per_file_size)."""
    sizes = {}
    total = 0
    for f in files:
        try:
            sz = os.path.getsize(f)
        except Exception:
            sz = 0
        sizes[f] = sz
        total += sz
    return total, sizes


def estimate_zip_total_bytes(files: list[str], total_bytes: int) -> int:
    """
    Conservative estimate of zipped total:
      compressible ~50%; incompressible ~100%; unknown ~90%.
    """
    comp = incom = 0
    _, per = sizes_bytes(files)
    for f, sz in per.items():
        ext = os.path.splitext(f)[1].lower()
        if ext in _COMPRESSIBLE:
            comp += sz
        elif ext in _INCOMPRESSIBLE:
            incom += sz
    unknown = max(0, total_bytes - comp - incom)
    return int(comp * 0.5 + incom * 1.0 + unknown * 0.9)


# ========= PACKAGING NOTE (with ASCII tree) =========


def append_packaging_note(
    desc: str, pre_files: int, pre_bytes: int, final_paths: list[str], report: list[dict]
) -> str:
    """
    Append a formatted packaging note. Shows totals and an ASCII tree of the original
    dataset structure up to the zipping level. The tree is reconstructed from the
    report entries' 'first_level' keys and 'dataset_root'.
    """

    def _gb(n):
        return f"{n / 1_000_000_000:.2f} GB"

    post_total = sum(os.path.getsize(p) for p in final_paths if os.path.exists(p))
    base = (desc or "No description provided.").strip()

    summary = []
    summary.append(
        f"Original payload (from x_dcas.data_files): {pre_files} files, ~{_gb(pre_bytes)} total."
    )
    summary.append(f"Final upload set: {len(final_paths)} item(s), ~{_gb(post_total)} total.")

    # ASCII tree (only if a report is available)
    tree_lines: list[str] = []
    if report:
        # totals per archive already in report
        summary.append(f"Created {len(report)} archive(s) to comply with upload limits.")
        for r in report:
            examples = ", ".join(r.get("examples", []))
            summary.append(f"{r['archive']}: {r['count']} files (~{_gb(r['bytes'])})")
            if examples:
                summary.append(f"   e.g., {examples}")

        # Build tree structure: group by first-level directory
        groups: dict[str, list[dict]] = {}
        dataset_root = None
        for r in report:
            k = r.get("first_level", "")  # "" means root files
            groups.setdefault(k, []).append(r)
            dataset_root = dataset_root or r.get("dataset_root")

        # Order groups: subdirs (sorted) then root files (if any) at the end
        keys = sorted([k for k in groups if k]) + ([""] if "" in groups else [])

        # Root label
        root_label = (dataset_root or "dataset") + "/"
        tree_lines.append(root_label)

        # Emit first-level nodes
        for gi, key in enumerate(keys):
            is_last = gi == len(keys) - 1
            branch = "└─ " if is_last else "├─ "
            prefix_children = "   " if is_last else "│  "

            entries = groups[key]
            if key == "":
                # Root files: may have multiple archives in the flat-folder case
                if len(entries) == 1:
                    e = entries[0]
                    tree_lines.append(
                        f"{branch}(root files) → {e['archive']} ({e['count']} files, ~{_gb(e['bytes'])})"
                    )
                else:
                    tree_lines.append(f"{branch}(root files)")
                    for j, e in enumerate(entries):
                        sub_last = j == len(entries) - 1
                        sub_branch = "└─ " if sub_last else "├─ "
                        tree_lines.append(
                            f"{prefix_children}{sub_branch}{e['archive']} ({e['count']} files, ~{_gb(e['bytes'])})"
                        )
            else:
                # Subdirectory: exactly one zip per subdir in preserve-first-level plan
                e = entries[0]
                tree_lines.append(
                    f"{branch}{key}/ → {e['archive']} ({e['count']} files, ~{_gb(e['bytes'])})"
                )

    # Compose final note (with two blank lines before header, and a single <pre> block)
    body_lines = summary
    if tree_lines:
        body_lines.append("")
        body_lines.append("Dataset structure (zipped at first level):")
        body_lines.extend(tree_lines)

    return base + "<pre>\n\n\n[PACKAGING NOTE]\n\n" + "\n".join(body_lines) + "\n</pre>"


# ========= People / affiliation / license helpers (shared) =========


def _normalize_orcid(raw: str | None) -> str | None:
    if not raw:
        return None
    s = str(raw).strip()
    s = s.replace("https://orcid.org/", "").replace("http://orcid.org/", "").strip()
    s = s.replace(" ", "").replace("-", "")
    if len(s) != 16:
        if len(s) == 19 and s.count("-") == 3:
            return s
        return None
    core, last = s[:-1], s[-1:]
    if core.isdigit() and (last.isdigit() or last.upper() == "X"):
        return f"{s[0:4]}-{s[4:8]}-{s[8:12]}-{s[12:16]}"
    return None


def _affiliation_from_node(node: dict | None) -> tuple[str | None, str | None]:
    if not isinstance(node, dict):
        return (None, None)
    name = node.get("name")
    ror = None
    aff_id = node.get("affiliation_id") or node.get("organization_id") or {}
    if isinstance(aff_id, dict) and (aff_id.get("type") or "").lower() == "ror":
        rid = aff_id.get("identifier")
        if isinstance(rid, str) and rid:
            ror = rid.strip()
    return (name, ror)


def description_from_madmp(ds: dict) -> str:
    desc = ds.get("description") or _get(ds, ["description", "text"])
    return desc or "No description provided."


def related_identifiers(ds: dict) -> list[dict[str, str]]:
    rels = []
    for ref in _norm_list(ds.get("related_identifier", [])) + _norm_list(ds.get("reference", [])):
        if isinstance(ref, dict):
            idv = ref.get("identifier") or ref.get("id")
            scheme = (ref.get("type") or ref.get("scheme") or "").upper() or None
            relation = ref.get("relation_type") or ref.get("relation") or "isReferencedBy"
        else:
            idv = str(ref)
            scheme = None
            relation = "isReferencedBy"
        if idv:
            r = {"identifier": idv, "relation": relation}
            if scheme:
                r["scheme"] = scheme
            rels.append(r)
    return rels[:100]


# ========= Parallel packaging plan & execution =========

# Tune these as needed or via env vars:
ZIP_WORKERS = max(1, min((multiprocessing.cpu_count() or 2), 8))  # CPU-bound
ZIP_CHUNK = 2000  # files per compressed zip chunk to keep central dir reasonable


class PackItem:
    """
    A packaging plan item.
    - kind = "single" -> path is a single file to upload as-is
    - kind = "zip"    -> zip_path is where to write; members is list of files
                         compression = zipfile.ZIP_DEFLATED or ZIP_STORED
    """

    __slots__ = ("kind", "path", "zip_path", "members", "compression")

    def __init__(
        self,
        kind: str,
        path: str | None = None,
        zip_path: str | None = None,
        members: list[str] | None = None,
        compression: int | None = None,
    ):
        self.kind = kind
        self.path = path
        self.zip_path = zip_path
        self.members = members or []
        self.compression = compression


def build_packaging_plan(files: list[str]) -> tuple[list[PackItem], list[dict], str]:
    """
    Return (plan, report, workdir). Does NOT create zips yet.
    """
    if not files:
        return [], [], tempfile.mkdtemp(prefix="zenodo_pack_")  # empty

    total, sizes = sizes_bytes(files)
    parent = os.path.commonpath(files)
    dataset_root_name = Path(parent).name or "dataset"

    comp_files, incom_files, other = [], [], []
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if ext in _COMPRESSIBLE:
            comp_files.append(f)
        elif ext in _INCOMPRESSIBLE:
            incom_files.append(f)
        else:
            other.append(f)

    singles: list[str] = []
    small_incom: list[str] = []
    for f in sorted(incom_files, key=lambda x: -sizes[x]):
        (singles if sizes[f] >= 1_000_000_000 else small_incom).append(f)  # >=1 GB single

    workdir = tempfile.mkdtemp(prefix="zenodo_pack_")
    plan: list[PackItem] = []
    report: list[dict] = []

    def add_zip_plan(members: list[str], name_stub: str, compression: int):
        zip_path = os.path.join(workdir, f"{name_stub}.zip")
        plan.append(PackItem("zip", zip_path=zip_path, members=members, compression=compression))
        report.append(
            {
                "archive": os.path.basename(zip_path),
                "count": len(members),
                "bytes": sum(sizes[m] for m in members),
                "examples": [os.path.basename(m) for m in members[:5]],
                "first_level": "",  # flat -> root files
                "dataset_root": dataset_root_name,  # for tree header
            }
        )

    # Compressible -> deflated zips (chunked)
    if comp_files:
        for i in range(0, len(comp_files), ZIP_CHUNK):
            chunk = comp_files[i : i + ZIP_CHUNK]
            add_zip_plan(
                chunk, f"comp_{1 + i // ZIP_CHUNK:03d}", getattr(zipfile, "ZIP_DEFLATED", 0)
            )

    # Reduce count if over 100 using STORE zips on small incompressible + unknown
    remain_pool = small_incom + other
    while (
        len(singles) + len(remain_pool) + sum(1 for it in plan if it.kind == "zip")
    ) > ZENODO_MAX_FILES:
        reduce_needed = (
            len(singles) + len(remain_pool) + sum(1 for it in plan if it.kind == "zip")
        ) - ZENODO_MAX_FILES
        K = min(max(1, reduce_needed + 1), 1000)
        group, remain_pool = remain_pool[:K], remain_pool[K:]
        add_zip_plan(
            group,
            f"store_{len([1 for it in plan if it.kind == 'zip']) + 1:03d}",
            getattr(zipfile, "ZIP_STORED", 0),
        )

    # Whatever remains can be singles
    singles.extend(remain_pool)
    for s in singles:
        plan.append(PackItem("single", path=s))
        # singles aren't reported as archives; they appear directly in uploads

    return plan, report, workdir


def _first_level_groups(files: list[str]) -> tuple[Path, dict[str, list[str]]]:
    """
    Group files by first-level subdirectory under the common parent.
    Returns (common_parent, groups), where groups maps:
      "" -> files directly under parent
      "subdir" -> files under parent/subdir/**
    Robust to cases where relpath == "." (Path(".").parts == ()).
    """
    if not files:
        return Path("."), {"": []}

    # Use absolute paths for stable commonpath behaviour
    files_abs = [os.path.abspath(f) for f in files]
    try:
        parent_str = os.path.commonpath(files_abs)
    except ValueError:
        # (Different drives on Windows). Fallback: use each file's own parent as "parent",
        # which yields all files as "" group (still valid for our callers).
        parent_str = os.path.dirname(files_abs[0])

    parent = Path(parent_str)
    groups: dict[str, list[str]] = {}

    for f in files_abs:
        rel_str = os.path.relpath(f, start=parent_str)

        # Normalize funky cases: "", "." → root
        if rel_str in ("", "."):
            head = ""
        else:
            # Use string split, not Path.parts (avoids the '.' empty-parts trap)
            norm = rel_str.replace("\\", "/")
            parts = norm.split("/")
            # a single component like "file.txt" is root-level
            head = "" if len(parts) == 1 else parts[0]

        groups.setdefault(head, []).append(f)

    return parent, groups


def build_packaging_plan_preserve_first_level(
    files: list[str],
) -> tuple[list[PackItem], list[dict], str]:
    """
    Preserve first-level directory structure:
      - If ONLY root files (no subdirs): fall back to build_packaging_plan(files)
      - Else: create one DEFLATED zip per first-level subdirectory.
              If there are root files, put them into 'root_files.zip'.
    """
    if not files:
        return [], [], tempfile.mkdtemp(prefix="zenodo_pack_")

    parent, groups = _first_level_groups(files)
    dataset_root_name = parent.name or "dataset"
    subdirs = [k for k in groups.keys() if k]  # exclude "" (root)

    # If no subdirectories, keep original smart plan
    if not subdirs:
        return build_packaging_plan(files)

    workdir = tempfile.mkdtemp(prefix="zenodo_pack_")
    plan: list[PackItem] = []
    report: list[dict] = []

    def add_zip(members: list[str], name_stub: str):
        zip_path = os.path.join(workdir, f"{name_stub}.zip")
        plan.append(
            PackItem(
                "zip",
                zip_path=zip_path,
                members=members,
                compression=getattr(zipfile, "ZIP_DEFLATED", 0),
            )
        )
        _, sizes = sizes_bytes(members)
        report.append(
            {
                "archive": os.path.basename(zip_path),
                "count": len(members),
                "bytes": sum(sizes.get(m, 0) for m in members),
                "examples": [os.path.basename(m) for m in members[:5]],
                "first_level": name_stub if name_stub != "root_files" else "",
                "dataset_root": dataset_root_name,
            }
        )

    # One zip per subdirectory
    for sub in sorted(subdirs):
        add_zip(groups[sub], f"{sub}")

    # Root files (if any) -> a single archive
    root_files = groups.get("", [])
    if root_files:
        add_zip(root_files, "root_files")

    # If we still exceed Zenodo file-count limit (extreme # of subdirs),
    # batch subdir zips by regrouping members (rare).
    if sum(1 for it in plan if it.kind == "zip") > ZENODO_MAX_FILES:
        all_members_groups = [it.members for it in plan if it.kind == "zip"]
        plan = []
        report = []
        batch_size = max(1, len(all_members_groups) // ZENODO_MAX_FILES + 1)
        for i in range(0, len(all_members_groups), batch_size):
            batch = []
            for grp in all_members_groups[i : i + batch_size]:
                batch.extend(grp)
            add_zip(batch, f"batched_{1 + i // batch_size:03d}")

    return plan, report, workdir


def _zip_worker(args):
    zip_path, members, compression = args
    base = os.path.commonpath(members) if len(members) > 1 else (os.path.dirname(members[0]) or ".")
    with zipfile.ZipFile(zip_path, "w", compression=compression, allowZip64=True) as zf:
        for fp in members:
            zf.write(fp, arcname=os.path.relpath(fp, start=base))
    return zip_path


def realize_packaging_plan_parallel(plan: list[PackItem]) -> list[str]:
    """
    Execute the plan: create zips in parallel (processes), return final paths to upload.
    """
    final_paths: list[str] = []
    zip_jobs = [(it.zip_path, it.members, it.compression) for it in plan if it.kind == "zip"]

    # Kick off zipping in parallel
    if zip_jobs:
        with ProcessPoolExecutor(max_workers=ZIP_WORKERS) as ex:
            futures = [ex.submit(_zip_worker, job) for job in zip_jobs]
            for fut in as_completed(futures):
                _ = fut.result()  # raise if worker failed

    # Collect final paths: singles + created zips
    for it in plan:
        if it.kind == "single":
            final_paths.append(it.path)
        elif it.kind == "zip":
            final_paths.append(it.zip_path)

    return final_paths
