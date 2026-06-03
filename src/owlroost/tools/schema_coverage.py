# src/owlroost/tools/schema_coverage.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from pathlib import Path

import toml
import yaml

from owlroost.schema.bootstrap import build_registry
from owlroost.schema.runtime_defaults import (
    build_runtime_defaults,
)

CONF_ROOT = Path("src/owlroost/conf")
CASE_ROOT = Path("examples")


# =========================================================
# Helpers
# =========================================================


def report_section(
    title,
    missing,
    guidance=None,
    limit=15,
):
    if not missing:
        return

    print(f"\n{title} ({len(missing)}):")

    if guidance:
        print()
        for line in guidance:
            print(f"  {line}")

    print()

    for m in sorted(missing)[:limit]:
        print("   ", m)

    if len(missing) > limit:
        print(f"   ... +{len(missing) - limit} more")


def normalize_key(k: str) -> str:
    return k.replace("-", "_")


def flatten(d, prefix=()):
    out = set()

    if isinstance(d, dict):
        for k, v in d.items():
            k = normalize_key(k)

            out |= flatten(
                v,
                prefix + (k,),
            )

    elif isinstance(d, list):
        if prefix:
            out.add(".".join(prefix))

    else:
        if prefix:
            out.add(".".join(prefix))

    return out


def pct(a, b):
    if not a:
        return 100.0

    return 100.0 * (len(a & b) / len(a))


def report_diff(
    label,
    missing,
    limit=15,
):
    if not missing:
        return

    print(f"\n{label} ({len(missing)}):")

    for m in sorted(missing)[:limit]:
        print("   ", m)

    if len(missing) > limit:
        print(f"   ... +{len(missing) - limit} more")


# =========================================================
# Loaders
# =========================================================


def load_hydra_fields():
    fields = set()

    for group_dir in CONF_ROOT.iterdir():
        if not group_dir.is_dir():
            continue

        default_file = group_dir / "default.yaml"

        if not default_file.exists():
            continue

        data = yaml.safe_load(default_file.read_text()) or {}

        for path in flatten(data):
            if path.startswith(group_dir.name + "."):
                fields.add(path)

            else:
                fields.add(f"{group_dir.name}.{path}")

    return fields


def load_toml_fields():
    fields = set()

    for file in CASE_ROOT.rglob("*.toml"):
        try:
            data = toml.load(file)

        except Exception:
            continue

        fields |= flatten(data)

    return fields


# =========================================================
# Classification
# =========================================================


def classify_registry(reg):
    canonical = set()
    compatibility = set()
    synthetic = set()

    compatibility_solver = {
        "solver_options.amoRoth",
        "solver_options.amoSurplus",
        "solver_options.maxRothConversion",
        "solver_options.netSpending",
        "solver_options.noLateSurplus",
        "solver_options.noRothConversions",
        "solver_options.spendingSlack",
    }

    synthetic_fields = {
        "roost.run_name",
        "roost.trial_id",
        "runtime.owl_execution_mode",
    }

    output_prefixes = (
        "financial.",
        "risk.",
        "timing.",
        "complexity.",
        "identity.",
        "run_status.",
        "schema_version.",
        "score.",
        "rates.",
        "solver.",
        "social_security.",
    )

    for f in reg.all():
        # -------------------------------------------------
        # Synthetic/runtime orchestration
        # -------------------------------------------------

        if f.name in synthetic_fields:
            synthetic.add(f.name)
            continue

        # -------------------------------------------------
        # Compatibility/legacy fields
        # -------------------------------------------------

        if f.name in compatibility_solver:
            compatibility.add(f.name)
            continue

        # -------------------------------------------------
        # Output prefixes
        # -------------------------------------------------

        if f.name.startswith(output_prefixes):
            continue

        # -------------------------------------------------
        # Canonical schema/runtime
        # -------------------------------------------------

        canonical.add(f.name)

    return (
        canonical,
        compatibility,
        synthetic,
    )


def classify_toml_fields(toml_fields):
    excluded_prefixes = (
        "case.",
        "cache.",
        "roost_environment.",
    )

    toml_fields = {f for f in toml_fields if not any(f.startswith(p) for p in excluded_prefixes)}

    compatibility_prefixes = ("solver_options.",)

    synthetic_prefixes = (
        "roost.",
        "runtime.",
        "trial.",
    )

    compatibility = {f for f in toml_fields if f.startswith(compatibility_prefixes)}

    synthetic = {f for f in toml_fields if f.startswith(synthetic_prefixes)}

    canonical = toml_fields - compatibility - synthetic

    return (
        canonical,
        compatibility,
        synthetic,
    )


# =========================================================
# Main
# =========================================================


