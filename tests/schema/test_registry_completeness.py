def test_registry_covers_all_owl_fields():
    from owlplanner.config.schema import CaseConfig

    from owlroost.schema.plugins.owl import OwlSchemaPlugin
    from owlroost.schema.registry import SchemaRegistry
    from owlroost.schema.runtime_defaults import (
        build_runtime_defaults,
        get_from_path,
    )
    from owlroost.schema.utils import unwrap_annotation

    # =====================================================
    # Constants
    # =====================================================

    VALID_SOURCES = {
        "input",
        "discovered",
        "derived",
        "metric",
        "internal",
    }

    VALID_LEVELS = {
        "case",
        "experiment",
        "run",
        "trial",
    }

    # =====================================================
    # Helper: walk pydantic model
    # =====================================================

    def walk_model(prefix, model):
        for name, field in model.model_fields.items():
            full_name = f"{prefix}.{name}" if prefix else name

            yield full_name, field

            annotation = unwrap_annotation(
                field.annotation,
            )

            if hasattr(
                annotation,
                "model_fields",
            ):
                yield from walk_model(
                    full_name,
                    annotation,
                )

    # =====================================================
    # Expected schema fields
    # =====================================================

    expected = {
        name
        for name, _ in walk_model(
            "",
            CaseConfig,
        )
    }

    # =====================================================
    # Runtime defaults
    # =====================================================

    runtime_defaults = build_runtime_defaults()

    # =====================================================
    # Registry
    # =====================================================

    reg = SchemaRegistry()

    OwlSchemaPlugin().register(
        reg,
    )

    fields = list(
        reg.all(),
    )

    registered = {field.name for field in fields}

    # =====================================================
    # 1. No duplicate names
    # =====================================================

    assert len(registered) == len(fields)

    # =====================================================
    # 2. OWL schema coverage
    # =====================================================

    missing = expected - registered

    assert not missing, "Missing fields in registry: " f"{missing}"

    # =====================================================
    # 3. Field semantic integrity
    # =====================================================

    invalid_sources = []
    invalid_levels = []

    for field in fields:
        if field.source not in VALID_SOURCES:
            invalid_sources.append(
                (
                    field.name,
                    field.source,
                )
            )

        if field.level not in VALID_LEVELS:
            invalid_levels.append(
                (
                    field.name,
                    field.level,
                )
            )

    assert not invalid_sources, "Invalid field sources: " f"{invalid_sources}"

    assert not invalid_levels, "Invalid field levels: " f"{invalid_levels}"

    # =====================================================
    # 4. Derived fields must define compute_fn
    # =====================================================

    missing_compute_fn = []

    for field in fields:
        if field.source == "derived":
            if field.compute_fn is None:
                missing_compute_fn.append(
                    field.name,
                )

    assert not missing_compute_fn, "Derived fields missing compute_fn: " f"{missing_compute_fn}"

    # =====================================================
    # 5. Registry → runtime resolvability
    # =====================================================

    unresolved = []

    for field in fields:
        if not field.path:
            continue

        parent = get_from_path(
            runtime_defaults,
            field.path[:-1],
        )

        if not isinstance(
            parent,
            dict,
        ):
            continue

        if field.path[-1] not in parent:
            continue

        val = get_from_path(
            runtime_defaults,
            field.path,
        )

        if val is None:
            unresolved.append(
                ".".join(field.path),
            )

    assert not unresolved, "Registry paths not found " "in runtime defaults: " f"{unresolved}"
