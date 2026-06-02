# src/owlroost/display/operations/help.py

"""
Help and field discovery utilities.
"""

from __future__ import annotations

# =========================================================
# Field Discovery
# =========================================================


def discover_view_fields(
    registry,
    level,
    view_name,
):
    """
    Return expanded fields defined by view.
    """

    return registry.expand_view_fields(
        level,
        view_name,
    )


def discover_queryable_fields(
    rows,
):
    """
    Discover queryable fields from rows.
    """

    fields = set()

    # =====================================================
    # Recursive Walker
    # =====================================================

    def walk(
        obj,
        prefix="",
    ):
        if not isinstance(
            obj,
            dict,
        ):
            return

        for key, value in obj.items():
            full = key if not prefix else f"{prefix}.{key}"

            fields.add(
                full,
            )

            if isinstance(
                value,
                dict,
            ):
                walk(
                    value,
                    full,
                )

    # =====================================================
    # Scan Rows
    # =====================================================

    for row in rows:
        walk(
            row.get(
                "_inputs",
                {},
            )
        )

        walk(
            row.get(
                "_metrics",
                {},
            )
        )

        walk(
            row.get(
                "_meta",
                {},
            )
        )

    return sorted(
        fields,
    )


# =========================================================
# CLI Help Rendering
# =========================================================


def render_field_help(
    *,
    rows,
    registry,
    level,
    view_name,
    mode="view",
    title="Available fields",
    examples=None,
):
    """
    Render field help.
    """

    import click

    click.echo()
    click.echo(f"{title}:")
    click.echo()

    # =====================================================
    # View Fields
    # =====================================================

    if mode == "view":
        fields = discover_view_fields(
            registry,
            level,
            view_name,
        )

    # =====================================================
    # Queryable Fields
    # =====================================================

    else:
        fields = discover_queryable_fields(
            rows,
        )

    synthetic_fields = [
        "id",
    ]

    fields = list(
        fields,
    )

    for sf in reversed(
        synthetic_fields,
    ):
        if sf not in fields:
            fields.insert(
                0,
                sf,
            )

    for field in sorted(
        fields,
    ):
        click.echo(f"  {field}")

    if examples:
        click.echo()
        click.echo("Examples:")
        click.echo()

        for ex in examples:
            click.echo(f"  {ex}")

    click.echo()
