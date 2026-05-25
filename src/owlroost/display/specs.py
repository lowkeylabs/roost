# src/owlroost/display/specs.py

from collections.abc import Callable
from dataclasses import dataclass, field

from ..schema.registry import FieldSpec


@dataclass
class DisplayProfile:
    label: str | None = None
    fmt: str | None = None
    label_align: str = "left"
    content_align: str = "left"
    width: int | None = None
    wrap: bool = False
    visible: bool = True


ExplainValueCallable = Callable[..., str]


@dataclass
class ExplainSpec:
    # =====================================================
    # Variable Definition
    #
    # What is this variable?
    # =====================================================

    variable: str | None = None

    # =====================================================
    # Value Interpretation
    #
    # What does the displayed value mean?
    # =====================================================

    value: str | None = None

    # =====================================================
    # Provenance / Lineage
    # =====================================================

    sources: list[str] = field(default_factory=list)

    # =====================================================
    # Units / Semantic Scale
    # =====================================================

    units: str | None = None

    # =====================================================
    # Notes / Caveats
    # =====================================================

    notes: str | None = None
    # =====================================================
    # Post Init
    # =====================================================


@dataclass
class DisplayField:
    # =====================================================
    # Semantic Field Name
    #
    # Public identifier used by:
    #   - views
    #   - groups
    #   - filters
    #   - sorting
    #   - reporting
    # =====================================================

    field_name: str

    # =====================================================
    # Storage Path
    #
    # Internal dotted lookup path.
    #
    # Examples:
    #   "_meta.case_id"
    #   "_metrics.elapsed_seconds"
    #   "_inputs.optimization_parameters.objective"
    #
    # Defaults to field_name.
    # =====================================================

    path: str | None = None
    semantic_field: FieldSpec | None = None

    profiles: dict[str, DisplayProfile] = field(default_factory=dict)

    default_aggregates: list[str] = field(default_factory=list)

    show_if: list[str] = field(default_factory=list)

    display_fn: Callable[[dict], object] | None = None

    description: str | None = None
    explain: ExplainSpec | None = None

    # =====================================================
    # Post Init
    # =====================================================

    def __post_init__(
        self,
    ):
        if self.path is None:
            self.path = self.field_name


@dataclass
class DisplayGroup:
    key: str
    entries: list[str | tuple | dict]
    description: str = ""


@dataclass
class ViewSpec:
    level: str
    name: str
    entries: list
    description: str = ""
