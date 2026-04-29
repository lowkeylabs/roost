import contextlib
import io

from owlplanner.rates import getRatesDistributions

from ..metric_registry import register_metric
from ..metric_spec import MetricSpec


def _input_rates_stats(r):
    rs = (r.get("_inputs") or {}).get("rates_selection", {})

    method = rs.get("method")
    frm = rs.get("from")
    to = rs.get("to")

    if method not in ["bootstrap_sor", "historical", "historical average"]:
        return None

    if frm is None or to is None:
        return None

    try:
        with contextlib.redirect_stdout(io.StringIO()):
            dist = getRatesDistributions(
                frm=frm,
                to=to,
                in_percent=False,
                mylog=None,  # 👈 keep this EXACTLY as before
            )
    except Exception:
        return None

    stock = dist.geo_means[0]
    inflation = dist.geo_means[3]

    return {
        "real": stock - inflation,
        "infl": inflation,
    }


def _input_real_return(r):
    stats = _input_rates_stats(r)
    return stats["real"] if stats else None


def _input_inflation(r):
    stats = _input_rates_stats(r)
    return stats["infl"] if stats else None


def _input_regime_old(r):
    stats = _input_rates_stats(r)
    if not stats:
        return None

    real = stats["real"]
    infl = stats["infl"]

    if real < 0.01 and infl > 0.04:
        return "stagflation"
    if real < 0.01 and infl <= 0.02:
        return "deflationary_bust"
    if real >= 0.05 and infl <= 0.02:
        return "goldilocks"
    if real >= 0.05 and infl > 0.04:
        return "inflationary_boom"

    return "moderate"


def _input_regime(r):
    stats = _input_rates_stats(r)
    if not stats:
        return None

    real = stats["real"]
    infl = stats["infl"]
    worst = stats.get("worst_year")

    if worst is not None and worst < -0.2:
        return "fragile"

    if real < 0.03 and infl > 0.035:
        return "stagflation"

    if real > 0.05 and infl < 0.025:
        return "goldilocks"

    return "moderate"


register_metric(
    MetricSpec(
        key="input_real_return",
        label="Input Real",
        dtype=float,
        fmt="percent",
        compute_level="run",
        compute_fn=_input_real_return,
        is_invariant=True,
    )
)

register_metric(
    MetricSpec(
        key="input_inflation",
        label="Input Infl",
        dtype=float,
        fmt="percent",
        compute_level="run",
        compute_fn=_input_inflation,
        is_invariant=True,
    )
)

register_metric(
    MetricSpec(
        key="input_rate_regime",
        label="Input Regime",
        dtype=str,
        compute_level="run",
        compute_fn=_input_regime,
        is_invariant=True,
    )
)
