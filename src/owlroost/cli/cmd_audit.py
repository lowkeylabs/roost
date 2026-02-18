from __future__ import annotations

import sys
import tomllib
from pathlib import Path

import click

# OWL metadata loader
from owlplanner.rate_models.loader import _collect_all_model_metadata

RESULTS_DIR = Path("results")

# Column widths
W_ID = 3
W_CASE = 18
W_DATE = 12
W_TIME = 8
W_RUNS = 5
W_TPR = 5
W_TRIALS = 7
W_MASTER = 10
W_SEEDS = 6
W_DUPL = 4
W_STATUS = 6

TABLE_WIDTH = 120


# =====================================================================
# CLI ENTRY
# =====================================================================


@click.command(name="audit")
@click.argument("experiment_id", required=False, type=int)
@click.option("--strict", is_flag=True)
@click.option("--verbose", is_flag=True)
@click.option("--purge", is_flag=True)
@click.option("--runs", is_flag=True)
def cmd_audit(experiment_id, strict, verbose, purge, runs):
    if not RESULTS_DIR.exists():
        click.echo("Results directory not found.")
        sys.exit(1)

    experiments = discover_all_experiments()

    if not experiments:
        click.echo("No experiments found.")
        sys.exit(0)

    if experiment_id is None:
        if runs:
            if purge:
                click.echo("ERROR: --purge only valid in overview mode.")
                sys.exit(1)

            render_run_audit(experiments)

            if strict:
                if any(not audit_run(run)["pass"] for exp in experiments for run in exp["runs"]):
                    sys.exit(1)

            return

        render_global_overview(experiments, strict, purge)
        return

    if experiment_id < 0 or experiment_id >= len(experiments):
        raise click.ClickException("Invalid experiment ID")

    render_run_audit(experiments, selected_id=experiment_id)

    if strict:
        selected = experiments[experiment_id]
        if any(not audit_run(run)["pass"] for run in selected["runs"]):
            sys.exit(1)


# =====================================================================
# MODEL METADATA
# =====================================================================

_MODEL_METADATA = {m["method"]: m for m in _collect_all_model_metadata()}


def method_is_stochastic(method: str) -> bool:
    md = _MODEL_METADATA.get(method)
    if not md:
        return True
    return not md.get("deterministic", True) and not md.get("constant", True)


# =====================================================================
# OVERVIEW
# =====================================================================


def render_global_overview(experiments, strict, purge):
    click.echo("\nAUDIT OVERVIEW")
    click.echo("=" * TABLE_WIDTH)

    header = (
        f"{'ID':>3} "
        f"{'CASE':<18} "
        f"{'DATE':<12} "
        f"{'TIME':<8} "
        f"{'RUNS':>5} "
        f"{'TPR':>5} "
        f"{'TRIALS':>7} "
        f"{'MASTER':>10} "
        f"{'SEEDS':>6} "
        f"{'STATUS':>6}"
    )
    click.echo(header)
    click.echo("-" * TABLE_WIDTH)

    rows = []

    for i, exp in enumerate(experiments):
        status = audit_experiment(exp)
        rows.append((i, exp, status))

    for i, exp, status in rows:
        seeds = "PASS" if status["seed_consistent"] else "FAIL"
        overall = "PASS" if status["pass"] else "FAIL"

        click.echo(
            f"{i:>3} "
            f"{exp['case']:<18} "
            f"{exp['date']:<12} "
            f"{exp['time']:<8} "
            f"{status['runs']:>5} "
            f"{status['tpr']:>5} "
            f"{status['trials']:>7} "
            f"{str(status['master']):>10} "
            f"{seeds:>6} "
            f"{overall:>6}"
        )

    click.echo("=" * TABLE_WIDTH)


# =====================================================================
# RUN AUDIT
# =====================================================================


def render_run_audit(experiments, selected_id=None):
    click.echo("\nRUN AUDIT")
    click.echo("=" * TABLE_WIDTH)

    header = (
        f"{'EXP':>4} "
        f"{'CASE':<18} "
        f"{'RUN':<8} "
        f"{'TPR':>5} "
        f"{'COMP/TOT':>10} "
        f"{'XRUN':>6} "
        f"{'UNIQ':>6} "
        f"{'S0':>10} "
        f"{'S1':>10} "
        f"{'S2':>10} "
        f"{'L0':>10} "
        f"{'L1':>10} "
        f"{'L2':>10}"
    )

    click.echo(header)
    click.echo("-" * TABLE_WIDTH)

    for exp_id, exp in enumerate(experiments):
        if selected_id is not None and exp_id != selected_id:
            continue

        xrun_result = audit_xrun(exp)

        xrun_text = "N/A" if xrun_result is None else "PASS" if xrun_result else "FAIL"

        for run in exp["runs"]:
            run_status = audit_run(run)

            comp_display = f"{run_status['complete']}/{run_status['total']}"

            # NEW: UNIQ logic
            if run_status["uniq_applicable"] is False:
                uniq_text = "N/A"
            else:
                uniq_text = "PASS" if run_status["uniq_pass"] else "FAIL"

            rate_seeds = (run_status["rate_seeds"] + ["—"] * 3)[:3]
            life_seeds = (run_status["longevity_seeds"] + ["—"] * 3)[:3]

            click.echo(
                f"{exp_id:>4} "
                f"{exp['case']:<18} "
                f"{run['name']:<8} "
                f"{run_status['tpr']:>5} "
                f"{comp_display:>10} "
                f"{xrun_text:>6} "
                f"{uniq_text:>6} "
                f"{str(rate_seeds[0]):>10} "
                f"{str(rate_seeds[1]):>10} "
                f"{str(rate_seeds[2]):>10} "
                f"{str(life_seeds[0]):>10} "
                f"{str(life_seeds[1]):>10} "
                f"{str(life_seeds[2]):>10}"
            )

    click.echo("=" * TABLE_WIDTH)


