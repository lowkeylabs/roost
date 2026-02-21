from .case import Case
from .registry import COLUMN_REGISTRY


def build_rows(cases: list[Case], columns: list[str]) -> list[dict]:
    rows = []

    for case in cases:
        row = {}
        for key in columns:
            col = COLUMN_REGISTRY[key]
            row[col.label] = col.extractor(case)
        rows.append(row)

    return rows
