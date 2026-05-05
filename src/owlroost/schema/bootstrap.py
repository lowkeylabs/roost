# src/owlroost/schema/bootstrap.py

from .plugins.case import CasePlugin
from .plugins.longevity import LongevityPlugin
from .plugins.metrics import MetricsSchemaPlugin
from .plugins.owl import OwlSchemaPlugin
from .plugins.owl_solver import OwlSolverPlugin
from .plugins.roost import RoostPlugin
from .plugins.runtime import RuntimePlugin
from .plugins.spending_policy import SpendingPolicyPlugin
from .plugins.trial import TrialPlugin
from .plugins.ui_bridge import OwlUiBridgePlugin
from .registry import SchemaRegistry
from .runtime_defaults import build_runtime_defaults, get_from_path


def build_registry(return_plugins: bool = False):
    reg = SchemaRegistry()

    plugins = [
        OwlSchemaPlugin(),
        LongevityPlugin(),
        SpendingPolicyPlugin(),
        TrialPlugin(),
        RuntimePlugin(),
        RoostPlugin(),
        MetricsSchemaPlugin(),
        OwlSolverPlugin(),
        OwlUiBridgePlugin(),
        CasePlugin(),
    ]

    for p in plugins:
        p.register(reg)

    runtime_defaults = build_runtime_defaults()
    reg.register_runtime_fields(runtime_defaults)
    reg.attach_runtime_defaults(runtime_defaults, get_from_path)

    if return_plugins:
        return reg, plugins

    return reg
