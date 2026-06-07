# src/owlroost/display/dashboards/bootstrap.py
#
# Copyright (c) 2026 John Leonard
# All rights reserved.
# SPDX-License-Identifier: LicenseRef-OwlRoost-Proprietary
# See LICENSE file in repository root.

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from owlroost.display.dashboards.layouts import (
    register_dashboards,
)


def register_display_dashboards(
    reg,
):
    register_dashboards(
        reg,
    )
