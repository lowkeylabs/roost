# src/owlroost/core/owl_runner.py

import ast
import json
import shutil
import time
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime
from io import StringIO
from pathlib import Path

import numpy as np
import owlplanner as owl
import pandas as pd
import toml
from loguru import logger

from owlroost.core.metrics_from_plan import write_metrics_json

# ---------------------------------------------------------------------
# Result object
# ---------------------------------------------------------------------


@dataclass
class PlanRunResult:
    status: str
    output_file: str | None = None
    summary: dict | None = None
    adjusted_toml: str | None = None


# ---------------------------------------------------------------------
# TOML override helpers
# ---------------------------------------------------------------------


def coerce_override_value(v):
    if isinstance(v, str):
        v = v.replace("\\ ", " ")
        try:
            return ast.literal_eval(v)
        except (ValueError, SyntaxError):
            return v
    return v


def _normalize_rates_selection(section_dict: dict):
    """
    Backward-compatible support for rates_selection.fromto
    Converts:
        fromto=[1966,1970]
    Into:
        from=1966
        to=1970
    """
    raw = section_dict.pop("fromto", None)
    if raw is None:
        return

    fromto = coerce_override_value(raw)
    if not isinstance(fromto, (list | tuple)) or len(fromto) != 2:
        raise ValueError(f"Invalid rates_selection.fromto value: {fromto}")

    frm, to = fromto
    section_dict["from"] = int(frm)
    section_dict["to"] = int(to)


def load_original_toml(case_file: str) -> str:
    with open(case_file, encoding="utf-8") as f:
        diconf = toml.load(f)
    return toml.dumps(diconf)


def load_and_override_toml(case_file: str, overrides: dict):
    """
    Generic section-based override merge.

    Assumptions:
      - Hydra group names match OWL section names
      - overrides is structured as:
            { section_name: { field: value } }
    """

    with open(case_file, encoding="utf-8") as f:
        diconf = toml.load(f)

    diconf = deepcopy(diconf)
    logger.debug("Overrides: {}", overrides)

    if not overrides:
        return diconf

    for section, values in overrides.items():
        if not isinstance(values, dict):
            raise RuntimeError(
                f"Override for section '{section}' must be a dict, got {type(values)}"
            )

        group = diconf.setdefault(section, {})

        # Special normalization for rates_selection
        if section == "rates_selection":
            values = dict(values)
            _normalize_rates_selection(values)

        for key, value in values.items():
            coerced = coerce_override_value(value)
            logger.debug("Overrides: {}: {}={}", section, key, coerced)
            group[key] = coerced

    return diconf


# ---------------------------------------------------------------------
# Inject ROOST + LONGEVITY sections
# ---------------------------------------------------------------------


def inject_runtime_sections(
    toml_dict: dict,
    roost_runtime: dict | None,
    longevity_runtime: dict | None,
):
    """
    Inject runtime-only metadata into effective TOML.
    """

    if roost_runtime:
        roost_section = toml_dict.setdefault("roost", {})
        for k, v in roost_runtime.items():
            if v is not None:
                roost_section[k] = v

    if longevity_runtime:
        longevity_section = toml_dict.setdefault("longevity", {})
        for k, v in longevity_runtime.items():
            longevity_section[k] = v


# ---------------------------------------------------------------------
# Optimization normalization
# ---------------------------------------------------------------------


def normalize_optimization(plan):
    objective = plan.objective
    solver_opts = plan.solverOptions

    if objective == "maxBequest":
        if "netSpending" not in solver_opts:
            raise RuntimeError("Objective=maxBequest requires solver option 'netSpending'")
        solver_opts.pop("bequest", None)

    elif objective == "maxSpending":
        if "bequest" not in solver_opts:
            raise RuntimeError("Objective=maxSpending requires solver option 'bequest'")
        solver_opts.pop("netSpending", None)

    else:
        raise RuntimeError(f"Unknown optimization objective: {objective}")


# ---------------------------------------------------------------------
# Core solver helpers
# ---------------------------------------------------------------------


def json_safe(obj):
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (datetime | date)):
        return obj.isoformat()
    if isinstance(obj, np.generic):
        return obj.item()
    if hasattr(obj, "__dict__"):
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def save_early_files(output_file: str, effective_toml: str, original_toml: str) -> None:
    output_path = Path(output_file)

    original_toml_path = output_path.with_suffix("").with_name(output_path.stem + "_original.toml")
    with open(original_toml_path, "w", encoding="utf-8") as f:
        f.write(original_toml)

    effective_toml_path = output_path.with_suffix("").with_name(
        output_path.stem + "_effective.toml"
    )
    with open(effective_toml_path, "w", encoding="utf-8") as f:
        f.write(effective_toml)