# =====================================================================
# CORE AUDIT LOGIC
# =====================================================================


def audit_xrun(experiment):
    runs = experiment["runs"]
    if not runs:
        return None

    methods = []

    for run in runs:
        if not run["trials"]:
            continue
        toml_path = next(run["trials"][0].glob("*_effective.toml"), None)
        if not toml_path:
            continue
        data = tomllib.load(toml_path.open("rb"))
        method = data.get("rates_selection", {}).get("method")
        methods.append(method)

    if not methods:
        return None

    if len(set(methods)) != 1:
        return None

    method = methods[0]

    if not method_is_stochastic(method):
        return None

    trial_counts = [len(r["trials"]) for r in runs]
    if len(set(trial_counts)) != 1:
        return False

    for i in range(trial_counts[0]):
        ref = extract_seeds(runs[0]["trials"][i])
        for r in runs[1:]:
            if extract_seeds(r["trials"][i]) != ref:
                return False

    return True


def audit_run(run):
    trials = run["trials"]
    total = len(trials)

    if total == 0:
        return {
            "tpr": 0,
            "complete": 0,
            "total": 0,
            "uniq_pass": False,
            "uniq_applicable": False,
            "rate_seeds": [],
            "longevity_seeds": [],
            "pass": False,
        }

    # Detect method
    toml_path = next(trials[0].glob("*_effective.toml"), None)
    method = None
    if toml_path:
        data = tomllib.load(toml_path.open("rb"))
        method = data.get("rates_selection", {}).get("method")

    stochastic = method_is_stochastic(method)

    # ------------------------------------------------------------
    # Determine if UNIQ applies
    # ------------------------------------------------------------

    if not stochastic or total == 1:
        uniq_applicable = False
        uniq = True  # does not matter
    else:
        uniq_applicable = True
        uniq = True

    seen = set()

    rate_seeds = []
    longevity_seeds = []

    for trial in trials:
        seeds = extract_seeds(trial)
        rs = seeds.get("rate_seed")
        ls = seeds.get("longevity_seed")

        if len(rate_seeds) < 3:
            rate_seeds.append(rs if rs is not None else "—")
        if len(longevity_seeds) < 3:
            longevity_seeds.append(ls if ls is not None else "—")

        if not uniq_applicable:
            continue

        if rs is None or ls is None:
            uniq = False
            continue

        key = (rs, ls)

        if key in seen:
            uniq = False
        else:
            seen.add(key)

    complete = sum(1 for t in trials if get_trial_status(t) in ("SOLVED", "FAILED"))

    return {
        "tpr": total,
        "complete": complete,
        "total": total,
        "uniq_pass": uniq,
        "uniq_applicable": uniq_applicable,
        "rate_seeds": rate_seeds,
        "longevity_seeds": longevity_seeds,
        "pass": True if not uniq_applicable else uniq,
    }


def audit_experiment(experiment):
    runs = experiment["runs"]
    trial_counts = [len(r["trials"]) for r in runs]

    tpr = trial_counts[0] if trial_counts else 0
    trials = sum(trial_counts)

    xrun = audit_xrun(experiment)

    seed_consistent = True if xrun is None else xrun

    incomplete = sum(1 for r in runs for t in r["trials"] if get_trial_status(t) == "INCOMPLETE")

    overall = seed_consistent and incomplete == 0

    return {
        "runs": len(runs),
        "tpr": tpr,
        "trials": trials,
        "master": None,
        "seed_consistent": seed_consistent,
        "incomplete_trials": incomplete,
        "pass": overall,
    }


# =====================================================================
# DISCOVERY
# =====================================================================


def discover_all_experiments():
    experiments = []

    for case_dir in sorted(p for p in RESULTS_DIR.iterdir() if p.is_dir()):
        case_name = case_dir.name

        for date_dir in sorted(p for p in case_dir.iterdir() if p.is_dir()):
            for time_dir in sorted(p for p in date_dir.iterdir() if p.is_dir()):
                runs = []

                for run_dir in sorted(
                    p for p in time_dir.iterdir() if p.is_dir() and p.name.startswith("run_")
                ):
                    trials_dir = run_dir / "trials"
                    trials = (
                        sorted(p for p in trials_dir.iterdir() if p.is_dir())
                        if trials_dir.exists()
                        else []
                    )

                    runs.append(
                        {
                            "name": run_dir.name,
                            "path": run_dir,
                            "trials": trials,
                        }
                    )

                if runs:
                    experiments.append(
                        {
                            "case": case_name,
                            "date": date_dir.name,
                            "time": time_dir.name,
                            "runs": runs,
                            "path": case_dir / date_dir.name / time_dir.name,
                        }
                    )

    return experiments


# =====================================================================
# HELPERS
# =====================================================================


def get_trial_status(trial_dir: Path):
    if (trial_dir / "SOLVED").exists():
        return "SOLVED"
    if (trial_dir / "UNSUCCESSFUL").exists():
        return "FAILED"
    return "INCOMPLETE"


def extract_seeds(trial_dir: Path):
    toml_path = next(trial_dir.glob("*_effective.toml"), None)
    if not toml_path:
        return {}

    data = tomllib.load(toml_path.open("rb"))

    return {
        "rate_seed": data.get("rates_selection", {}).get("rate_seed"),
        "longevity_seed": data.get("basic_info", {}).get("longevity_seed"),
    }
