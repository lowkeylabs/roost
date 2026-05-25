# src/owlroost/display/fields/__init__.py

from .balances import (
    register_display_fields as register_balance_fields,
)
from .balances2 import (
    register_display_fields as register_balance2_fields,
)
from .identity import (
    register_display_fields as register_identity_fields,
)
from .methodology import (
    register_display_fields as register_methodology_fields,
)
from .provenance import (
    register_display_fields as register_provenance_fields,
)
from .runtime import (
    register_display_fields as register_runtime_fields,
)
from .scaling import (
    register_display_fields as register_scaling_fields,
)


def register_all_display_fields(
    reg,
):
    """
    Register all display field modules.

    Registration ordering matters:

        1. foundational identity
        2. methodology/planning
        3. operational runtime
        4. computational scaling
        5. provenance/inventory
        6. financial balance-sheet
        7. supplemental balance-sheet migrations

    balances2.py exists temporarily to preserve
    full overrides.py functionality during the
    refactor transition.

    Future cleanup may merge balances.py and
    balances2.py once semantics stabilize.
    """

    register_identity_fields(reg)

    register_methodology_fields(reg)

    register_runtime_fields(reg)

    register_scaling_fields(reg)

    register_provenance_fields(reg)

    register_balance_fields(reg)

    # =====================================================
    # Supplemental migration fields
    # =====================================================

    register_balance2_fields(reg)
