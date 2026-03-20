import math
import statistics


def mean(values):
    return statistics.mean(values) if values else None


def median(values):
    return statistics.median(values) if values else None


def sum_(values):
    return sum(values) if values else 0


def min_(values):
    return min(values) if values else None


def max_(values):
    return max(values) if values else None


def percentile(values, p):
    if not values:
        return None
    values = sorted(values)
    k = (len(values) - 1) * (p / 100)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return values[int(k)]
    return values[f] + (values[c] - values[f]) * (k - f)


def len_(values):
    return len(values) if values else 0


AGG_FUNCS = {
    "mean": mean,
    "pct": mean,
    "cnt": len_,
    "median": median,
    "sum": sum_,
    "min": min_,
    "max": max_,
    "p10": lambda v: percentile(v, 10),
    "p90": lambda v: percentile(v, 90),
}
