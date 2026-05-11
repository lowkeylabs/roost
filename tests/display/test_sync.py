# tests/display/test_sync.py

from __future__ import annotations

from owlroost.display.registry import DisplayRegistry
from owlroost.display.specs import (
    DisplayField,
    DisplayProfile,
)
from owlroost.display.sync import (
    path_to_pivot_label,
    path_to_table_label,
    sync_display_registry,
)
from owlroost.schema.registry import (
    FieldSpec,
    SchemaRegistry,
)

# =========================================================
# Helpers
# =========================================================


def build_schema_registry():
    reg = SchemaRegistry()

    reg.register(
        FieldSpec(
            name="runtime.trial_jobs",
            dtype=int,
            description="Number of parallel trial workers.",
        )
    )

    reg.register(
        FieldSpec(
            name="solver.elapsed_seconds",
            dtype=float,
            description="Elapsed runtime in seconds.",
        )
    )

    return reg


# =========================================================
# Label Helpers
# =========================================================


def test_path_to_table_label():
    assert path_to_table_label("runtime.trial_jobs") == "Trial Jobs"

    assert path_to_table_label("solver.elapsed_seconds") == "Elapsed Seconds"


def test_path_to_pivot_label():
    assert path_to_pivot_label("runtime.trial_jobs") == "Runtime Trial Jobs"

    assert path_to_pivot_label("solver.elapsed_seconds") == "Solver Elapsed Seconds"


# =========================================================
# Sync
# =========================================================


def test_sync_creates_display_fields():
    schema_reg = build_schema_registry()

    display_reg = DisplayRegistry()

    sync_display_registry(
        schema_reg,
        display_reg,
    )

    assert display_reg.has_display_field("runtime.trial_jobs")

    assert display_reg.has_display_field("solver.elapsed_seconds")


def test_sync_copies_description():
    schema_reg = build_schema_registry()

    display_reg = DisplayRegistry()

    sync_display_registry(
        schema_reg,
        display_reg,
    )

    field = display_reg.get_display_field("runtime.trial_jobs")

    assert field.description == "Number of parallel trial workers."


def test_sync_creates_profiles():
    schema_reg = build_schema_registry()

    display_reg = DisplayRegistry()

    sync_display_registry(
        schema_reg,
        display_reg,
    )

    field = display_reg.get_display_field("runtime.trial_jobs")

    assert "table" in field.profiles

    assert "pivot" in field.profiles


def test_sync_creates_table_label():
    schema_reg = build_schema_registry()

    display_reg = DisplayRegistry()

    sync_display_registry(
        schema_reg,
        display_reg,
    )

    field = display_reg.get_display_field("runtime.trial_jobs")

    assert field.profiles["table"].label == "Trial Jobs"


def test_sync_creates_pivot_label():
    schema_reg = build_schema_registry()

    display_reg = DisplayRegistry()

    sync_display_registry(
        schema_reg,
        display_reg,
    )

    field = display_reg.get_display_field("runtime.trial_jobs")

    assert field.profiles["pivot"].label == "Runtime Trial Jobs"


def test_sync_preserves_existing_display_field():
    schema_reg = build_schema_registry()

    display_reg = DisplayRegistry()

    existing = DisplayField(
        field_name="runtime.trial_jobs",
        description="Custom description",
        profiles={
            "table": DisplayProfile(
                label="Jobs",
            ),
        },
    )

    display_reg.register_display_field(existing)

    sync_display_registry(
        schema_reg,
        display_reg,
    )

    field = display_reg.get_display_field("runtime.trial_jobs")

    # ----------------------------------------
    # Ensure object preserved
    # ----------------------------------------
    assert field is existing

    # ----------------------------------------
    # Ensure override preserved
    # ----------------------------------------
    assert field.profiles["table"].label == "Jobs"

    assert field.description == "Custom description"


def test_sync_does_not_duplicate_fields():
    schema_reg = build_schema_registry()

    display_reg = DisplayRegistry()

    sync_display_registry(
        schema_reg,
        display_reg,
    )

    sync_display_registry(
        schema_reg,
        display_reg,
    )

    assert len(display_reg.all_display_fields()) == 2


def test_sync_empty_schema_registry():
    schema_reg = SchemaRegistry()

    display_reg = DisplayRegistry()

    sync_display_registry(
        schema_reg,
        display_reg,
    )

    assert len(display_reg.all_display_fields()) == 0


def test_sync_multiple_fields():
    schema_reg = build_schema_registry()

    display_reg = DisplayRegistry()

    sync_display_registry(
        schema_reg,
        display_reg,
    )

    names = {f.field_name for f in display_reg.all_display_fields()}

    assert names == {
        "runtime.trial_jobs",
        "solver.elapsed_seconds",
    }


def test_sync_profile_objects_created():
    schema_reg = build_schema_registry()

    display_reg = DisplayRegistry()

    sync_display_registry(
        schema_reg,
        display_reg,
    )

    field = display_reg.get_display_field("solver.elapsed_seconds")

    assert isinstance(
        field.profiles["table"],
        DisplayProfile,
    )

    assert isinstance(
        field.profiles["pivot"],
        DisplayProfile,
    )
