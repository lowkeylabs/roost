def format_value(value, fmt: str | None):
    if value is None:
        return "."

    # -------------------------------------------------
    # LIST HANDLING (recursive)
    # -------------------------------------------------
    if isinstance(value, list):
        # Recursively format each element
        formatted_items = [format_value(v, fmt) for v in value]

        # Domain rule: two values → slash
        if len(formatted_items) == 2:
            return "/".join(formatted_items)

        return ", ".join(formatted_items)

    if fmt == "truncate_20":
        try:
            s = str(value)
            if len(s) > 20:
                return s[:17] + "..."
            return s
        except Exception:
            return str(value)

    # ---- scalar formatting ----
    if fmt == "currency":
        try:
            return f"${value:,.0f}"
        except Exception:
            return str(value)

    if fmt == "currency_k":
        try:
            # value already in thousands
            return f"${value:,.0f} k"
        except Exception:
            return str(value)

    if fmt == "float1":
        try:
            return f"{value:,.1f}"
        except Exception:
            return str(value)

    if fmt == "int_dash":
        try:
            if value == 0:
                return " - "
            else:
                return f"{int(value)}"
        except Exception:
            return str(value)

    if fmt == "float1_dash":
        try:
            if value == 0:
                return " - "
            else:
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

    if fmt == "int":
        try:
            return f"{int(value)}"
        except Exception:
            return str(value)

    return str(value)
