from __future__ import annotations

from owlroost.metrics.aggregation.registry import (
    AGG_FUNCS,
    get_aggregation_func,
    list_aggregations,
)


def test_builtin_aggregations_registered():
    assert "median" in AGG_FUNCS

    assert "p90" in AGG_FUNCS

    assert "cnt" in AGG_FUNCS


def test_get_aggregation_func():
    func = get_aggregation_func("median")

    assert callable(func)


def test_list_aggregations_sorted():
    names = list_aggregations()

    assert names == sorted(names)
