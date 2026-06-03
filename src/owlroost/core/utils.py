# src/owlroost/core/utils.py

from pathlib import Path

def normalize_module_path(
    file_name,
):
    p = Path(file_name)

    parts = p.parts

    try:
        idx = parts.index("owlroost")

        return "/".join(
            parts[idx + 1 :]
        )

    except ValueError:
        return p.name