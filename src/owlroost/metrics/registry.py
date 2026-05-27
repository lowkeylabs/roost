# src/owlroost/metrics/registry.py

from __future__ import annotations

from collections.abc import (
    Iterator,
)

from owlroost.metrics.specs import (
    MetricSpec,
)

# =========================================================
# Metrics Registry
# =========================================================


class MetricsRegistry:
    """
    Runtime registry and lookup container
    for observable metrics ontology.

    Notes
    -----
    MetricsRegistry intentionally owns only:

        - metric registration
        - lookup/indexing
        - iteration

    It intentionally does NOT own:

        - runtime metric generation
        - aggregation execution
        - catalog indexing
        - display composition
        - reporting behavior

    Canonical semantic ownership belongs
    to:

        - MetricSpec
        - OntologySpec

    Architectural Invariant
    -----------------------
    ROOST maintains exactly one canonical
    semantic identity per metric name.

    Duplicate metric registrations are
    therefore considered ontology errors.
    """

    # =====================================================
    # Construction
    # =====================================================

    def __init__(
        self,
    ):
        self._fields: dict[
            str,
            MetricSpec,
        ] = {}

    # =====================================================
    # Registration
    # =====================================================

    def register(
        self,
        field: MetricSpec,
    ):
        """
        Register canonical metric ontology.

        Parameters
        ----------
        field
            Canonical metric specification.

        Raises
        ------
        ValueError
            If duplicate semantic identity
            is detected.
        """

        if field.name in self._fields:
            raise ValueError(
                "Duplicate metric field "
                f"registered: "
                f"{field.name}"
            )

        self._fields[field.name] = field

    # =====================================================
    # Lookup
    # =====================================================

    def get(
        self,
        name: str,
    ) -> MetricSpec:
        """
        Retrieve metric specification by
        canonical semantic identity.
        """

        try:
            return self._fields[name]

        except KeyError as err:
            raise KeyError(
                "Metric field not found: "
                f"{name}"
            ) from err

    def exists(
        self,
        name: str,
    ) -> bool:
        """
        Return whether canonical metric
        exists.
        """

        return name in self._fields

    # =====================================================
    # Iteration
    # =====================================================

    def all(
        self,
    ) -> list[MetricSpec]:
        """
        Return all metric specifications.

        Notes
        -----
        Results are returned in stable
        canonical name order for
        deterministic analytical behavior.
        """

        return [
            self._fields[name]
            for name in sorted(
                self._fields
            )
        ]

    def names(
        self,
    ):
        """
        Iterate canonical metric names.
        """

        return iter(
            sorted(
                self._fields.keys()
            )
        )

    def items(
        self,
    ):
        """
        Iterate registry items in stable
        canonical name order.
        """

        for name in sorted(
            self._fields
        ):
            yield (
                name,
                self._fields[name],
            )

    # =====================================================
    # Introspection
    # =====================================================

    def __contains__(
        self,
        name: str,
    ) -> bool:
        """
        Support:

            "x" in registry
        """

        return name in self._fields

    def __len__(
        self,
    ) -> int:
        """
        Number of registered metrics.
        """

        return len(self._fields)

    def __iter__(
        self,
    ) -> Iterator[
        MetricSpec
    ]:
        """
        Iterate metric specifications in
        stable canonical order.
        """

        return iter(
            self.all()
        )
