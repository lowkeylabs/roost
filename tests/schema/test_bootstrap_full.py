# tests/schema/test_bootstrap_full.py


def test_full_registry_contains_all_plugins():
    from owlroost.schema.bootstrap import build_registry

    reg = build_registry()

    # OWL
    assert reg.get("basic_info.names")

    # Longevity
    assert reg.get("longevity.sex")

    # Spending policy
    assert reg.get("spending_policy.essential")
