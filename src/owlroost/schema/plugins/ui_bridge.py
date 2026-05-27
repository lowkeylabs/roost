# src/owlroost/schema/plugins/ui_bridge.py

from owlplanner.config import ui_bridge as ub

from ..registry import FieldSpec


class OwlUiBridgePlugin:
    """
    Harvest schema-relevant signals from
    owlplanner.config.ui_bridge.

    We only register config-facing fields
    that OWL accepts via config, not
    UI-only flattened keys.

    Sources:

        - ACA_FIELDS
            -> aca_settings.*

        - bootstrap_sor handling
            -> rates_selection.bootstrap_type
            -> rates_selection.block_size

        - explicit reads/writes in ui_bridge
            -> rates/tax knobs

        - account allocation mode
            -> asset_allocation.taxable
            -> asset_allocation.tax_deferred
            -> asset_allocation.tax_free
            -> asset_allocation.hsa
    """

    def register(self, registry):
        # -------------------------------------------------
        # helper: register only if missing
        # -------------------------------------------------

        def register_if_missing(
            name,
            path,
            dtype=object,
            description="",
        ):
            if name in registry._fields:
                return

            registry.register(
                FieldSpec(
                    name=name,
                    dtype=dtype,
                    path=path,
                    source="input",
                    materialization_level="case",
                    description=description,
                )
            )

        # -------------------------------------------------
        # 1) ACA fields
        # -------------------------------------------------

        aca_fields = getattr(
            ub,
            "ACA_FIELDS",
            [],
        )

        for key in aca_fields:
            register_if_missing(
                name=f"aca_settings.{key}",
                path=(
                    "aca_settings",
                    key,
                ),
                description=(
                    "Derived from OWL "
                    "ui_bridge ACA_FIELDS"
                ),
            )

        # -------------------------------------------------
        # 2) rates_selection extras exposed by ui_bridge
        # -------------------------------------------------

        rates_extras = {
            # bootstrap mode
            "bootstrap_type",
            "block_size",
            # tax knobs / rates knobs
            "heirs_rate_on_tax_deferred_estate",
            "dividend_rate",
            "long_term_capital_gains_rate",
            "net_investment_income_tax",
            "state_tax",
            "obbba_expiration_year",
            # seeds sometimes injected/propagated
            "rates_seed",
        }

        for key in rates_extras:
            register_if_missing(
                name=f"rates_selection.{key}",
                path=(
                    "rates_selection",
                    key,
                ),
                description=(
                    "Derived from OWL ui_bridge "
                    "(rates_selection extras)"
                ),
            )

        # -------------------------------------------------
        # 3) asset_allocation account-mode fields
        # -------------------------------------------------

        aa_account_fields = {
            "taxable",
            "tax_deferred",
            "tax_free",
            "hsa",
        }

        for key in aa_account_fields:
            register_if_missing(
                name=f"asset_allocation.{key}",
                path=(
                    "asset_allocation",
                    key,
                ),
                dtype=list,
                description=(
                    "Derived from OWL ui_bridge "
                    "(account allocation mode)"
                ),
            )

        # -------------------------------------------------
        # 4) fixed_income minor fields surfaced in UI
        # -------------------------------------------------

        fi_extras = {
            "social_security_trim_pct",
            "social_security_trim_year",
        }

        for key in fi_extras:
            register_if_missing(
                name=f"fixed_income.{key}",
                path=(
                    "fixed_income",
                    key,
                ),
                description=(
                    "Derived from OWL ui_bridge "
                    "(fixed_income extras)"
                ),
            )