def solve_and_save(plan, output_file: str) -> None:
    normalize_optimization(plan)

    output_path = Path(output_file)

    rates_dict = {
        "Year": plan.year_n.tolist(),
        "S&P 500": plan.tau_kn[0].tolist(),
        "Corporate Baa": plan.tau_kn[1].tolist(),
        "T Bonds": plan.tau_kn[2].tolist(),
        "inflation": plan.tau_kn[3].tolist(),
    }

    rates_path = output_path.with_suffix("").with_name(output_path.stem + "_rates.xlsx")
    pd.DataFrame(rates_dict).to_excel(rates_path, index=False, sheet_name="Rates")

    # ------------------------------
    # Timing wrapper around solve()
    # ------------------------------
    start_time = time.time()
    start_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(start_time))

    plan.solve(plan.objective, plan.solverOptions)

    end_time = time.time()
    end_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(end_time))

    elapsed_seconds = end_time - start_time

    timing = {
        "solve_start": start_iso,
        "solve_end": end_iso,
        "elapsed_seconds": elapsed_seconds,
    }

    metrics_path = output_path.with_suffix("").with_name(output_path.stem + "_metrics.json")
    write_metrics_json(plan, metrics_path, timing)

    if plan.caseStatus != "solved":
        return

    p = Path(output_file)
    results_file = p.with_name(f"{p.stem}_results{p.suffix}")
    plan.saveWorkbook(basename=results_file, overwrite=True)

    summary_path = output_path.with_suffix("").with_name(output_path.stem + "_summary.json")
    with open(summary_path, "w") as f:
        json.dump(plan.summaryDic(), f, indent=2, sort_keys=False, default=json_safe)


# ---------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------


def run_single_case(
    *,
    case_file: str,
    overrides: dict,
    output_file: str,
    roost_runtime: dict | None = None,
    longevity_runtime: dict | None = None,
) -> PlanRunResult:
    """
    Run a single OWL case using direct section-based overrides
    and runtime metadata injection.
    """

    logger.debug("run_single_case overrides: {}", overrides)

    original_toml = load_original_toml(case_file)

    # Only apply structured section overrides
    toml_dict = load_and_override_toml(case_file, overrides)

    inject_runtime_sections(
        toml_dict,
        roost_runtime,
        longevity_runtime,
    )

    # Handle HFP relocation
    hfp_section = toml_dict.get("household_financial_profile", {})
    hfp_file = hfp_section.get("HFP_file_name")

    trial_path = Path(output_file).parent

    if hfp_file:
        hfp_path = Path(case_file).parent / hfp_file

        hfp_original = trial_path / f"{hfp_path.stem}_original{hfp_path.suffix}"
        shutil.copy2(hfp_path, hfp_original)

        hfp_modified = trial_path / f"{hfp_path.stem}_effective{hfp_path.suffix}"
        shutil.copy2(hfp_original, hfp_modified)
        hfp_section["HFP_file_name"] = hfp_modified.name

    modified_toml = toml.dumps(toml_dict)
    toml_buf = StringIO(modified_toml)
    toml_buf.seek(0)

    save_early_files(output_file, modified_toml, original_toml)

    plan = owl.readConfig(
        toml_buf,
        logstreams="loguru",
        loadHFP=False,
    )

    if hfp_file:
        plan.readHFP(str(hfp_modified))

    status = "unknown"

    try:
        solve_and_save(plan, output_file)
        status = (plan.caseStatus or "unknown").lower()

    except Exception:
        logger.exception("Trial failed with exception")
        status = "failed"

        # 🔥 CRITICAL: still write metrics for failed trials
        try:
            metrics_path = (
                Path(output_file)
                .with_suffix("")
                .with_name(Path(output_file).stem + "_metrics.json")
            )
            write_metrics_json(plan, metrics_path, timing={"elapsed_seconds": None})
        except Exception:
            logger.exception("Failed to write fallback metrics")

    # --------------------------------------------------
    # ALWAYS write status file
    # --------------------------------------------------
    status_file = Path(trial_path) / status.upper()
    status_file.touch(exist_ok=True)

    if status != "solved":
        return PlanRunResult(status=status)

    return PlanRunResult(
        status="solved",
        output_file=output_file,
        summary=plan.summaryDic(),
        adjusted_toml=modified_toml,
    )
