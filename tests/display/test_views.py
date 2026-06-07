from __future__ import annotations

from owlroost.display.fields import (
    register_all_display_fields,
)
from owlroost.display.groups import (
    register_display_groups,
)
from owlroost.display.registry import (
    DisplayRegistry,
)
from owlroost.display.views import (
    register_display_views,
)

# =========================================================
# Fixtures
# =========================================================


def build_registry() -> DisplayRegistry:
    reg = DisplayRegistry()

    register_all_display_fields(
        reg,
    )

    register_display_groups(
        reg,
    )

    register_display_views(
        reg,
    )

    return reg


# =========================================================
# Loading
# =========================================================


def test_example_views_load():
    reg = build_registry()

    expected = {
        ("case", "example-scalar"),
        ("case", "example-overlays"),
        ("case", "example-synthetic"),
        ("case", "example-profiles"),
        ("case", "example-summary"),
        ("case", "example-architecture"),
        ("catalog", "example-catalog"),
    }

    for level, name in expected:
        assert reg.has_view(
            level,
            name,
        )


def test_testing_views_load():
    reg = build_registry()

    expected = {
        ("case", "testing-basic"),
        ("case", "testing-boolean"),
        ("case", "testing-composed"),
        ("case", "testing-summary"),
        ("case", "testing-expansion"),
        ("case", "testing-fixture"),
    }

    for level, name in expected:
        assert reg.has_view(
            level,
            name,
        )


# =========================================================
# View Contents
# =========================================================


def test_example_architecture_view_references_group():
    reg = build_registry()

    view = reg.get_view(
        "case",
        "example-architecture",
    )

    assert ("group", "example.architecture") in view.entries


# =========================================================
# Expansion
# =========================================================


def test_example_architecture_view_expands():
    reg = build_registry()

    expanded = reg.expand_view_fields(
        "case",
        "example-architecture",
    )

    assert "example.synthetic" in expanded

    assert "example.composed" in expanded

    assert "example.bequest_overlay" in expanded

    assert "example.runtime_metric" in expanded


def test_testing_fixture_view_expands():
    reg = build_registry()

    expanded = reg.expand_view_fields(
        "case",
        "testing-fixture",
    )

    assert "testing.scalar" in expanded

    assert "testing.string" in expanded

    assert "testing.boolean" in expanded

    assert "testing.composed" in expanded

    assert "testing.semantic" in expanded
