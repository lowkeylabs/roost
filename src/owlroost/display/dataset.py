# src/owlroost/display/dataset.py


class Dataset:
    def __init__(self, rows, level="case"):
        self.rows = rows
        self.level = level

    def view(self, name="default", layout="table"):
        from .api import extract_view

        return extract_view(self, name, layout)

    def pipe(self):
        from .pipeline import Pipeline

        return Pipeline(self)
