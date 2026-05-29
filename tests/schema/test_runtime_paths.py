from __future__ import annotations

from owlroost.schema.specs import (
    FieldSpec,
)

# =========================================================
# Runtime Paths
# =========================================================


def test_empty_runtime_path():
    f = FieldSpec(
        name="root",
    )

    assert f.path == ()


def test_nested_runtime_path():
    f = FieldSpec(
        name="financial.spending.total.today",
        path=(
            "financial",
            "spending",
            "total",
            "today",
        ),
    )

    assert f.path == (
        "financial",
        "spending",
        "total",
        "today",
    )


def test_runtime_path_type_normalized():
    f = FieldSpec(
        name="financial.spending.total.today",
        path=(
            "financial",
            "spending",
            "total",
            "today",
        ),
    )

    assert isinstance(
        f.path,
        tuple,
    )


def test_runtime_path_matches_name():
    f = FieldSpec(
        name="timing.elapsed_seconds",
        path=(
            "timing",
            "elapsed_seconds",
        ),
    )

    assert ".".join(f.path) == f.name
