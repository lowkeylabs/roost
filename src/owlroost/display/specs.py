# src/owlroost/display.specs.py

from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class DisplayProfile:
    label: str | None = None
    fmt: str | None = None
    label_align: str = "left"
    content_align: str = "left"
    width: int | None = None
    wrap: bool = False
    explanation: str | None = None
    visible: bool = True


@dataclass
class DisplayField:
    field_name: str
    description: str | None = None
    profiles: dict[str, DisplayProfile] = field(default_factory=dict)
    default_aggregates: list[str] = field(default_factory=list)
    show_if: list[str] = field(default_factory=list)
    display_fn: Callable[[dict], object] | None = None


@dataclass
class DisplayGroup:
    key: str
    entries: list[str | tuple]
    description: str = ""


@dataclass
class ViewSpec:
    level: str
    name: str
    entries: list
    description: str = ""
