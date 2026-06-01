# src/owlroost/schema/sweeps/rates_from_to.py

"""
rates_selection.from_to sweep variable.
"""

from __future__ import annotations

from owlroost.catalog.ontology import (
    CatalogNodeType,
)

from ..registry import (
    FieldSpec,
)


def register_schema_fields(
    reg,
):
    reg.register(
        FieldSpec(
            name="rates_selection.from_to",
            dtype=str,
            path=(
                "rates_selection",
                "from_to",
            ),
            source="sweep",
            owner="ROOST",
            semantic_domain="decision",
            value_origin="user-specified",
            projection_kind="canonical",
            analytic_kind="observed",
            materialization_level="run",
            node_type=CatalogNodeType.VARIABLE,
            expands_to=[
                "rates_selection.from",
                "rates_selection.to",
            ],
            description=("Historical market window formatted as YYYY-YYYY."),
            defined_in="rates_from_to",
        )
    )


def expand(
    run_dict,
):
    rates = run_dict.setdefault(
        "rates_selection",
        {},
    )

    value = rates.pop(
        "from_to",
        None,
    )

    if not value:
        return

    start, end = value.split(
        "-",
        1,
    )

    rates["from"] = int(start)
    rates["to"] = int(end)
