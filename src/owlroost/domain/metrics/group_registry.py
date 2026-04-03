from __future__ import annotations

from typing import Any

# =========================================================
# Registry
# =========================================================

METRIC_GROUP_REGISTRY: dict[str, dict[str, Any]] = {}


# =========================================================
# Registration
# =========================================================


def register_group(
    name: str,
    items: list,
    description: str | None = None,
    default_opts: dict | None = None,
):
    """
    Register a reusable group of metrics.

    Parameters
    ----------
    name : str
        Unique group name.
    items : list
        List of MetricKey-compatible items (same format as views).
        Can include:
            - metric keys
            - (metric, agg)
            - (metric, opts)
            - (metric, agg, opts)
            - {"separator": ...}
            - ("group", other_group_name)  # nested groups
    description : str, optional
        Human-readable description of the group.
    """
    if name in METRIC_GROUP_REGISTRY:
        raise ValueError(f"Group '{name}' is already registered")

    METRIC_GROUP_REGISTRY[name] = {
        "items": items,
        "description": description or "",
        "default_opts": default_opts or {},
    }


# =========================================================
# Accessors
# =========================================================


def get_group(name: str) -> dict:
    if name not in METRIC_GROUP_REGISTRY:
        raise KeyError(f"Unknown group '{name}'")
    return METRIC_GROUP_REGISTRY[name]


def list_groups() -> list[str]:
    return sorted(METRIC_GROUP_REGISTRY.keys())


def get_group_description(name: str) -> str:
    group = get_group(name)
    return group.get("description", "")


# =========================================================
# Expansion
# =========================================================


def expand_group(name: str) -> list:
    """
    Expand a group into a flat list of MetricKey items.

    Handles nested groups recursively.
    """
    group = get_group(name)
    items = group["items"]
    default_opts = group.get("default_opts", {})

    expanded: list = []

    for item in items:
        # ----------------------------------------
        # Nested group: ("group", "name")
        # ----------------------------------------
        if isinstance(item, tuple) and len(item) >= 2 and item[0] == "group":
            sub_group_name = item[1]
            expanded.extend(expand_group_with_defaults(sub_group_name, default_opts))
            continue

        # ----------------------------------------
        # Pass-through (metric, tuple, dict, etc.)
        # ----------------------------------------
        expanded.append(_apply_default_options(item, default_opts))

    return expanded


# =========================================================
# View Integration Helper
# =========================================================


def expand_items_with_groups(items: list) -> list:
    """
    Expand a list of MetricKey items, resolving any group references.

    This is intended to be called from view resolution.

    Example:
        ("group", "core_outcomes")

    becomes:
        [("spending_annual", "median"), ...]
    """
    expanded: list = []

    for item in items:
        # ----------------------------------------
        # Group reference
        # ----------------------------------------
        if isinstance(item, tuple) and len(item) >= 2 and item[0] == "group":
            group_name = item[1]

            # Optional opts (e.g., {"show_if": ...})
            opts = item[2] if len(item) > 2 and isinstance(item[2], dict) else None

            group_items = expand_group(group_name)

            # Apply view-level opts to each item if present
            if opts:
                for g in group_items:
                    expanded.append(_merge_item_options(g, opts))
            else:
                expanded.extend(group_items)

            continue

        expanded.append(item)

    return expanded


# =========================================================
# Internal Helpers
# =========================================================


def _merge_item_options(item, opts: dict):
    """
    Merge view-level options (e.g., show_if) into a MetricKey item.

    Supports:
        - "metric"
        - ("metric", agg)
        - ("metric", opts)
        - ("metric", agg, opts)
    """
    # ----------------------------------------
    # Simple string key
    # ----------------------------------------
    if isinstance(item, str):
        return (item, opts)

    # ----------------------------------------
    # Tuple forms
    # ----------------------------------------
    if isinstance(item, tuple):
        if len(item) == 2:
            key, second = item

            # (key, agg)
            if isinstance(second, str):
                return (key, second, opts)

            # (key, existing_opts)
            if isinstance(second, dict):
                merged = {**second, **opts}
                return (key, merged)

        if len(item) == 3:
            key, agg, existing_opts = item
            merged = {**(existing_opts or {}), **opts}
            return (key, agg, merged)

    # ----------------------------------------
    # Dict form
    # ----------------------------------------
    if isinstance(item, dict):
        return {**item, **opts}

    return item


def _apply_default_options(item, default_opts: dict):
    """
    Apply default options ONLY if item does not already define them.
    """
    if not default_opts:
        return item

    # ----------------------------------------
    # Simple string
    # ----------------------------------------
    if isinstance(item, str):
        return (item, dict(default_opts))

    # ----------------------------------------
    # Tuple forms
    # ----------------------------------------
    if isinstance(item, tuple):
        if len(item) == 2:
            key, second = item

            if isinstance(second, str):
                return (key, second, dict(default_opts))

            if isinstance(second, dict):
                merged = {**default_opts, **second}  # item overrides default
                return (key, merged)

        if len(item) == 3:
            key, agg, existing_opts = item
            merged = {**default_opts, **(existing_opts or {})}
            return (key, agg, merged)

    # ----------------------------------------
    # Dict
    # ----------------------------------------
    if isinstance(item, dict):
        if "separator" in item:
            return item
        return {**default_opts, **item}

    return item


def expand_group_with_defaults(name: str, inherited_defaults: dict) -> list:
    group = get_group(name)
    items = group["items"]

    # merge parent → child defaults
    local_defaults = {**inherited_defaults, **group.get("default_opts", {})}

    expanded = []

    for item in items:
        if isinstance(item, tuple) and len(item) >= 2 and item[0] == "group":
            expanded.extend(expand_group_with_defaults(item[1], local_defaults))
        else:
            expanded.append(_apply_default_options(item, local_defaults))

    return expanded
