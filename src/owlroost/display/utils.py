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
