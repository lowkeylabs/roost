from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class Column:
    key: str
    label: str
    extractor: Callable[[Any], Any]
    group: str
    align: str = "left"  # left | right | center
    header_align: str = "center"  # left | right | center
    fmt: str | None = None  # None | "currency" | "currency_k" | "float2" | "float3" | "int"


COLUMN_REGISTRY: dict[str, Column] = {}
GROUP_REGISTRY: dict[str, list[str]] = {}
VIEW_REGISTRY: dict[str, list[str]] = {}


def register_column(column: Column):
    COLUMN_REGISTRY[column.key] = column

    # auto-register in group
    GROUP_REGISTRY.setdefault(column.group, []).append(column.key)


def register_view(name: str, column_keys: list[str]):
    VIEW_REGISTRY[name] = column_keys
