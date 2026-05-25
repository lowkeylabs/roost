# src/owlroost/display/fields/balances2.py

from __future__ import annotations

# =========================================================
# Registration
# =========================================================


def register_display_fields(
    reg,
):
    """
    Supplemental balance-sheet and HFP display fields.

    This module captures fields and semantics that were
    not migrated during the initial balances.py split.

    Goal:
        eliminate overrides.py without losing behavior.

    Cleanup/refactor can occur later once migration
    completeness is verified.
    """
