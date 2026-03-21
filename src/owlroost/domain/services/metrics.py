from __future__ import annotations

import json
from pathlib import Path

from owlroost.domain.metrics.metric_registry import METRIC_REGISTRY
from owlroost.domain.metrics.metric_spec import MetricSpec


def load_metrics(trial_path: Path) -> dict | None:
    file = next(trial_path.glob("*_metrics.json"), None)
    if not file:
        return None

    try:
        return json.loads(file.read_text())
    except Exception:
        return None


def extract_row(data: dict, specs: list[MetricSpec], base_row: dict | None = None) -> dict:
    row = base_row.copy() if base_row else {}

    for spec in specs:
        try:
            # ----------------------------------------
            # 1. compute_fn (explicit override)
            # ----------------------------------------
            if spec.compute_fn:
                row[spec.key] = spec.compute_fn(row)

            # ----------------------------------------
            # 2. already present (context enrichment)
            # ----------------------------------------
            elif spec.key in row:
                continue  # keep existing value

            # ----------------------------------------
            # 3. path-based extraction
            # ----------------------------------------
            elif spec.path:
                row[spec.key] = spec.extract(data)

            # ----------------------------------------
            # 4. default fallback
            # ----------------------------------------
            else:
                row[spec.key] = None

        except Exception:
            row[spec.key] = None

    return row


def build_trial_row(
    trial_path: Path,
    specs: list[MetricSpec] | None = None,
    base_row: dict | None = None,
) -> dict | None:
    data = load_metrics(trial_path)
    if not data:
        return None

    # -------------------------------------------------
    # FULL EXTRACTION SUPPORT (THIS IS THE FIX)
    # -------------------------------------------------
    if specs is None:
        specs = list(METRIC_REGISTRY.values())

    return extract_row(data, specs, base_row=base_row)
