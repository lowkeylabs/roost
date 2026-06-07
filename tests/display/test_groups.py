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

    return reg


# =========================================================
# Loading
# =========================================================


def test_example_groups_load():
    reg = build_registry()

    expected = {
        "example.scalar",
        "example.overlays",
        "example.synthetic",
        "example.profiles",
        "example.summary",
        "example.architecture",
    }

    for group_name in expected:
        assert reg.has_group(
            group_name,
        )


def test_testing_groups_load():
    reg = build_registry()

    expected = {
        "testing.basic",
        "testing.boolean",
        "testing.composed",
        "testing.summary",
        "testing.expansion",
    }

    for group_name in expected:
        assert reg.has_group(
            group_name,
        )


# =========================================================
# Contents
# =========================================================


def test_example_overlays_group_contents():
    reg = build_registry()

    group = reg.get_group(
        "example.overlays",
    )

    assert "example.bequest_overlay" in group.entries

    assert "example.runtime_metric" in group.entries


def test_example_summary_is_nested():
    reg = build_registry()

    group = reg.get_group(
        "example.summary",
    )

    assert ("group", "example.overlays") in group.entries

    assert ("group", "example.synthetic") in group.entries


# =========================================================
# Expansion
# =========================================================


def test_testing_expansion_group_expands():
    reg = build_registry()

    expanded = reg.expand_group(
        "testing.expansion",
    )

    assert "testing.scalar" in expanded

    assert "testing.string" in expanded

    assert "testing.boolean" in expanded

    assert "testing.composed" in expanded

    assert "testing.semantic" in expanded
