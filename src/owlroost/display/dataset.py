from __future__ import annotations


class Dataset:
    def __init__(
        self,
        rows,
        level="case",
    ):
        self.rows = rows
        self.level = level

    def clone(self, rows):
        return Dataset(
            rows=rows,
            level=self.level,
        )

    def filter(self, *filters):
        from .utils import apply_filters

        return self.clone(
            apply_filters(
                self.rows,
                filters,
            )
        )

    def sort(self, sort_key):
        from .utils import apply_sort

        return self.clone(
            apply_sort(
                self.rows,
                sort_key,
            )
        )

    def canonical_sort(self):
        from .utils import apply_canonical_sort

        return self.clone(
            apply_canonical_sort(
                self.rows,
            )
        )

    def top(self, n):
        from .utils import apply_top

        return self.clone(
            apply_top(
                self.rows,
                n,
            )
        )

    def view(
        self,
        registry,
        level=None,
        name="default",
        layout="table",
        explain=None,
    ):
        from .materialize import materialize_view

        return materialize_view(
            dataset=self,
            registry=registry,
            level=level or self.level,
            view_name=name,
            mode=layout,
            explain=explain,
        )

    def pipe(self):
        from .pipeline import Pipeline

        return Pipeline(self)
