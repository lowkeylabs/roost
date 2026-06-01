# src/owlroost/version.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("owl-roost")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+unknown"
