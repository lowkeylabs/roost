from __future__ import annotations

from collections.abc import Callable
from statistics import mean, median
from typing import Any

from ..formatting import format_value

# =========================================================
# Helpers
# =========================================================


def _clean(values: list[Any]) -> list[float]:
    return [v for v in values if v is not None]


# =========================================================
# Core Patterns (fmt-aware)
# =========================================================


def series_mean(fmt: str | None = None) -> Callable[[list[Any], list[Any], list[dict]], str]:
    def fn(values, raw, rows):
        clean = _clean(raw)
        if not clean:
            return "No data"

        v = mean(clean)
        return f"Average {format_value(v, fmt)}"

    return fn


def series_median(fmt: str | None = None) -> Callable[[list[Any], list[Any], list[dict]], str]:
    def fn(values, raw, rows):
        clean = _clean(raw)
        if not clean:
            return "No data"

        v = median(clean)
        return f"Median {format_value(v, fmt)}"

    return fn


def series_min_max(fmt: str | None = None) -> Callable[[list[Any], list[Any], list[dict]], str]:
    def fn(values, raw, rows):
        clean = _clean(raw)
        if not clean:
            return "No data"

        lo = format_value(min(clean), fmt)
        hi = format_value(max(clean), fmt)

        return f"Range {lo} → {hi}"

    return fn


# =========================================================
# Success / Boolean Patterns
# =========================================================


def series_success_rate() -> Callable[[list[Any], list[Any], list[dict]], str]:
    def fn(values, raw, rows):
        clean = _clean(raw)
        if not clean:
            return "No data"

        success = sum(1 for v in clean if v)
        total = len(clean)

        return f"{success}/{total} succeeded ({format_value(success / total, 'percent')})"

    return fn


def series_failure_rate() -> Callable[[list[Any], list[Any], list[dict]], str]:
    def fn(values, raw, rows):
        clean = _clean(raw)
        if not clean:
            return "No data"

        fail = sum(1 for v in clean if not v)
        total = len(clean)

        return f"{fail}/{total} failed ({format_value(fail / total, 'percent')})"

    return fn


# =========================================================
# Threshold / Risk Patterns
# =========================================================


def series_below(threshold: float, fmt: str | None = None) -> Callable:
    def fn(values, raw, rows):
        clean = _clean(raw)
        if not clean:
            return "No data"

        count = sum(1 for v in clean if v < threshold)
        total = len(clean)

        return (
            f"{count}/{total} below {format_value(threshold, fmt)} "
            f"({format_value(count / total, 'percent')})"
        )

    return fn


def series_above(threshold: float, fmt: str | None = None) -> Callable:
    def fn(values, raw, rows):
        clean = _clean(raw)
        if not clean:
            return "No data"

        count = sum(1 for v in clean if v > threshold)
        total = len(clean)

        return (
            f"{count}/{total} above {format_value(threshold, fmt)} "
            f"({format_value(count / total, 'percent')})"
        )

    return fn


# =========================================================
# Distribution Shape
# =========================================================


def series_distribution_summary(fmt: str | None = None) -> Callable:
    def fn(values, raw, rows):
        clean = sorted(_clean(raw))
        if not clean:
            return "No data"

        n = len(clean)

        p10 = clean[int(0.1 * (n - 1))]
        p50 = median(clean)
        p90 = clean[int(0.9 * (n - 1))]

        return (
            f"P10 {format_value(p10, fmt)}, "
            f"P50 {format_value(p50, fmt)}, "
            f"P90 {format_value(p90, fmt)}"
        )

    return fn


# =========================================================
# Financial Risk Patterns
# =========================================================


def series_tail_loss(threshold: float, fmt: str | None = None) -> Callable:
    def fn(values, raw, rows):
        clean = _clean(raw)
        if not clean:
            return "No data"

        losses = [v for v in clean if v < threshold]
        total = len(clean)

        if not losses:
            return "No losses"

        return (
            f"{len(losses)}/{total} losses "
            f"({format_value(len(losses) / total, 'percent')}), "
            f"worst {format_value(min(losses), fmt)}"
        )

    return fn


def series_worst_case(fmt: str | None = None) -> Callable:
    def fn(values, raw, rows):
        clean = _clean(raw)
        if not clean:
            return "No data"

        return f"Worst {format_value(min(clean), fmt)}"

    return fn


def series_best_case(fmt: str | None = None) -> Callable:
    def fn(values, raw, rows):
        clean = _clean(raw)
        if not clean:
            return "No data"

        return f"Best {format_value(max(clean), fmt)}"

    return fn
