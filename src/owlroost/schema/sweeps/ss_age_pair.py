# src/owlroost/schema/sweeps/ss_age_pair.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
Convenience alias for Social Security age sweeps.
"""

from __future__ import annotations

import re

from owlroost.catalog.ontology import (
    CatalogNodeType,
)

from ..registry import (
    FieldSpec,
)

_RANGE_RE = re.compile(
    r"""
    ^
    range
    \(
        \s*
        (?P<start>[^,]+)
        \s*,
        \s*
        (?P<stop>[^,]+)
        (?:
            \s*,
            \s*
            (?P<step>[^)]+)
        )?
    \)
    $
    """,
    re.VERBOSE,
)


def register_schema_fields(
    reg,
):
    reg.register(
        FieldSpec(
            name="roost_sweeps.ss_age_pair",
            dtype=str,
            path=(
                "roost_sweeps",
                "ss_age_pair",
            ),
            source="sweep",
            owner="ROOST",
            semantic_domain="decision",
            value_origin="user-specified",
            projection_kind="canonical",
            analytic_kind="observed",
            materialization_level="run",
            node_type=CatalogNodeType.VARIABLE,
            materializes_to=[
                "roost_sweeps.ss_age_person0",
                "roost_sweeps.ss_age_person1",
            ],
            description=("Convenience alias for Social Security age sweeps."),
            defined_in="ss_age_pair",
        )
    )


# =========================================================
# Helpers
# =========================================================


def _parse_number(
    text: str,
) -> float:
    text = text.strip()

    if "/" in text:
        numerator, denominator = text.split(
            "/",
            1,
        )

        return float(numerator) / float(denominator)

    return float(text)


def _format_age(
    value: float,
) -> str:
    value = round(
        value,
        6,
    )

    if value.is_integer():
        return str(
            int(value),
        )

    return f"{value:.4f}".rstrip("0").rstrip(".")


def _expand_expr(
    text: str,
) -> list[str]:
    text = text.strip()

    match = _RANGE_RE.match(
        text,
    )

    if match is None:
        return [
            text,
        ]

    start = _parse_number(match.group("start"))

    stop = _parse_number(match.group("stop"))

    step_text = match.group("step")

    step = _parse_number(step_text) if step_text is not None else 1.0

    values = []

    current = start

    while current <= stop + 1e-12:
        values.append(_format_age(current))

        current += step

    return values


# =========================================================
# CLI Expansion
# =========================================================


def expand_cli_to_override(
    override: str,
):
    """
    Convert:

        roost_sweeps.ss_age_pair=A-B

    into:

        roost_sweeps.ss_age_person0=A
        roost_sweeps.ss_age_person1=B

    while expanding any ROOST range()
    expressions into Hydra choice sweeps.
    """

    prefix = "roost_sweeps.ss_age_pair="

    if not override.startswith(
        prefix,
    ):
        return None

    value = override[len(prefix) :]

    left_text, right_text = value.split(
        "-",
        1,
    )

    left_values = _expand_expr(
        left_text,
    )

    right_values = _expand_expr(
        right_text,
    )

    return [
        (
            "roost_sweeps.ss_age_person0="
            + ",".join(
                left_values,
            )
        ),
        (
            "roost_sweeps.ss_age_person1="
            + ",".join(
                right_values,
            )
        ),
    ]
