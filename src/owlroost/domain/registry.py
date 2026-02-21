from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .case import Case


@dataclass
class Column:
    key: str
    label: str
    extractor: Callable[[Case], Any]
    group: str


COLUMN_REGISTRY: dict[str, Column] = {}


def register_column(column: Column):
    COLUMN_REGISTRY[column.key] = column
