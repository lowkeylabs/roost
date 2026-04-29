from collections.abc import Callable

# from dataclasses import dataclass
# from typing import Any


ANALYSIS_VIEW_REGISTRY: dict[str, Callable] = {}


def register_analysis_view(name: str, fn: Callable):
    ANALYSIS_VIEW_REGISTRY[name] = fn
