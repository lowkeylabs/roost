# src/owlroost/tools/schema_coverage.py

from pathlib import Path

import toml
import yaml

from owlroost.schema.bootstrap import build_registry
from owlroost.schema.runtime_defaults import build_runtime_defaults

CONF_ROOT = Path("src/owlroost/conf")
CASE_ROOT = Path("examples")


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def normalize_key(k: str) -> str:
    return k.replace("-", "_")


def flatten(d, prefix=()):
    out = set()

    if isinstance(d, dict):
        for k, v in d.items():
            k = normalize_key(k)
            out |= flatten(v, prefix + (k,))
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


def report_diff(label, missing, limit=10):
    if not missing:
        return

    print(f"\n{label} ({len(missing)} missing):")
    for m in sorted(missing)[:limit]:
        print("  ", m)

    if len(missing) > limit:
        print(f"  ... +{len(missing) - limit} more")


# ---------------------------------------------------------
# Loaders
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# Classification
# ---------------------------------------------------------
def classify_registry(reg):
    owl_fields = set()
    roost_fields = set()

    for f in reg.all():
        if f.source in ("input", "runtime", "owl"):
            owl_fields.add(f.name)
        else:
            roost_fields.add(f.name)

    return owl_fields, roost_fields


def classify_toml_fields(toml_fields):
    excluded_prefixes = ("case.", "cache.", "runtime_environment.")

    toml_fields = {f for f in toml_fields if not any(f.startswith(p) for p in excluded_prefixes)}

    extra_prefixes = (
        "longevity.",
        "spending_policy.",
        "roost.",
        "runtime.",
        "trial.",
        "metrics.",
    )

    extra = {f for f in toml_fields if f.startswith(extra_prefixes)}
    core = toml_fields - extra

    return core, extra


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def main():
    reg = build_registry()
    runtime = build_runtime_defaults()

    registry_fields = {f.name for f in reg.all()}
    runtime_fields = flatten(runtime)
    hydra_fields = load_hydra_fields()
    toml_fields_raw = load_toml_fields()

    # -----------------------------------------------------
    # Classify
    # -----------------------------------------------------
    registry_owl, registry_roost = classify_registry(reg)
    toml_core, toml_extra = classify_toml_fields(toml_fields_raw)

    runtime_owl = runtime_fields  # runtime already OWL

    # -----------------------------------------------------
    # Coverage
    # -----------------------------------------------------
    runtime_missing = runtime_owl - registry_owl
    toml_missing = toml_core - registry_owl
    extra_missing = toml_extra - registry_fields

    # -----------------------------------------------------
    # Ignore root-level fields for Hydra comparison
    # -----------------------------------------------------
    registry_owl_leaf = {f for f in registry_owl if "." in f}

    hydra_missing = registry_owl_leaf - hydra_fields

    print("\nSchema Coverage Report")
    print("-" * 30)

    print(f"OWL runtime fields:     {len(runtime_owl)}")
    print(f"Registry OWL fields:    {len(registry_owl)}")
    print(f"Registry ROOST fields:  {len(registry_roost)}")
    print(f"Hydra config fields:    {len(hydra_fields)}")
    print(f"TOML corpus fields:     {len(toml_fields_raw)}")
    print(f"TOML extra fields:      {len(toml_extra)}")

    print("\nCoverage (OWL scope):")
    print(
        f"  runtime → registry:   {pct(runtime_owl, registry_owl):6.1f}%  ({len(runtime_missing)} missing)"
    )
    print(
        f"  registry → hydra:     {pct(registry_owl_leaf, hydra_fields):6.1f}%  ({len(hydra_missing)} missing)"
    )
    print(
        f"  toml → registry:      {pct(toml_core, registry_owl):6.1f}%  ({len(toml_missing)} missing)"
    )

    print("\nCoverage (ROOST extensions):")
    print(
        f"  extra → registry:     {pct(toml_extra, registry_fields):6.1f}%  ({len(extra_missing)} missing)"
    )

    # -----------------------------------------------------
    # Details
    # -----------------------------------------------------
    report_diff("Registry missing OWL runtime fields", runtime_missing)
    report_diff("Hydra missing registry fields (OWL scope)", hydra_missing)
    report_diff("Registry missing TOML fields (OWL scope)", toml_missing)
    report_diff("Registry missing EXTRA section fields", extra_missing)

    print("\nDone.\n")


if __name__ == "__main__":
    main()
