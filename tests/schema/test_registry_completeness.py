def test_registry_covers_all_owl_fields():
    from owlplanner.config.schema import CaseConfig

    from owlroost.schema.plugins.owl import OwlSchemaPlugin
    from owlroost.schema.registry import SchemaRegistry
    from owlroost.schema.utils import unwrap_annotation

    # ----------------------------------------
    # Helper: walk pydantic model
    # ----------------------------------------
    def walk_model(prefix, model):
        for name, field in model.model_fields.items():
            full_name = f"{prefix}.{name}" if prefix else name
            yield full_name, field

            # recurse into nested models
            annotation = unwrap_annotation(field.annotation)
            if hasattr(annotation, "model_fields"):
                yield from walk_model(full_name, annotation)

    # ----------------------------------------
    # Build expected field set
    # ----------------------------------------
    expected = set()

    for name, _ in walk_model("", CaseConfig):
        expected.add(name)

    # ----------------------------------------
    # Build registry
    # ----------------------------------------
    reg = SchemaRegistry()
    OwlSchemaPlugin().register(reg)

    registered = {field.name for field in reg.all()}

    # ----------------------------------------
    # Compare
    # ----------------------------------------
    missing = expected - registered
    extra = registered - expected

    assert not missing, f"Missing fields in registry: {missing}"
    assert not extra, f"Unexpected extra fields: {extra}"
