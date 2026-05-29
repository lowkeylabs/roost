PREFERRED_ORDER = {
    "method": 0,
    "from": 1,
    "to": 2,
}


def format_value(value, fmt: str | None):
    if value is None:
        return "."

    # -------------------------------------------------
    # SPECIAL FORMATTERS (must come before list logic)
    # -------------------------------------------------

    if fmt == "boolean_flag":
        if value is None:
            return "-"
        return "Yes" if value else "-"

    if fmt == "count_ratio":
        if not value:
            return "-"
        count, total = value
        return f"{int(count)}/{int(total)}"

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

    if fmt == "overrides":
        if not value:
            return "-"

        if isinstance(value, dict):
            PREFERRED_ORDER = {
                "method": 0,
                "from": 1,
                "to": 2,
            }

            ALIASES = {
                "rsmethod": "method",
                "rsfrom": "from",
                "rsto": "to",
            }

            def normalize_key(k):
                if isinstance(k, str):
                    k = k.replace("fixed_income.social_security_ages", "ss_ages")
                    k = k.replace("solver_options.spendingSlack", "spendSlack")
                    k = k.replace("rates_selection.", "")
                return k

            def sort_key(item):
                k, _ = item
                k_clean = normalize_key(k)
                return (PREFERRED_ORDER.get(k_clean, 99), k_clean)

            lines = []

            for k, v in sorted(value.items(), key=sort_key):
                k_clean = normalize_key(k)
                k_display = ALIASES.get(k_clean, k_clean)

                v_str = format_value(v, None)

                lines.append(f"{k_display}\n{v_str}")

            return "\n".join(lines)

        return str(value)

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

    if fmt == "currency_short":
        try:
            v = float(value)

            if v == 0:
                return "$0"

            if abs(v) >= 1_000_000:
                return f"${v / 1_000_000:.1f}M".rstrip("0").rstrip(".")

            if abs(v) >= 1_000:
                return f"${v / 1_000:.0f}K"

            return f"${int(v)}"

        except Exception:
            return str(value)

    if fmt == "percent":
        try:
            return f"{value:,.0%}"
        except Exception:
            return str(value)

    if fmt == "percent1":
        try:
            return f"{value:,.1%}"
        except Exception:
            return str(value)

    if fmt == "percent2":
        try:
            return f"{value:,.2%}"
        except Exception:
            return str(value)

    if fmt == "currency_k":
        try:
            return f"${value / 1000.0:,.0f} k"
        except Exception:
            return str(value)

    if fmt == "float1":
        try:
            return f"{value:,.1f}"
        except Exception:
            return str(value)

    if fmt == "float1_k":
        try:
            v = round(value / 1000.0, 1)
            return f"{v:,.1f}"
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

    if fmt == "age_ym":
        try:
            if value is None:
                return "-"

            v = float(value)
            years = int(v)
            months = int(round((v - years) * 12))

            # handle rounding edge case
            if months == 12:
                years += 1
                months = 0

            return f"{years}y {months}m"
        except Exception:
            return str(value)

    if fmt == "time_hms":
        try:
            import datetime

            if value is None:
                return "-"

            # value is epoch seconds
            dt = datetime.datetime.fromtimestamp(float(value))

            return dt.strftime("%H:%M:%S")
        except Exception:
            return str(value)

    if fmt == "duration_hms":
        try:
            if value is None:
                return "-"

            total = int(round(float(value)))

            hours = total // 3600
            minutes = (total % 3600) // 60
            seconds = total % 60

            if hours > 0:
                return f"{hours}:{minutes:02d}:{seconds:02d}"
            elif minutes > 0:
                return f"{minutes}:{seconds:02d}"
            else:
                return f"{seconds}s"

        except Exception:
            return str(value)

    # -------------------------------------------------
    # FALLBACK
    # -------------------------------------------------

    return str(value)
