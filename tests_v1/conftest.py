import pytest

from owlroost.domain.metrics import load_metrics


@pytest.fixture(autouse=True, scope="session")
def load_metrics_once():
    load_metrics()
