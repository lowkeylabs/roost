from pathlib import Path

import toml


def toml_plan_name(path: str) -> str:
    """
    Extract Plan Name from an OWL TOML file.

    If case_name is missing, fallback to filename stem.
    """

    p = Path(path)

    if not p.exists():
        raise FileNotFoundError(f"TOML file not found: {p}")

    data = toml.load(p)

    name = data.get("case_name")

    if not name:
        # Fallback: filename without extension
        name = p.stem

    # Normalize for filesystem safety
    return str(name).strip().replace(" ", "_").replace("&", "and")
