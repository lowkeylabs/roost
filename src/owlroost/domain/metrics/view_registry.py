from dataclasses import dataclass
from typing import Union

from .metric_registry import METRIC_REGISTRY, get_metric
from .metric_spec import MetricSpec

METRIC_VIEW_REGISTRY: dict[str, dict[str, dict]] = {
    "trial": {},
    "run": {},
    "experiments": {},
}

MetricKey = Union[  # noqa: UP007
    str,
    tuple[str, str],  # (key, aggregate)
    tuple[str, dict],  # (key, opts)
    tuple[str, str, dict],  # (key, aggregate, opts)
]


@dataclass
class ResolvedMetric:
    spec: MetricSpec
    aggregate: str | None = None
    view_show_if: str | None = None

    # -----------------------------
    # Core identity
    # -----------------------------
    @property
    def key(self):
        return self.spec.key

    # -----------------------------
    # Display
    # -----------------------------
    @property
    def label(self):
        if self.aggregate:
            return f"{self.spec.label}\n({self.aggregate})"
        return self.spec.label

    @property
    def align(self):
        return self.spec.align

    @property
    def fmt(self):
        return self.spec.fmt

    @property
    def dtype(self):
        return self.spec.dtype


# ===============================================
# Registration
# ===============================================


def register_view(
    level: str,
    name: str,
    metric_keys: list[MetricKey],
    layout: str = "table",
    explain: bool = False,
    description: str | None = None,
    tags: list[str] | None = None,
):
    METRIC_VIEW_REGISTRY[level][name] = {
        "metrics": metric_keys,
        "layout": layout,
        "explain": explain,
        "description": description or "",
        "tags": tags or [],
    }


# ===============================================
# Resolution
# ===============================================


def resolve_metric(key):
    # aggregate form: ("bequest", "mean")
    if isinstance(key, tuple):
        base, agg = key
        spec = get_metric(base)
        return (spec, agg)

    return (get_metric(key), None)


def get_view(level: str, name: str):
    view_def = METRIC_VIEW_REGISTRY[level][name]
    keys = view_def["metrics"]
    layout = view_def.get("layout", "table")
    explain = view_def.get("explain", False)

    resolved = []
    missing = []

    for item in keys:
        parsed = parse_view_item(item)

        key = parsed["key"]
        agg = parsed["aggregate"]
        view_show_if = parsed["view_show_if"]

        if key not in METRIC_REGISTRY:
            missing.append(item)
            continue

        spec = get_metric(key)

        if agg and agg not in (spec.aggregates or []):
            raise KeyError(f"Metric '{key}' does not support aggregate '{agg}'")

        resolved.append(ResolvedMetric(spec, agg, view_show_if))

    if missing:
        raise KeyError(f"View '{level}:{name}' references unknown metrics: {missing}")

    return resolved, layout, explain


# ===============================================
# View metadata and help
# ===============================================


def view_keys(view):
    return {rm.key for rm in view}


def get_view_tags(level: str, name: str) -> list[str]:
    entry = METRIC_VIEW_REGISTRY.get(level, {}).get(name)
    if not entry:
        return []
    return entry.get("tags", [])


def get_view_description(level: str, name: str) -> str:
    entry = METRIC_VIEW_REGISTRY.get(level, {}).get(name)
    if not entry:
        return ""
    return entry.get("description", "")


def list_views(level: str):
    return sorted(METRIC_VIEW_REGISTRY[level].keys())


def parse_view_item(item):
    if isinstance(item, str):
        return {"key": item, "aggregate": None, "view_show_if": None}

    if isinstance(item, tuple):
        # ----------------------------------------
        # (key, agg)
        # ----------------------------------------
        if len(item) == 2:
            key, second = item

            # Case: (key, {"show_if": ...})
            if isinstance(second, dict):
                return {
                    "key": key,
                    "aggregate": None,
                    "view_show_if": second.get("show_if"),
                }

            # Case: (key, agg)
            return {
                "key": key,
                "aggregate": second,
                "view_show_if": None,
            }

        # ----------------------------------------
        # (key, agg, opts)
        # ----------------------------------------
        if len(item) == 3:
            key, agg, opts = item
            return {
                "key": key,
                "aggregate": agg,
                "view_show_if": (opts or {}).get("show_if"),
            }

    if isinstance(item, dict):
        return {
            "key": item["key"],
            "aggregate": item.get("aggregate"),
            "view_show_if": item.get("show_if"),
        }

    raise ValueError(f"Invalid view item: {item}")


def view_help(
    display_level: str,
    display_mode: str,
    row: dict | None = None,
    tag_filter: str | None = None,
) -> str:
    """
    Render help text for available views in the current context.
    Optionally filter by tag.
    """

    context_views = list_views_for_context(display_level, display_mode, row)

    lines: list[str] = []

    lines.append(f"[bold]Available views for level '{display_level}':[/bold]")
    lines.append("[dim](use --view <name>)[/dim]\n")

    if tag_filter:
        lines.append(f"[dim]Filtering by tag: '{tag_filter}'[/dim]\n")

    def render_group(title: str, views: list[str]):
        group_lines = []

        for v in views:
            tags = get_view_tags(display_level, v)

            # Apply tag filter
            if tag_filter and tag_filter not in tags:
                continue

            desc = get_view_description(display_level, v)
            tag_str = f" [dim]({', '.join(tags)})[/dim]" if tags else ""

            if desc:
                group_lines.append(f"  {v:<12} - {desc}{tag_str}")
            else:
                group_lines.append(f"  {v}{tag_str}")

        # Only render group if it has entries
        if group_lines:
            lines.append(f"[bold]{title}:[/bold]")
            lines.extend(group_lines)
            lines.append("")

    if "recommended" in context_views:
        render_group("Recommended", context_views["recommended"])

    render_group("All", context_views["all"])

    # Handle case where filter matches nothing
    if len(lines) <= 2:
        lines.append(f"[yellow]No views match tag '{tag_filter}'[/yellow]\n")

    return "\n".join(lines)


def list_views_for_level(level: str) -> list[str]:
    return sorted(METRIC_VIEW_REGISTRY.get(level, {}).keys())


def resolve_default_view(display_level: str, display_mode: str, row: dict | None) -> str:
    if display_level == "run":
        return "default"

    if display_level == "trial":
        if display_mode == "list":
            return "default"

        if display_mode == "detail":
            status = (row or {}).get("status")
            if status == "failed":
                return "failures"
            return "fragility"

    return "default"


def list_views_for_context(display_level: str, display_mode: str, row: dict | None):
    all_views = list_views_for_level(display_level)

    if display_level != "trial" or display_mode != "detail":
        return {"all": all_views}

    status = (row or {}).get("status")

    if status == "failed":
        return {
            "recommended": ["failures"],
            "all": all_views,
        }

    return {
        "recommended": ["fragility", "outcomes"],
        "all": all_views,
    }
