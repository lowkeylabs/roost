# src/owlroost/display/utils.py


def extract_path(data, path):
    if path == "_path":
        return str(data["_path"])

    parts = path.split(".")
    cur = data["_inputs"]

    for p in parts:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(p)

    return cur


def attach_row_ids(dataset):
    rows = []
    for i, r in enumerate(dataset.rows):
        new = dict(r)
        new["_row_id"] = i
        rows.append(new)
    return type(dataset)(rows, level=dataset.level)


def inject_id_column(table, dataset):
    table.columns = ["ID"] + list(table.columns)

    new_rows = []
    for row_data, r in zip(table.rows, dataset.rows, strict=False):
        new_rows.append([str(r["_row_id"])] + list(row_data))

    table.rows = new_rows
    return table
