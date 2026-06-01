# src/owlroost/tools/generate_explain_metadata.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

import re
from pathlib import Path

# =========================================================
# Paths
# =========================================================

THIS_FILE = Path(__file__).resolve()

OWLROOST_ROOT = THIS_FILE.parents[1]

OUTPUT_DIR = OWLROOST_ROOT / "schema" / "generated"

OUTPUT_FILE = OUTPUT_DIR / "owl_parameter_docs.py"

# =========================================================
# Locate Owl PARAMETERS.md
# =========================================================

# ---------------------------------------------
# Assumes editable sibling checkout:
#
#   ../owl-planner/
#
# Can be adjusted later if needed.
# ---------------------------------------------

OWL_PARAMETERS_MD = OWLROOST_ROOT.parents[2] / "owl-planner" / "PARAMETERS.md"

# =========================================================
# Regex Helpers
# =========================================================

SECTION_RE = re.compile(r"^##+\s+(.+?)\s*$")

TABLE_ROW_RE = re.compile(r"^\|(.+)\|$")

# =========================================================
# Utilities
# =========================================================


def clean_section_name(
    text,
):
    """
    Remove Quarto/UI wrappers from section names.

    Examples
    --------
    :orange[[solver_options]]
        -> solver_options

    :orange[root_level_parameters]
        -> root_level_parameters
    """

    text = text.strip()

    # -----------------------------------------------------
    # Remove :orange[
    # -----------------------------------------------------

    if text.startswith(":orange["):
        text = text[len(":orange[") :]

    # -----------------------------------------------------
    # Remove outer brackets
    # -----------------------------------------------------

    text = text.rstrip("]")

    # -----------------------------------------------------
    # Remove doubled [[ ]]
    # -----------------------------------------------------

    text = text.strip("[]")

    return text


def clean_cell(
    text,
):
    """
    Clean markdown table cell.
    """

    text = text.strip()

    # remove markdown backticks
    text = text.replace("`", "")

    # collapse whitespace
    text = " ".join(text.split())

    return text


def infer_units(
    description,
):
    """
    Infer semantic units from description text.
    """

    desc = description.lower()

    if "thousand" in desc and "dollar" in desc:
        return "thousands_usd"

    if "dollar" in desc:
        return "usd"

    if "percent" in desc:
        return "percent"

    if "year" in desc:
        return "years"

    return None


# =========================================================
# Parser
# =========================================================


def parse_parameters_md(
    path,
):
    """
    Parse PARAMETERS.md into structured metadata.
    """

    text = path.read_text(encoding="utf-8")

    lines = text.splitlines()

    docs = {}

    current_section = None

    in_table = False

    for line in lines:
        stripped = line.strip()

        # -------------------------------------------------
        # Section headers
        # -------------------------------------------------

        m = SECTION_RE.match(stripped)

        if m:
            current_section = clean_section_name(m.group(1).strip().lower().replace(" ", "_"))

            in_table = False

            continue

        # -------------------------------------------------
        # Markdown table row
        # -------------------------------------------------

        if stripped.startswith("|"):
            # separator row
            if "---" in stripped:
                continue

            m = TABLE_ROW_RE.match(stripped)

            if not m:
                continue

            raw = m.group(1)

            cells = [clean_cell(c) for c in raw.split("|")]

            # skip malformed rows
            if len(cells) < 3:
                continue

            # detect table header
            header0 = cells[0].lower()

            if header0 in {
                "parameter",
                "name",
                "field",
            }:
                in_table = True
                continue

            if not in_table:
                continue

            # -------------------------------------------------
            # Extract fields
            # -------------------------------------------------

            param_name = cells[0]
            param_type = cells[1]
            description = cells[2]

            if not param_name:
                continue

            docs[param_name] = {
                "section": current_section,
                "type": param_type,
                "description": description,
                "units": infer_units(description),
                "notes": None,
            }

    return docs


# =========================================================
# Python Emitter
# =========================================================


def emit_python_module(
    docs,
):
    """
    Emit generated Python module.
    """

    lines = []

    lines.append('"""')
    lines.append("AUTO-GENERATED FILE.")
    lines.append("")
    lines.append("Generated by:")
    lines.append("    owlroost.tools.generate_explain_metadata")
    lines.append("")
    lines.append("DO NOT EDIT MANUALLY.")
    lines.append('"""')
    lines.append("")
    lines.append("from __future__ import annotations")
    lines.append("")
    lines.append("OWL_PARAMETER_DOCS = {")

    for key in sorted(docs):
        item = docs[key]

        lines.append(f'    "{key}": {{')

        for k, v in item.items():
            lines.append(f"        {k!r}: {v!r},")

        lines.append("    },")

    lines.append("}")
    lines.append("")

    return "\n".join(lines)


# =========================================================
# Main
# =========================================================


def main():
    """
    Generate structured OWL parameter metadata.
    """

    print(f"Reading: {OWL_PARAMETERS_MD}")

    if not OWL_PARAMETERS_MD.exists():
        raise FileNotFoundError(f"Could not locate PARAMETERS.md:\n{OWL_PARAMETERS_MD}")

    docs = parse_parameters_md(OWL_PARAMETERS_MD)

    print(f"Parsed {len(docs)} parameters.")

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = emit_python_module(docs)

    OUTPUT_FILE.write_text(
        output,
        encoding="utf-8",
    )

    print(f"Wrote:\n{OUTPUT_FILE}")


# =========================================================
# Entry
# =========================================================

if __name__ == "__main__":
    main()
