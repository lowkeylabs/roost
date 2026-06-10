# src/owlroost/exceptions.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
ROOST exception hierarchy.

Notes
-----
ROOST distinguishes between:

- user-facing exceptions
- ordinary Python exceptions

User-facing exceptions should be
caught at the CLI boundary and
rendered as concise messages without
tracebacks.

All other exceptions are treated as
programmer errors and should surface
normally during development.
"""

from __future__ import annotations


class RoostBaseError(
    Exception,
):
    """
    Base class for all ROOST-specific
    exceptions.
    """


class RoostError(
    RoostBaseError,
):
    """
    User-facing ROOST exception.

    Raised when user-supplied input is
    invalid or cannot be processed.

    Examples
    --------
    - invalid CLI arguments
    - invalid TOML configuration
    - invalid sweep specifications
    - invalid filters or sort fields
    - unknown views, groups, or fields
    - invalid Hydra overrides
    """
