from pathlib import Path

import yaml

from owlroost.schema.bootstrap import build_registry

CONF_ROOT = Path("src/owlroost/conf")


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def flatten(d, prefix=()):
    out = set()

    if isinstance(d, dict):
        for k, v in d.items():
            out |= flatten(v, prefix + (k,))
    elif isinstance(d, list):
        # treat list as atomic
        if prefix:
            out.add(".".join(prefix))
    else:
        if prefix:
            out.add(".".join(prefix))

    return out


def load_hydra_fields():
    fields = set()

    for group_dir in CONF_ROOT.iterdir():
        if not group_dir.is_dir():
            continue

        default_file = group_dir / "default.yaml"
        if not default_file.exists():
            continue

        data = yaml.safe_load(default_file.read_text())

        # -------------------------------------------------
        # 🔥 CASE 1: scalar root (e.g. case_name, description)
        # -------------------------------------------------
        if not isinstance(data, dict):
            fields.add(group_dir.name)
            continue

        # -------------------------------------------------
        # 🔥 CASE 2: dict root
        # -------------------------------------------------
        flat_paths = flatten(data)

        for path in flat_paths:
            parts = path.split(".")

            # already namespaced
            if parts[0] == group_dir.name:
                fields.add(path)
            else:
                fields.add(f"{group_dir.name}.{path}")

    return fields


def normalize_registry_fields(
    reg,
):
    """
    Return registry fields eligible for Hydra generation.

    Includes:
        - container/group nodes
        - leaf fields

    Includes only:
        - input fields
        - runtime fields
    """

    out = set()

    for f in reg.all():
        # -------------------------------------------------
        # Hydra-eligible sources only
        # -------------------------------------------------

        if f.source not in (
            "input",
            "runtime",
        ):
            continue

        # -------------------------------------------------
        # Must have path
        # -------------------------------------------------

        if not f.path:
            continue

        # -------------------------------------------------
        # Add all prefixes
        #
        # Example:
        #   ("longevity", "model_name")
        #
        # becomes:
        #   longevity
        #   longevity.model_name
        # -------------------------------------------------

        for i in range(1, len(f.path) + 1):
            out.add(".".join(f.path[:i]))

    return out


def normalize_hydra_fields():
    hydra_fields = load_hydra_fields()

    # remove hydra internals
    hydra_fields = {f for f in hydra_fields if not f.startswith("hydra.")}

    # leaf only
    hydra_fields = {f for f in hydra_fields if "." in f}

    # 🔥 remove derived/output domains ONLY
    hydra_fields = {
        f
        for f in hydra_fields
        if not (
            f.startswith("financial.")
            or f.startswith("risk.")
            or f.startswith("timing.")
            or f.startswith("complexity.")
            or f.startswith("identity.")
            or f.startswith("run_status.")
            or f.startswith("schema_version.")
            or f.startswith("score.")
            or f.startswith("rates.")  # derived summary rates
            or f.startswith("solver.")  # solver outputs
            or f.startswith("social_security.")  # output projections
        )
    }

    return hydra_fields


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------


def xtest_hydra_conf_subset_of_registry():
    reg = build_registry()

    registry_fields = normalize_registry_fields(reg)
    hydra_fields = normalize_hydra_fields()

    extra = hydra_fields - registry_fields

    assert not extra, "Hydra config contains unknown fields:\n" + "\n".join(sorted(extra))
