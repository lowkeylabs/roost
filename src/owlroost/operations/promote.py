from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from pathlib import Path

import tomlkit

# =========================================================
# Public API
# =========================================================


def collect_promote_targets(
    rows,
):
    """
    Resolve run directories from dataset rows.

    Promotion only operates on run-level rows.
    """

    targets = []

    for row in rows:
        paths = row.get("_paths", {})

        run_dir = paths.get("run_dir")

        if run_dir is None:
            continue

        run_dir = Path(run_dir)

        run_toml = run_dir / "run.toml"

        if not run_toml.exists():
            continue

        targets.append(run_dir)

    # Deduplicate + stable ordering
    return sorted(set(targets))


def promote_runs(
    run_dirs,
    cwd=".",
):
    """
    Promote run.toml files into the working directory.

    Parameters
    ----------
    run_dirs:
        Iterable of run directories.

    cwd:
        Working directory where promoted TOMLs
        should be written.

    Returns
    -------
    list[Path]
        Paths to promoted TOML files.
    """

    cwd = Path(cwd).resolve()

    promoted = []

    for run_dir in run_dirs:
        path = promote_run(
            run_dir,
            cwd=cwd,
        )

        promoted.append(path)

    return promoted


# =========================================================
# Single Promotion
# =========================================================


def promote_run(
    run_dir,
    cwd,
):
    """
    Promote a single run directory.
    """

    run_dir = Path(run_dir).resolve()

    run_toml = run_dir / "run.toml"

    if not run_toml.exists():
        raise FileNotFoundError(f"Missing run.toml: {run_toml}")

    # =====================================================
    # Load effective run config
    # =====================================================

    run_doc = tomlkit.parse(
        run_toml.read_text(
            encoding="utf-8",
        )
    )

    promoted_doc = deepcopy(
        run_doc,
    )

    # =====================================================
    # Determine lineage BEFORE sanitization
    # =====================================================

    parent_filename = resolve_parent_filename(
        promoted_doc,
    )

    root_filename = resolve_root_filename(
        promoted_doc,
        parent_filename,
    )

    # =====================================================
    # Generate promoted filename
    # =====================================================

    promoted_filename = next_promoted_filename(
        parent_filename,
        cwd,
    )

    promoted_path = cwd / promoted_filename

    # =====================================================
    # Load + sanitize parent config
    # =====================================================

    parent_path = cwd / parent_filename

    parent_doc = None

    if parent_path.exists():
        parent_doc = tomlkit.parse(
            parent_path.read_text(
                encoding="utf-8",
            )
        )

        parent_doc = deepcopy(
            parent_doc,
        )

        sanitize_promoted_config(
            parent_doc,
        )

    # =====================================================
    # Remove operational/runtime sections
    # =====================================================

    sanitize_promoted_config(
        promoted_doc,
    )

    # =====================================================
    # Rewrite promoted identity
    # =====================================================

    apply_promoted_identity(
        promoted_doc,
        promoted_filename,
    )

    # =====================================================
    # Build promotion section
    # =====================================================

    promotion_section = build_promotion_section(
        promoted_doc=promoted_doc,
        parent_doc=parent_doc,
        parent_filename=parent_filename,
        root_filename=root_filename,
        run_dir=run_dir,
        run_toml=run_toml,
    )

    promoted_doc["promotion"] = promotion_section

    # =====================================================
    # Write promoted TOML
    # =====================================================

    promoted_path.write_text(
        tomlkit.dumps(promoted_doc),
        encoding="utf-8",
    )

    promotion = promoted_doc.get(
        "promotion",
        {},
    )

    return {
        "path": promoted_path,
        "diff_is_empty": bool(
            promotion.get(
                "diff_is_empty",
                False,
            )
        ),
    }


# =========================================================
# Parent Resolution
# =========================================================


def resolve_parent_filename(
    doc,
):
    """
    Determine parent TOML filename.

    Priority:
        1. Existing promotion.parent
        2. case.file basename
    """

    promotion = doc.get(
        "promotion",
        {},
    )

    parent = promotion.get(
        "parent",
    )

    if parent:
        return str(parent)

    case = doc.get(
        "case",
        {},
    )

    case_file = case.get(
        "file",
    )

    if not case_file:
        raise ValueError("Unable to determine parent filename.")

    return Path(case_file).name


def resolve_root_filename(
    doc,
    fallback,
):
    """
    Determine root TOML filename.
    """

    promotion = doc.get(
        "promotion",
        {},
    )

    root = promotion.get(
        "root",
    )

    if root:
        return str(root)

    return fallback


# =========================================================
# Filename Generation
# =========================================================


def next_promoted_filename(
    parent_filename,
    cwd,
):
    """
    Generate next sequential promotion filename.

    Example:
        case_alex+jamie.toml
            -> case_alex+jamie-p001.toml
    """

    parent_path = Path(parent_filename)

    stem = parent_path.stem

    # ----------------------------------------
    # Remove existing promotion suffix
    # ----------------------------------------

    if "-p" in stem:
        parts = stem.rsplit(
            "-p",
            1,
        )

        if len(parts) == 2 and parts[1].isdigit():
            stem = parts[0]

    pattern = f"{stem}-p*.toml"

    existing = sorted(cwd.glob(pattern))

    max_num = 0

    for path in existing:
        suffix = path.stem.rsplit(
            "-p",
            1,
        )[-1]

        try:
            num = int(suffix)

        except ValueError:
            continue

        max_num = max(
            max_num,
            num,
        )

    next_num = max_num + 1

    return f"{stem}-p{next_num:03d}.toml"


