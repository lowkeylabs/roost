from __future__ import annotations

import json
from pathlib import Path

from owlroost.domain.metrics.metric_spec import MetricSpec


def load_metrics(trial_path: Path) -> dict | None:
    file = next(trial_path.glob("*_metrics.json"), None)
    if not file:
        return None

    try:
        return json.loads(file.read_text())
    except Exception:
        return None


def extract_row(data: dict, specs: list[MetricSpec]) -> dict:
    row = {}

    for spec in specs:
        try:
            row[spec.key] = spec.extract(data)
        except Exception:
            row[spec.key] = None

    return row


def build_trial_row(trial_path: Path, specs: list[MetricSpec]) -> dict | None:
    data = load_metrics(trial_path)
    if not data:
        return None

    return extract_row(data, specs)
