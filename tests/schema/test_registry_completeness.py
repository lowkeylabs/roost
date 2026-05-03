def test_registry_covers_all_owl_fields():
    from owlplanner.config.schema import CaseConfig

    from owlroost.schema.plugins.owl import OwlSchemaPlugin
    from owlroost.schema.registry import SchemaRegistry
    from owlroost.schema.runtime_defaults import (
        build_runtime_defaults,
        get_from_path,
    )
    from owlroost.schema.utils import unwrap_annotation

    # ----------------------------------------
    # Helper: walk pydantic model
    # ----------------------------------------
    def walk_model(prefix, model):
        for name, field in model.model_fields.items():
            full_name = f"{prefix}.{name}" if prefix else name
            yield full_name, field

            annotation = unwrap_annotation(field.annotation)
            if hasattr(annotation, "model_fields"):
                yield from walk_model(full_name, annotation)

    # ----------------------------------------
    # Helper: walk runtime dict
    # ----------------------------------------
    def walk_dict(prefix, d):
        for k, v in d.items():
            full = f"{prefix}.{k}" if prefix else k
            yield full
            if isinstance(v, dict):
                yield from walk_dict(full, v)

    # ----------------------------------------
    # Expected (schema)
    # ----------------------------------------
    expected = {name for name, _ in walk_model("", CaseConfig)}

    # ----------------------------------------
    # Runtime defaults (OWL truth)
    # ----------------------------------------
    runtime_defaults = build_runtime_defaults()
    runtime_fields = set(walk_dict("", runtime_defaults))

    # ----------------------------------------
    # Registry
    # ----------------------------------------
    reg = SchemaRegistry()
    OwlSchemaPlugin().register(reg)

    registered = {field.name for field in reg.all()}

    assert len(registered) == len(list(reg.all()))

    # ----------------------------------------
    # 1. Schema coverage (must still hold)
    # ----------------------------------------
    missing = expected - registered
    assert not missing, f"Missing fields in registry: {missing}"

    # ----------------------------------------
    # 2. Runtime coverage (NEW)
    # ----------------------------------------
    missing_runtime = runtime_fields - registered

    allowed_missing = set()  # keep empty unless needed
    unexpected_runtime = missing_runtime - allowed_missing

    assert not unexpected_runtime, f"Runtime fields missing from registry: {unexpected_runtime}"

    # ----------------------------------------
    # 3. Registry → runtime resolvability (NEW)
    # ----------------------------------------
    unresolved = []

    for f in reg.all():
        if not f.path:
            continue

        val = get_from_path(runtime_defaults, f.path)

        # Only flag if parent exists but child does not
        parent = get_from_path(runtime_defaults, f.path[:-1])

        if isinstance(parent, dict) and f.path[-1] in parent:
            if val is None:
                unresolved.append(".".join(f.path))

    assert not unresolved, f"Registry paths not found in runtime defaults: {unresolved}"
