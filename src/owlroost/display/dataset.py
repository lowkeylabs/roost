from __future__ import annotations


class Dataset:
    def __init__(
        self,
        rows,
        level="case",
    ):
        self.rows = rows
        self.level = level

    def __len__(self):
        return len(self.rows)

    def head(
        self,
        n=5,
    ):
        return self.clone(
            rows=self.rows[:n],
        )

    def clone(
        self,
        rows=None,
        level=None,
    ):
        return Dataset(
            rows=rows if rows is not None else self.rows,
            level=level if level is not None else self.level,
        )

    def filter(self, *filters):
        from .utils import apply_filters

        return self.clone(
            rows=apply_filters(
                self.rows,
                filters,
            )
        )

    def sort(self, sort_key):
        from .utils import apply_sort

        return self.clone(
            rows=apply_sort(
                self.rows,
                sort_key,
            )
        )

    def canonical_sort(self):
        from .utils import apply_canonical_sort

        return self.clone(
            rows=apply_canonical_sort(
                self.rows,
            )
        )

    def top(self, n):
        from .utils import apply_top

        return self.clone(
            rows=apply_top(
                self.rows,
                n,
            )
        )

    def project(
        self,
        level,
    ):
        from .projection import project_dataset

        return project_dataset(
            self,
            level,
        )

    def view(
        self,
        registry,
        name="default",
        layout="table",
        explain=None,
    ):
        from .materialize import materialize_view

        return materialize_view(
            dataset=self,
            registry=registry,
            level=self.level,
            view_name=name,
            mode=layout,
            explain=explain,
        )

    def pipe(self):
        from .pipeline import Pipeline

        return Pipeline(self)
