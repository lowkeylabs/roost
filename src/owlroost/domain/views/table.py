from ..registry import COLUMN_REGISTRY


def build_rows(cases, column_keys):
    rows = []

    for case in cases:
        row = {}

        for key in column_keys:
            column = COLUMN_REGISTRY[key]
            row[key] = column.extractor(case)

        rows.append(row)

    return rows
