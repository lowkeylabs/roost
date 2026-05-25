# src/owlroost/schema/bootstrap.py

from .plugins.case import CasePlugin
from .plugins.derived import DerivedMetricsPlugin
from .plugins.group_derived import GroupDerivedMetricsPlugin
from .plugins.hydra_helpers import HydraHelperPlugin
from .plugins.longevity import LongevityPlugin
from .plugins.metrics import MetricsSchemaPlugin
from .plugins.owl import OwlSchemaPlugin
from .plugins.roost_runtime import RoostRuntimePlugin
from .plugins.runtime_environment import RuntimeEnvironmentPlugin
from .plugins.spending_policy import SpendingPolicyPlugin
from .plugins.ui_bridge import OwlUiBridgePlugin
from .registry import SchemaRegistry
from .runtime_defaults import (
    build_runtime_defaults,
    get_from_path,
)


def build_registry(
    return_plugins: bool = False,
):
    reg = SchemaRegistry()

    # =====================================================
    # Plugins
    # =====================================================

    plugins = [
        OwlSchemaPlugin(),
        LongevityPlugin(),
        SpendingPolicyPlugin(),
        RoostRuntimePlugin(),
        RuntimeEnvironmentPlugin(),
        MetricsSchemaPlugin(),
        DerivedMetricsPlugin(),
        GroupDerivedMetricsPlugin(),
        OwlUiBridgePlugin(),
        HydraHelperPlugin(),
        CasePlugin(),
    ]

    # =====================================================
    # Register plugins
    # =====================================================

    for p in plugins:
        p.register(reg)

    # =====================================================
    # Discover runtime-expanded OWL defaults
    # =====================================================

    discovered_defaults = build_runtime_defaults()

    reg.register_discovered_fields(
        discovered_defaults,
    )

    reg.attach_discovered_defaults(
        discovered_defaults,
        get_from_path,
    )

    # =====================================================
    # Return
    # =====================================================

    if return_plugins:
        return reg, plugins

    return reg
