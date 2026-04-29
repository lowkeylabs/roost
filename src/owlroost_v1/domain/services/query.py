from ..metrics.view_registry import view_keys


def apply_sort(rows, view, sort_key):
    if not sort_key:
        return rows

    direction = -1
    key = sort_key

    if sort_key.startswith("+"):
        direction = 1
        key = sort_key[1:]
    elif sort_key.startswith("-"):
        key = sort_key[1:]

    valid_keys = view_keys(view)

    if key not in valid_keys:
        raise ValueError(f"Invalid sort key '{key}'. Valid: {', '.join(sorted(valid_keys))}")

    def safe_value(row):
        v = row.get(key)
        if v is None:
            return float("inf") if direction == 1 else float("-inf")
        return v

    return sorted(rows, key=safe_value, reverse=(direction == -1))


def parse_filter(expr):
    # in operator
    if "=in:" in expr:
        key, val = expr.split("=in:", 1)
        values = [v.strip() for v in val.split(",")]
        return key.strip(), "in", values

    for op in ["=", ">", "<"]:
        if op in expr:
            key, val = expr.split(op, 1)
            return key.strip(), op, val.strip()

    raise ValueError(f"Invalid filter '{expr}'")


def coerce_value(val):
    if isinstance(val, list):
        return [coerce_value(v) for v in val]

    try:
        return float(val)
    except ValueError:
        return val.lower()


def apply_filters(rows, view, filters):
    if not filters:
        return rows

    valid_keys = view_keys(view)

    parsed = []
    for f in filters:
        key, op, val = parse_filter(f)

        if key not in valid_keys:
            raise ValueError(f"Invalid filter key '{key}'. Valid: {', '.join(sorted(valid_keys))}")

        parsed.append((key, op, coerce_value(val)))

    def match(row):
        for key, op, val in parsed:
            rv = row.get(key)

            if rv is None:
                return False

            rv_cmp = rv.lower() if isinstance(rv, str) else rv

            if op == "=" and rv_cmp != val:
                return False

            if op == "in":
                if rv_cmp not in val:
                    return False

            if op == ">" and (not isinstance(rv_cmp, (int, float)) or rv_cmp <= val):  # noqa: UP038
                return False

            if op == "<" and (not isinstance(rv_cmp, (int, float)) or rv_cmp >= val):  # noqa: UP038
                return False

        return True

    return [r for r in rows if match(r)]


def apply_top(rows, top_n):
    if top_n is None:
        return rows
    return rows[:top_n] if top_n > 0 else []
