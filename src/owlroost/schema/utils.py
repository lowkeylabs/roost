import types
from typing import Union, get_args, get_origin

from pydantic_core import PydanticUndefined


def is_pydantic_model(annotation):
    return hasattr(annotation, "model_fields")


def walk_model(prefix, model):
    """
    Recursively walk a Pydantic model and yield (name, field).
    """
    for name, field in model.model_fields.items():
        full_name = f"{prefix}.{name}" if prefix else name

        yield full_name, field

        annotation = unwrap_annotation(field.annotation)

        if is_pydantic_model(annotation):
            yield from walk_model(full_name, annotation)


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
