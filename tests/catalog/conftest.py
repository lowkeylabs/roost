from __future__ import annotations

import pytest

from owlroost.catalog.service import (
    load_catalog,
)

from owlroost.metrics.bootstrap import (
    build_metrics_registry,
)

from owlroost.schema.bootstrap import (
    build_registry,
)


@pytest.fixture
def registries():

    schema_registry = build_registry()

    metrics_registry = (
        build_metrics_registry()
    )

    return (
        schema_registry,
        metrics_registry,
    )


@pytest.fixture
def catalog_dataset(
    registries,
):

    (
        schema_registry,
        metrics_registry,
    ) = registries

    return load_catalog(
        schema_registry=schema_registry,
        metrics_registry=metrics_registry,
    )
