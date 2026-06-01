# src/owlroost/display/renderers/markdown_table.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations


def render_markdown_table(table):
    cols = table.columns
    rows = table.rows

    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"

    body = ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]

    return "\n".join([header, sep] + body)
