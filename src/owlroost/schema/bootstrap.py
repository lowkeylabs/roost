# src/owlroost/schema/bootstrap.py

from .plugins.longevity import LongevityPlugin
from .plugins.owl import OwlSchemaPlugin
from .plugins.spending_policy import SpendingPolicyPlugin
from .registry import SchemaRegistry


def build_registry():
    reg = SchemaRegistry()

    OwlSchemaPlugin().register(reg)
    LongevityPlugin().register(reg)
    SpendingPolicyPlugin().register(reg)

    return reg