# =========================================================
# Sanitization
# =========================================================


def sanitize_promoted_config(
    doc,
):
    """
    Remove operational/generated sections.

    Promotion should create a clean,
    independently runnable TOML.
    """

    removable = [
        "metrics",
        "run_status",
        "run_timing",
        "run_execution",
        "promotion",
        "hydra",
        "hydra_runtime",
        "hydra_overrides",
    ]

    for key in removable:
        if key in doc:
            del doc[key]


def apply_promoted_identity(
    doc,
    promoted_filename,
):
    """
    Rewrite promoted TOML identity fields.

    Promotion creates a new first-class
    case artifact.
    """

    promoted_filename = Path(
        promoted_filename,
    ).name

    promoted_stem = Path(
        promoted_filename,
    ).stem

    # =====================================================
    # case_name
    # =====================================================

    if promoted_stem.startswith("case_"):
        case_name = promoted_stem[len("case_") :]

    else:
        case_name = promoted_stem

    doc["case_name"] = case_name

    # =====================================================
    # [case]
    # =====================================================

    case_section = doc.get(
        "case",
    )

    if case_section is None:
        case_section = tomlkit.table()
        doc["case"] = case_section

    case_section["file"] = promoted_filename

    case_section["name"] = promoted_stem


# =========================================================
# Promotion Metadata
# =========================================================


def build_promotion_section(
    promoted_doc,
    parent_doc,
    parent_filename,
    root_filename,
    run_dir,
    run_toml,
):
    """
    Construct [promotion] section.
    """

    section = tomlkit.table()

    # =====================================================
    # Core provenance
    # =====================================================

    section["parent"] = parent_filename

    section["root"] = root_filename

    section["promoted_at"] = datetime.now().astimezone().isoformat()

    section["source_run"] = str(
        run_dir,
    )

    section["source_run_toml"] = str(
        run_toml,
    )

    # =====================================================
    # Replayable semantic diff
    # =====================================================

    diff = compute_diff(
        parent_doc,
        promoted_doc,
    )

    # -----------------------------------------------------
    # No semantic differences
    # -----------------------------------------------------

    if not diff:
        section["diff_is_empty"] = True

        return section

    # -----------------------------------------------------
    # Materialize diff table
    # -----------------------------------------------------

    diff_table = tomlkit.table()

    for key, value in sorted(diff.items()):
        entry = tomlkit.table()

        entry["old"] = value["old"]

        entry["new"] = value["new"]

        diff_table[key] = entry

    section["diff"] = diff_table

    return section


# =========================================================
# Diff Engine
# =========================================================


def compute_diff(
    parent_doc,
    promoted_doc,
):
    """
    Compute replayable semantic diff.

    Returns
    -------
    dict[str, dict]
        Mapping:

            key -> {
                "old": value,
                "new": value,
            }
    """

    if parent_doc is None:
        return {}

    parent_flat = flatten_dict(
        parent_doc,
    )

    promoted_flat = flatten_dict(
        promoted_doc,
    )

    diff = {}

    keys = sorted(set(parent_flat) | set(promoted_flat))

    ignored_prefixes = (
        "promotion.",
        "roost_runtime.",
        "runtime_environment.",
    )

    ignored_exact = {
        "case.file",
        "case.name",
        "case_name",
    }

    for key in keys:
        # --------------------------------------------
        # Ignore noisy/generated/runtime fields
        # --------------------------------------------

        if key in ignored_exact:
            continue

        if key.startswith(ignored_prefixes):
            continue

        old = parent_flat.get(
            key,
        )

        new = promoted_flat.get(
            key,
        )

        if old == new:
            continue

        # --------------------------------------------
        # TOML-safe missing markers
        # --------------------------------------------

        if old is None:
            old = "__MISSING__"

        if new is None:
            new = "__MISSING__"

        diff[key] = {
            "old": normalize_scalar(old),
            "new": normalize_scalar(new),
        }

    return diff


# =========================================================
# Flatten Helpers
# =========================================================


def flatten_dict(
    obj,
    prefix="",
):
    """
    Flatten nested TOML structures into dotted keys.
    """

    result = {}

    if isinstance(
        obj,
        dict,
    ):
        for key, value in obj.items():
            # --------------------------------------------
            # Ignore promotion lineage metadata
            # --------------------------------------------

            if key == "promotion":
                continue

            path = f"{prefix}.{key}" if prefix else str(key)

            result.update(
                flatten_dict(
                    value,
                    path,
                )
            )

    else:
        result[prefix] = normalize_scalar(
            obj,
        )

    return result


def normalize_scalar(
    value,
):
    """
    Normalize TOML values for diff stability.
    """

    if isinstance(
        value,
        Path,
    ):
        return str(value)

    return value
