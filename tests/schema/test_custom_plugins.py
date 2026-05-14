# tests/schema/test_custom_plugins.py


def test_longevity_plugin_registers_fields():
    from owlroost.schema.plugins.longevity import LongevityPlugin
    from owlroost.schema.registry import SchemaRegistry

    reg = SchemaRegistry()
    LongevityPlugin().register(reg)

    field = reg.get("longevity.sex")

    assert field.name == "longevity.sex"
    assert field.source == "input"


def test_spending_policy_plugin_registers_fields():
    from owlroost.schema.plugins.spending_policy import SpendingPolicyPlugin
    from owlroost.schema.registry import SchemaRegistry

    reg = SchemaRegistry()
    SpendingPolicyPlugin().register(reg)

    field = reg.get("spending_policy.essential_spending")

    assert field.name == "spending_policy.essential_spending"


def test_system_models_registered():
    from owlroost.schema.bootstrap import build_registry

    reg = build_registry()

    assert reg.get("roost_runtime.trials_per_run")
    assert reg.get("roost_runtime.master_seed")
