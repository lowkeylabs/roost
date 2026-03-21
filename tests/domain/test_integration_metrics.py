from owlroost.domain.metrics.metric_registry import METRIC_REGISTRY
from owlroost.domain.metrics.metric_spec import extract_metrics
from owlroost.domain.metrics.view_registry import get_view


def test_extract_metrics_end_to_end():
    data = {
        "run_status": {"status": "solved"},
        "timing": {"elapsed_seconds": 10.5},
        "financial": {
            "bequest": {"total": {"today": 100000}},
            "spending": {"total": {"today": 50000}},
        },
        "risk": {
            "outcome": {
                "classification": {"risk_level": "low"},
                "assets": {"final_today": 200000},
                "cushion": {"min_cushion_ratio": 0.2},
                "drawdown": {"worst_drawdown_factor": -0.3},
                "terminal": {"spending_to_assets_ratio": 0.1},
                "depletion": {"depleted": False, "years_to_depletion": None},
            },
            "scenario": {
                "severity_score": 0.5,
                "returns": {"avg": 0.06, "min": -0.2},
                "inflation": {"avg": 0.03},
            },
        },
    }

    specs = list(METRIC_REGISTRY.values())
    row = extract_metrics(data, specs)

    assert row["status"] == "solved"
    assert row["elapsed"] == 10.5
    assert row["bequest"] == 100000
    assert row["spending"] == 50000
    assert row["risk"] == "low"


def test_view_and_registry_integration():
    view, _layout = get_view("trial", "default")

    keys = [spec.key for spec in view]

    assert "status" in keys
    assert "bequest" in keys
