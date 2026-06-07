# src/owlroost/display/renderers/latex_table.py
#
# Copyright (c) 2026 John Leonard
# All rights reserved.
# SPDX-License-Identifier: LicenseRef-OwlRoost-Proprietary
# See LICENSE file in repository root.

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations


def render_latex_table(table):
    cols = table.columns
    rows = table.rows

    header = " & ".join(cols) + " \\\\ \\hline"
    body = [" & ".join(str(c) for c in r) + " \\\\" for r in rows]

    return "\n".join(
        [
            "\\begin{tabular}{" + "l" * len(cols) + "}",
            "\\hline",
            header,
            *body,
            "\\hline",
            "\\end{tabular}",
        ]
    )
