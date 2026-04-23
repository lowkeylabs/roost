# src/owlroost/domain/models/table.py


class RoostTable:
    def __init__(self, columns, rows, layout="table", meta=None):
        self.columns = columns
        self.rows = rows
        self.layout = layout
        self.meta = meta or {}

    def __len__(self):
        return len(self.rows)

    def __repr__(self):
        return (
            f"RoostTable(rows={len(self.rows)}, cols={len(self.columns)}, layout='{self.layout}')"
        )

    # -----------------------------------------------------
    # Column key access (NEW)
    # -----------------------------------------------------
    def column_keys(self):
        """
        Return stable keys for columns if available.
        Falls back to column labels.
        """
        return self.meta.get("column_keys", self.columns)

    def column_key(self, index):
        keys = self.column_keys()
        return keys[index] if index < len(keys) else None

    # -----------------------------------------------------
    # Internal cell extractor
    # -----------------------------------------------------
    def _extract(self, cell, formatted=False):
        if isinstance(cell, dict):
            return cell["formatted"] if formatted else cell["value"]
        return cell

    # -----------------------------------------------------
    # DataFrame conversion
    # -----------------------------------------------------
    def to_dataframe(self, formatted=False, normalize_columns=True):
        """
        Convert to pandas DataFrame.

        Parameters:
            formatted (bool): use formatted values
            normalize_columns (bool): flatten '\n' for pandas
        """
        import pandas as pd

        data = [[self._extract(c, formatted=formatted) for c in row] for row in self.rows]

        if normalize_columns:
            columns = [c.replace("\n", " ").strip() for c in self.columns]
        else:
            columns = list(self.columns)

        return pd.DataFrame(data, columns=columns)

    # -----------------------------------------------------
    # Column access
    # -----------------------------------------------------
    def series(self, col, formatted=False):
        df = self.to_dataframe(formatted=formatted)

        if col not in df:
            raise KeyError(f"Column '{col}' not found")

        return df[col]

    def numeric_series(self, col):
        import pandas as pd

        return pd.to_numeric(self.series(col, formatted=False), errors="coerce")

    # -----------------------------------------------------
    # Convenience helpers
    # -----------------------------------------------------
    def has_column(self, col):
        return col in self.columns

    def head(self, n=5, formatted=False):
        return self.to_dataframe(formatted=formatted).head(n)

    def columns_list(self):
        return list(self.columns)
