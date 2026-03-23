from __future__ import annotations

import json
from pathlib import Path

from owlplanner.config.toml_io import load_toml

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


def load_effective(trial_path: Path) -> dict:
    file = next(trial_path.glob("*_effective.toml"), None)

    if not file:
        return {}

    try:
        result = load_toml(str(file))

        # Case 1: OWL tuple return
        if isinstance(result, tuple):
            for item in result:
                if isinstance(item, dict):
                    return item
            return {}

        # Case 2: direct dict
        if isinstance(result, dict):
            return result

        # Case 3: unexpected (string, etc.)
        return {}

    except Exception:
        return {}


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
    #
    data = load_metrics(trial_path)
    metrics_data = load_metrics(trial_path)
    if not metrics_data:
        return None

    effective_data = load_effective(trial_path)

    # ----------------------------------------
    # Unified data payload (NEW)
    # ----------------------------------------
    data = {
        **metrics_data,
        "_inputs": effective_data,  # namespaced input layer
    }

    if specs is None:
        specs = list(METRIC_REGISTRY.values())

    return extract_row(data, specs, base_row=base_row)
