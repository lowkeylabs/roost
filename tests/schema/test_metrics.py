def test_metrics_fields_registered():
    from owlroost.schema.bootstrap import build_registry

    reg = build_registry()

    assert reg.get("financial.spending.year0.future")
    assert reg.get("risk.summary.overall_risk")
    assert reg.get("complexity.num_constraints")


def test_metrics_fields_marked_as_output():
    from owlroost.schema.bootstrap import build_registry

    reg = build_registry()

    field = reg.get("financial.spending.year0.future")

    assert field.source == "output"


def test_input_and_output_coexist():
    from owlroost.schema.bootstrap import build_registry

    reg = build_registry()

    assert reg.get("basic_info.names")  # input
    assert reg.get("financial.spending.year0")  # output
