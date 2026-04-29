from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tomllib
from pathlib import Path

import click
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
W_DUPL = 6
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
@click.option("--dry-run", is_flag=True, help="Show what would be purged without deleting.")
@click.option("--runs", is_flag=True)
def cmd_audit(experiment_id, strict, verbose, purge, dry_run, runs):
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

        render_global_overview(experiments, strict, purge, dry_run)
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


def render_global_overview(experiments, strict, purge, dry_run):
    click.echo("\nAUDIT OVERVIEW")
    click.echo("=" * TABLE_WIDTH)

    header = (
        f"{'ID':>{W_ID}} "
        f"{'CASE':<{W_CASE}} "
        f"{'DATE':<{W_DATE}} "
        f"{'TIME':<{W_TIME}} "
        f"{'RUNS':>{W_RUNS}} "
        f"{'TPR':>{W_TPR}} "
        f"{'TRIALS':>{W_TRIALS}} "
        f"{'MASTER':>{W_MASTER}} "
        f"{'SEEDS':>{W_SEEDS}} "
        f"{'DUPL':>{W_DUPL}} "
        f"{'STATUS':>{W_STATUS}}"
    )
    click.echo(header)
    click.echo("-" * TABLE_WIDTH)

    # -------------------------------------------------------------
    # Compute signatures
    # -------------------------------------------------------------

    signatures = {}
    canonical_index = {}

    for idx, exp in enumerate(experiments):
        sig = compute_signature(exp)
        signatures[idx] = sig

        if sig is None:
            continue

        canonical_index[sig] = idx  # most recent wins (higher index)

    # -------------------------------------------------------------
    # Render rows
    # -------------------------------------------------------------

    for idx, exp in enumerate(experiments):
        status = audit_experiment(exp)

        seeds = "PASS" if status["seed_consistent"] else "FAIL"
        overall = "PASS" if status["pass"] else "FAIL"

        sig = signatures.get(idx)
        dupl_text = "—"

        if sig is not None:
            canonical = canonical_index.get(sig)
            if canonical is not None and canonical != idx:
                dupl_text = str(canonical)

        case_display = clip(exp["case"], W_CASE)

        click.echo(
            f"{idx:>{W_ID}} "
            f"{case_display:<{W_CASE}} "
            f"{exp['date']:<{W_DATE}} "
            f"{exp['time']:<{W_TIME}} "
            f"{status['runs']:>{W_RUNS}} "
            f"{status['tpr']:>{W_TPR}} "
            f"{status['trials']:>{W_TRIALS}} "
            f"{str(status['master']):>{W_MASTER}} "
            f"{seeds:>{W_SEEDS}} "
            f"{dupl_text:>{W_DUPL}} "
            f"{overall:>{W_STATUS}}"
        )

    click.echo("=" * TABLE_WIDTH)

    # -------------------------------------------------------------
    # Purge older duplicates
    # -------------------------------------------------------------

    if purge:
        click.echo("\nPurge Mode:")
        for idx, exp in enumerate(experiments):
            sig = signatures.get(idx)
            if sig is None:
                continue

            if canonical_index.get(sig) != idx:
                if dry_run:
                    click.echo(f"[DRY-RUN] Would purge experiment {idx}: {exp['case']}")
                else:
                    shutil.rmtree(exp["path"])
                    click.echo(f"Purged experiment {idx}: {exp['case']}")


# =====================================================================
# RUN AUDIT
# =====================================================================


def render_run_audit(experiments, selected_id=None):
    click.echo("\nRUN AUDIT")
    click.echo("=" * TABLE_WIDTH)

    header = (
        f"{'EXP':>{W_ID + 1}} "
        f"{'CASE':<{W_CASE}} "
        f"{'RUN':<{W_TIME}} "
        f"{'TPR':>{W_TPR}} "
        f"{'COMP/TOT':>{W_MASTER}} "
        f"{'XRUN':>{W_SEEDS}} "
        f"{'UNIQ':>{W_SEEDS}} "
        f"{'S0':>{W_MASTER}} "
        f"{'S1':>{W_MASTER}} "
        f"{'S2':>{W_MASTER}} "
        f"{'L0':>{W_MASTER}} "
        f"{'L1':>{W_MASTER}} "
        f"{'L2':>{W_MASTER}}"
    )

    click.echo(header)
    click.echo("-" * TABLE_WIDTH)

    for exp_id, exp in enumerate(experiments):
        if selected_id is not None and exp_id != selected_id:
            continue

        xrun_result = audit_xrun(exp)
        case_display = clip(exp["case"], W_CASE)

        xrun_text = "N/A" if xrun_result is None else "PASS" if xrun_result else "FAIL"

        for run in exp["runs"]:
            run_status = audit_run(run)
            comp_display = f"{run_status['complete']}/{run_status['total']}"

            uniq_text = (
                "N/A"
                if run_status["uniq_applicable"] is False
                else "PASS"
                if run_status["uniq_pass"]
                else "FAIL"
            )

            rate_seeds = (run_status["rate_seeds"] + ["—"] * 3)[:3]
            life_seeds = (run_status["longevity_seeds"] + ["—"] * 3)[:3]

            click.echo(
                f"{exp_id:>{W_ID + 1}} "
                f"{case_display:<{W_CASE}} "
                f"{run['name']:<{W_TIME}} "
                f"{run_status['tpr']:>{W_TPR}} "
                f"{comp_display:>{W_MASTER}} "
                f"{xrun_text:>{W_SEEDS}} "
                f"{uniq_text:>{W_SEEDS}} "
                f"{str(rate_seeds[0]):>{W_MASTER}} "
                f"{str(rate_seeds[1]):>{W_MASTER}} "
                f"{str(rate_seeds[2]):>{W_MASTER}} "
                f"{str(life_seeds[0]):>{W_MASTER}} "
                f"{str(life_seeds[1]):>{W_MASTER}} "
                f"{str(life_seeds[2]):>{W_MASTER}}"
            )

    click.echo("=" * TABLE_WIDTH)


# =====================================================================
# SIGNATURE
# =====================================================================


def compute_signature(experiment):
    runs = experiment["runs"]
    if not runs:
        return None

    trials = runs[0]["trials"]
    if not trials:
        return None

    toml_path = next(trials[0].glob("*_effective.toml"), None)
    if not toml_path:
        return None

    data = tomllib.load(toml_path.open("rb"))

    data.get("rates_selection", {}).pop("rate_seed", None)
    data.get("basic_info", {}).pop("longevity_seed", None)

    canonical = json.dumps(data, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


# =====================================================================
# EXISTING AUDIT LOGIC (UNCHANGED)
# =====================================================================

# (Everything below remains identical to your current logic)


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

    toml_path = next(trials[0].glob("*_effective.toml"), None)
    method = None
    if toml_path:
        data = tomllib.load(toml_path.open("rb"))
        method = data.get("rates_selection", {}).get("method")

    stochastic = method_is_stochastic(method)

    if not stochastic or total == 1:
        uniq_applicable = False
        uniq = True
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


def clip(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    return text[: width - 3] + "..."
