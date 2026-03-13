# tests/schema/test_conf_owl_alignment.py

from pathlib import Path

from owlplanner.config.schema import KNOWN_SECTIONS

import owlroost
from owlroost.domain.case import EXTRA_SECTION_REGISTRY

CONF_ROOT = Path(owlroost.__file__).resolve().parent / "conf"


# ------------------------------------------------------------
# Hydra orchestration-only groups
# ------------------------------------------------------------

HYDRA_ORCHESTRATION_GROUPS = {
    "hydra",
    "logging",
    "trial",
    "case",  # CLI injection group
    "__pycache__",
}


def test_conf_groups_align_with_schema():
    """
    Ensure every Hydra config group (folder containing default.yaml)
    corresponds to:

      - An OWL KNOWN_SECTION
      - A ROOST extension section
      - A Hydra orchestration group

    Prevents stale or mistyped config groups.
    """

    conf_dirs = {
        p.name for p in CONF_ROOT.iterdir() if p.is_dir() and (p / "default.yaml").exists()
    }

    owl_sections = set(KNOWN_SECTIONS)
    roost_extensions = set(EXTRA_SECTION_REGISTRY.keys())

    allowed = owl_sections | roost_extensions | HYDRA_ORCHESTRATION_GROUPS

    unknown = conf_dirs - allowed

    assert not unknown, f"Unknown Hydra config groups not recognized by OWL or ROOST: {unknown}"