def main():
    reg = build_registry()

    runtime = build_runtime_defaults()

    registry_fields = {f.name for f in reg.all()}

    runtime_fields = flatten(runtime)

    hydra_fields = load_hydra_fields()

    toml_fields_raw = load_toml_fields()

    # -----------------------------------------------------
    # Classification
    # -----------------------------------------------------

    (
        registry_canonical,
        registry_compat,
        registry_synthetic,
    ) = classify_registry(reg)

    (
        toml_canonical,
        toml_compat,
        toml_synthetic,
    ) = classify_toml_fields(toml_fields_raw)

    # -----------------------------------------------------
    # Coverage
    # -----------------------------------------------------

    runtime_missing = runtime_fields - registry_canonical

    # -----------------------------------------------------
    # Hydra comparison scope
    #
    # Hydra only represents:
    # - leaf config fields
    # - dotted paths
    # -----------------------------------------------------

    registry_hydra_scope = {f for f in registry_canonical if "." in f}

    hydra_missing = registry_hydra_scope - hydra_fields

    canonical_missing = toml_canonical - registry_canonical

    compatibility_missing = toml_compat - registry_fields

    synthetic_missing = toml_synthetic - registry_fields

    # -----------------------------------------------------
    # Report
    # -----------------------------------------------------

    print("\nSchema Coverage Report")
    print("=" * 60)

    # =====================================================
    # Registry Summary
    # =====================================================

    print("\nRegistry Summary")
    print("-" * 60)

    print(f"Canonical registry fields:      {len(registry_canonical)}")

    print(f"Compatibility fields:           {len(registry_compat)}")

    print(f"Synthetic/runtime fields:       {len(registry_synthetic)}")

    print(f"Hydra config fields:            {len(hydra_fields)}")

    print(f"TOML corpus fields:             {len(toml_fields_raw)}")

    # =====================================================
    # Canonical Coverage
    # =====================================================

    print("\nCanonical Coverage")
    print("-" * 60)

    print(
        f"runtime → registry:             "
        f"{pct(runtime_fields, registry_canonical):6.1f}%"
        f"  ({len(runtime_missing)} missing)"
    )

    print(
        f"registry → hydra:               "
        f"{pct(registry_hydra_scope, hydra_fields):6.1f}%"
        f"  ({len(hydra_missing)} missing)"
    )

    print(
        f"toml → registry:                "
        f"{pct(toml_canonical, registry_canonical):6.1f}%"
        f"  ({len(canonical_missing)} missing)"
    )

    # =====================================================
    # Compatibility Coverage
    # =====================================================

    print("\nCompatibility Coverage")
    print("-" * 60)

    print(
        f"compatibility → registry:       "
        f"{pct(toml_compat, registry_fields):6.1f}%"
        f"  ({len(compatibility_missing)} missing)"
    )

    # =====================================================
    # Synthetic Coverage
    # =====================================================

    print("\nSynthetic / Runtime Coverage")
    print("-" * 60)

    print(
        f"synthetic → registry:           "
        f"{pct(toml_synthetic, registry_fields):6.1f}%"
        f"  ({len(synthetic_missing)} missing)"
    )

    # =====================================================
    # Details
    # =====================================================

    print("\nDetailed Diagnostics")
    print("-" * 60)

    report_diff(
        "Registry missing runtime fields",
        runtime_missing,
    )

    report_section(
        "Hydra missing canonical fields",
        hydra_missing,
        guidance=[
            "Canonical registry fields missing from Hydra config.",
            "",
            "Typical fixes:",
            "  - regenerate Hydra config",
            "  - or add manual overrides",
            "",
            "Primary locations:",
            "  src/owlroost/tools/generate_hydra_conf.py",
            "  src/owlroost/conf/",
        ],
    )

    report_section(
        "Registry missing canonical TOML fields",
        canonical_missing,
        guidance=[
            "These fields exist in example TOMLs",
            "but are not represented in canonical schema.",
            "",
            "Typical fixes:",
            "  - add field to Owl schema plugin",
            "  - add compatibility translation",
            "  - or migrate old TOMLs",
            "",
            "Primary locations:",
            "  src/owlroost/schema/plugins/owl.py",
            "  src/owlplanner/config/schema.py",
        ],
    )

    report_section(
        "Registry missing compatibility fields",
        compatibility_missing,
        guidance=[
            "These are legacy/compatibility fields",
            "observed in real TOMLs.",
            "",
            "Typical fixes:",
            "  - add compatibility registration",
            "  - add legacy translation",
            "  - or migrate old TOMLs",
            "",
            "Primary locations:",
            "  src/owlroost/schema/plugins/owl_solver.py",
            "  src/owlplanner/config/legacy.py",
        ],
    )

    report_section(
        "Registry missing synthetic/runtime fields",
        synthetic_missing,
        guidance=[
            "These are orchestration/runtime metadata fields.",
            "",
            "Typical fixes:",
            "  - add synthetic runtime registration",
            "  - or intentionally ignore",
            "",
            "Primary locations:",
            "  src/owlroost/schema/plugins/roost.py",
            "  src/owlroost/schema/plugins/runtime.py",
        ],
    )

    print("\nDone.\n")


if __name__ == "__main__":
    main()
