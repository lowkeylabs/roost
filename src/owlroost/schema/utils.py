# src/owlroost/schema/utils.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

import types
from typing import Union, get_args, get_origin

from pydantic_core import PydanticUndefined


def is_pydantic_model(annotation):
    return hasattr(annotation, "model_fields")


def walk_model(
    prefix,
    model,
    *,
    expansions=None,
):
    """
    Recursively walk a Pydantic model and yield
    (full_name, field) for semantic leaf fields.

    Notes
    -----
    Model B2 Architecture
    ---------------------
    The schema registry owns semantic
    variables only.

    Container models are traversal
    structures and are not emitted as
    schema fields.

    Example
    -------

        [aca_settings]
        slcsp_annual = 14.0

    Emits:

        aca_settings.slcsp_annual

    Does NOT emit:

        aca_settings

    Namespace/container nodes are
    synthesized later by the catalog
    subsystem.

    Alias Handling
    --------------
    The schema registry represents the
    public TOML ontology rather than
    Python implementation details.

    Example:

        from_: int = Field(
            alias="from",
        )

    Emits:

        rates_selection.from

    rather than:

        rates_selection.from_
    """

    expansions = expansions or {}

    for py_name, field in model.model_fields.items():
        # =============================================
        # Public ontology name
        # =============================================

        public_name = field.alias if field.alias is not None else py_name

        full_name = f"{prefix}.{public_name}" if prefix else public_name

        # =============================================
        # Explicit Expansion Override
        # =============================================

        expansion_model = expansions.get(
            full_name,
        )

        if expansion_model is not None:
            yield from walk_model(
                full_name,
                expansion_model,
                expansions=expansions,
            )

            continue

        # =============================================
        # Normal Recursive Traversal
        # =============================================

        annotation = unwrap_annotation(
            field.annotation,
        )

        if is_pydantic_model(
            annotation,
        ):
            yield from walk_model(
                full_name,
                annotation,
                expansions=expansions,
            )

            continue

        # =============================================
        # Leaf Semantic Variable
        # =============================================

        yield full_name, field


def unwrap_annotation(annotation):
    origin = get_origin(annotation)

    # Handle typing.Union (old style)
    if origin is Union:
        args = [a for a in get_args(annotation) if a is not type(None)]
        return args[0] if args else annotation

    # Handle PEP 604 (new style: X | None)
    if origin is types.UnionType:
        args = [a for a in get_args(annotation) if a is not type(None)]
        return args[0] if args else annotation

    return annotation


def resolve_field_default(
    field,
):
    """
    Resolve normalized default from Pydantic v2 field.
    """

    if field.default_factory is not None:
        return field.default_factory()

    if field.default is PydanticUndefined:
        return None

    return field.default
