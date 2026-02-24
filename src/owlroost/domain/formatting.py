def format_value(value, fmt: str | None):
    if value is None:
        return "."

    # -------------------------------------------------
    # SPECIAL FORMATTERS (must come before list logic)
    # -------------------------------------------------

    if fmt == "allocation":
        if not value:
            return "-"

        normalized = []

        for person in value:
            # If structure is [[[...],[...]], ...]
            # take first regime block
            if isinstance(person, list) and person and isinstance(person[0], list):
                normalized.append(person[0])
            else:
                normalized.append(person)

        return "/".join("[" + ",".join(str(int(x)) for x in alloc) + "]" for alloc in normalized)

    # -------------------------------------------------
    # DEFAULT FLOAT NORMALIZATION (when no explicit fmt)
    # -------------------------------------------------

    if fmt is None and isinstance(value, float):
        # Remove floating point noise like 7.000000000000001
        s = f"{value:.6f}".rstrip("0").rstrip(".")
        return s

    # -------------------------------------------------
    # LIST HANDLING (recursive)
    # -------------------------------------------------

    if isinstance(value, list):
        formatted_items = []

        for v in value:
            if isinstance(v, float) and fmt is None:
                s = f"{v:.6f}".rstrip("0").rstrip(".")
                formatted_items.append(s)
            else:
                formatted_items.append(format_value(v, fmt))

        # Domain rule: two values → slash
        if len(formatted_items) == 2:
            return "/".join(formatted_items)

        return ",".join(formatted_items)

    # -------------------------------------------------
    # STRING TRUNCATION
    # -------------------------------------------------

    if fmt == "truncate_20":
        try:
            s = str(value)
            if len(s) > 20:
                return s[:17] + "..."
            return s
        except Exception:
            return str(value)

    # -------------------------------------------------
    # SCALAR FORMATTERS
    # -------------------------------------------------

    if fmt == "check":
        return "✓" if value else "–"

    if fmt == "currency":
        try:
            return f"${value:,.0f}"
        except Exception:
            return str(value)

    if fmt == "percent":
        try:
            return f"{value:,.0%}"
        except Exception:
            return str(value)

    if fmt == "percent2":
        try:
            return f"{value:,.2%}"
        except Exception:
            return str(value)

    if fmt == "currency_k":
        try:
            return f"${value:,.0f} k"
        except Exception:
            return str(value)

    if fmt == "float1":
        try:
            return f"{value:,.1f}"
        except Exception:
            return str(value)

    if fmt == "float2":
        try:
            return f"{value:,.2f}"
        except Exception:
            return str(value)

    if fmt == "float3":
        try:
            return f"{value:.3f}"
        except Exception:
            return str(value)

    if fmt == "float1_dash":
        try:
            return " - " if value == 0 else f"{value:,.1f}"
        except Exception:
            return str(value)

    if fmt == "int_dash":
        try:
            return " - " if value == 0 else f"{int(value)}"
        except Exception:
            return str(value)

    if fmt == "int":
        try:
            return f"{int(value)}"
        except Exception:
            return str(value)

    # -------------------------------------------------
    # FALLBACK
    # -------------------------------------------------

    return str(value)
