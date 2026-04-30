# src/owlroost/schema/bootstrap.py

from .plugins.longevity import LongevityPlugin
from .plugins.metrics import MetricsSchemaPlugin
from .plugins.owl import OwlSchemaPlugin
from .plugins.roost import RoostPlugin
from .plugins.runtime import RuntimePlugin
from .plugins.spending_policy import SpendingPolicyPlugin
from .plugins.trial import TrialPlugin
from .registry import SchemaRegistry


def build_registry():
    reg = SchemaRegistry()

    OwlSchemaPlugin().register(reg)
    LongevityPlugin().register(reg)
    SpendingPolicyPlugin().register(reg)

    MetricsSchemaPlugin().register(reg)

    TrialPlugin().register(reg)
    RuntimePlugin().register(reg)
    RoostPlugin().register(reg)

    return reg
