from __future__ import annotations

from owlplanner.config.defaults import (
    default_config,
)

from ..registry import (
    FieldSpec,
)

# =========================================================
# Solver Key Discovery
# =========================================================

try:
    import owlplanner.config.ui_bridge as ui_bridge

    SOLVER_OPT_KEYS = getattr(
        ui_bridge,
        "SOLVER_OPT_KEYS",
        [],
    )

except Exception:
    SOLVER_OPT_KEYS = []

# =========================================================
# Helpers
# =========================================================


def infer_dtype(value):
    """
    Infer a stable dtype from a default value.

    Lists are treated as list.
    None becomes object.
    """

    if value is None:
        return object

    if isinstance(value, list):
        return list

    return type(value)


# =========================================================
# Plugin
# =========================================================


class OwlSolverPlugin:
    """
    Register solver_options fields using:

        - supported UI/config keys from SOLVER_OPT_KEYS
        - defaults/dtypes from default_config()

    This preserves:

        - compatibility coverage
        - canonical supported fields
        - runtime defaults
        - dynamic dtype inference

    while avoiding:

        - hardcoded duplicate lists
        - stale manual metadata
    """

    def register(
        self,
        registry,
    ):
        config = default_config()

        solver_defaults = config.get(
            "solver_options",
            {},
        )

        if not isinstance(
            solver_defaults,
            dict,
        ):
            solver_defaults = {}

        # -------------------------------------------------
        # Additional compatibility fields
        #
        # These are supported by Owl but may not appear in:
        #
        #     - SOLVER_OPT_KEYS
        #     - default_config()
        #
        # Keep small and intentional.
        # -------------------------------------------------

        extra_keys = {
            "gap",
            "minTaxableBalance",
            "previousMAGIs",
            "timePreference",
            "withACA",
            "withDecomposition",
            "withSSAges",
        }

        # -------------------------------------------------
        # Union of all supported keys
        # -------------------------------------------------

        all_keys = (
            set(SOLVER_OPT_KEYS)
            | set(solver_defaults.keys())
            | extra_keys
        )

        # -------------------------------------------------
        # Register fields
        # -------------------------------------------------

        for key in sorted(all_keys):
            name = f"solver_options.{key}"

            # ---------------------------------------------
            # Skip existing registrations
            # ---------------------------------------------

            if name in registry._fields:
                continue

            default_value = solver_defaults.get(key)

            registry.register(
                FieldSpec(
                    name=name,
                    dtype=infer_dtype(default_value),
                    path=(
                        "solver_options",
                        key,
                    ),
                    source="owl",
                    materialization_level="case",
                    default=default_value,
                    default_source=(
                        "runtime"
                        if key in solver_defaults
                        else None
                    ),
                    description=(
                        "Derived from OWL solver "
                        "configuration support."
                    ),
                )
            )
