# src/owlroost/display/dashboards/specs.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(slots=True)
class DashboardSpec:
    """
    Dashboard definition.

    Notes
    -----
    Dashboards are higher-level
    presentation artifacts used by
    discovery-oriented commands such as:

        roost vars

    Unlike DisplayView, dashboards are
    free-form Rich renderers.
    """

    name: str

    render: Callable

    description: str = ""
