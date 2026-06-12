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
from owlroost.core.utils import normalize_module_path

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
            projection_kind="synthetic",
            analytic_kind="primary",
            materialization_level="run",
            node_type=CatalogNodeType.VARIABLE,
            materializes_to=[
                "fixed_income.social_security_ages",
            ],
            description=("Convenience CLI alias for Social Security age sweeps."),
            defined_in=normalize_module_path(__file__),
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

        return float(numerator) / float(
            denominator,
        )

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

    return f"{value:.6f}".rstrip("0").rstrip(".")


def _is_range_expr(
    text: str,
) -> bool:
    return (
        _RANGE_RE.match(
            text.strip(),
        )
        is not None
    )


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

    start = _parse_number(
        match.group(
            "start",
        )
    )

    stop = _parse_number(
        match.group(
            "stop",
        )
    )

    step_text = match.group(
        "step",
    )

    step = _parse_number(step_text) if step_text is not None else 1.0

    values = []

    current = start

    while current <= stop + 1e-12:
        values.append(
            _format_age(
                current,
            )
        )

        current += step

    return values


def _split_top_level(
    text: str,
    *,
    sep: str = ",",
) -> list[str]:
    """
    Split on separators that occur only
    at top-level (outside parentheses).
    """

    parts = []
    current = []

    depth = 0

    for ch in text:
        if ch == "(":
            depth += 1

        elif ch == ")":
            depth -= 1

        if ch == sep and depth == 0:
            parts.append("".join(current).strip())
            current = []
            continue

        current.append(ch)

    parts.append("".join(current).strip())

    return [p for p in parts if p]


def _split_pair(
    text: str,
) -> tuple[str, str]:
    """
    Split:

        left-right

    at the first top-level '-'.

    Reject malformed expressions such as:

        62-64-67
    """

    depth = 0
    split_index = None

    for i, ch in enumerate(text):
        if ch == "(":
            depth += 1

        elif ch == ")":
            depth -= 1

        elif ch == "-" and depth == 0:
            if split_index is not None:
                raise ValueError(f"Invalid ss_age_pair: {text}")

            split_index = i

    if split_index is None:
        raise ValueError(f"Invalid ss_age_pair: {text}")

    return (
        text[:split_index].strip(),
        text[split_index + 1 :].strip(),
    )


# =========================================================
# CLI Expansion
# =========================================================


def expand_cli_to_override(
    override: str,
):
    """
    Modes
    -----

    Explicit paired sweep:

        64-64,67-67

    stays as ss_age_pair and is handled
    inside Hydra.

    Cartesian sweep:

        range(62,70)-range(62,70)

    expands to person0/person1 sweeps.
    """

    prefix = "roost_sweeps.ss_age_pair="

    if not override.startswith(
        prefix,
    ):
        return None

    value = override[len(prefix) :]

    pair_tokens = _split_top_level(
        value,
    )

    # -------------------------------------
    # Multiple pairs
    # -------------------------------------

    if len(pair_tokens) > 1:
        return None

    # -------------------------------------
    # Single pair
    # -------------------------------------

    left_text, right_text = _split_pair(
        pair_tokens[0],
    )

    left_is_range = _is_range_expr(
        left_text,
    )

    right_is_range = _is_range_expr(
        right_text,
    )

    # Explicit single pair
    if not (left_is_range or right_is_range):
        return None

    left_values = _expand_expr(
        left_text,
    )

    right_values = _expand_expr(
        right_text,
    )

    return [
        ("roost_sweeps.ss_age_person0=" + ",".join(left_values)),
        ("roost_sweeps.ss_age_person1=" + ",".join(right_values)),
    ]


# =========================================================
# Materialization
# =========================================================


def materialize_override_to_canonical(
    run_dict,
):
    roost_sweeps = run_dict.setdefault(
        "roost_sweeps",
        {},
    )

    value = roost_sweeps.pop(
        "ss_age_pair",
        None,
    )

    if value is None:
        return

    pairs = _split_top_level(
        value,
    )

    if len(pairs) != 1:
        raise ValueError("Explicit ss_age_pair materialization expects exactly one pair.")

    left_text, right_text = _split_pair(
        pairs[0],
    )

    fixed_income = run_dict.setdefault(
        "fixed_income",
        {},
    )

    fixed_income["social_security_ages"] = [
        float(left_text),
        float(right_text),
    ]
