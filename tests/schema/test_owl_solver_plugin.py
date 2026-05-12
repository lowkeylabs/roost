import inspect

from owlplanner.config.defaults import (
    default_config,
)

import owlroost.schema.plugins.owl_solver as mod
from owlroost.schema.bootstrap import (
    build_registry,
)

# =========================================================
# Solver Fields Registered
# =========================================================


def test_solver_fields_registered():
    """
    Solver fields derived from Owl defaults
    should exist in registry.
    """

    reg = build_registry()

    solver_defaults = default_config()["solver_options"]

    expected = [f"solver_options.{k}" for k in solver_defaults]

    for name in expected:
        assert reg.get(name)


# =========================================================
# Defaults Propagate
# =========================================================


def test_solver_defaults_propagate():
    """
    Owl default values should propagate
    into FieldSpec.default.
    """

    reg = build_registry()

    f = reg.get("solver_options.bequest")

    assert f.default is not None


# =========================================================
# Dtype Inference
# =========================================================


def test_solver_dtype_inference():
    """
    Solver dtypes should be inferred
    from Owl defaults.
    """

    reg = build_registry()

    f = reg.get("solver_options.bequest")

    assert f.dtype in (
        int,
        float,
    )


# =========================================================
# Safe UI Bridge Access
# =========================================================


def test_solver_plugin_uses_safe_ui_bridge_access():
    """
    OwlSolverPlugin should avoid fragile
    direct symbol imports from ui_bridge.
    """

    src = inspect.getsource(mod)

    assert "from owlplanner.config.ui_bridge import" not in src

    assert "getattr(" in src


# =========================================================
# All Solver Defaults Registered
# =========================================================


def test_all_solver_defaults_registered():
    """
    Every Owl solver default should
    appear in registry automatically.
    """

    reg = build_registry()

    solver_opts = default_config()["solver_options"]

    for key in solver_opts:
        name = f"solver_options.{key}"

        assert reg.get(name)


# =========================================================
# No Display Fields In Schema Registry
# =========================================================


def test_no_display_fields_in_schema_registry():
    """
    Display-only fields should never
    leak into SchemaRegistry.
    """

    reg = build_registry()

    for f in reg.all():
        assert not f.name.startswith("display.")


# =========================================================
# Registry Field Names Unique
# =========================================================


def test_registry_field_names_unique():
    """
    Registry should never contain
    duplicate field names.
    """

    reg = build_registry()

    names = [f.name for f in reg.all()]

    assert len(names) == len(set(names))
