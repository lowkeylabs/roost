# src/owlroost/domain/metrics/definitions/utils.py


RATES_METHOD_ABBR = {
    "historical": "Hist",
    "historical average": "HAvg",
    "histogaussian": "HGauss",
    "histolognormal": "HLog",
    "bootstrap_sor": "bSor",
    "var": "VaR",
    "garch_dcc": "Gdcc",
}

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------


def _debug_row(r):
    import json

    # if os.getenv("ROOST_DEBUG_ELAPSED") == "1":
    print("\n\n[DEBUG] row keys:", list(r.keys()))
    print("\n\n[DEBUG] row:", json.dumps(r, indent=2, default=str))

    return None


def _bool_value(value: bool, true_msg: str, false_msg: str) -> str:
    return true_msg if value else false_msg


def wrap_value_fn(fn):
    def series_fn(values, raw, rows):
        clean = [v for v in values if v is not None]
        if not clean:
            return "-"
        return fn(clean[0], rows[0] if rows else None)

    return series_fn


def _as_float(v):
    if v is None:
        return None

    # already numeric
    if isinstance(v, (int, float)):
        return float(v)

    # percent string
    if isinstance(v, str):
        if v.endswith("%"):
            return float(v.strip("%")) / 100.0
        if "/" in v:
            num, den = v.split("/")
            return float(num) / float(den)

    # 🔥 CRITICAL: handle tuple (count_ratio)
    if isinstance(v, tuple) and len(v) == 2:
        num, den = v
        try:
            return float(num) / float(den) if den else None
        except Exception:
            return None

    return None


def _format_age_ym(age):
    if age is None:
        return "-"
    try:
        years = int(age)
        months = int(round((age - years) * 12))
        if months == 12:
            years += 1
            months = 0
        return f"{years}y {months}m"
    except Exception:
        return "-"
