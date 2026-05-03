# src/owlroost/display/pipeline.py


class Pipeline:
    def __init__(self, dataset):
        self.dataset = dataset
        self._table = None

    def view(self, name="default", layout="table"):
        from .api import extract_view

        self._table = extract_view(self.dataset, name, layout)
        return self

    def render(self, renderer="rich"):
        from .api import render

        if self._table is None:
            raise ValueError("No view selected. Call .view() first.")

        return render(self._table, renderer)
