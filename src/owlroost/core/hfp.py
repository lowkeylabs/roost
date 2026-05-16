# src/owlroost/core/hfp.py

from __future__ import annotations

from copy import deepcopy
from io import StringIO
from pathlib import Path

import owlplanner.hfp_io as hfp_io
from loguru import logger
from owlplanner.mylogging import Logger

# =========================================================
# In-memory cache
# =========================================================

_HFP_CACHE = {}

# =========================================================
# Public API
# =========================================================


def summarize_hfp(
    case_path,
    inputs,
):
    """
    Load and summarize OWL HFP workbook.

    Returns lightweight normalized summary:

        {
            "has_hfp": True,
            "total_fixed_assets": 1234567.0,
            "total_debts": 250000.0,
            "mortgage_debt": 200000.0,
            "fixed_asset_count": 3,
            "debt_count": 2,
            "residence_value": 900000.0,
        }

    Returns empty/default summary if:
    - no HFP configured
    - workbook missing
    - workbook invalid
    """

    # =====================================================
    # Default summary
    # =====================================================

    summary = {
        "has_hfp": False,
        "total_fixed_assets": 0.0,
        "total_debts": 0.0,
        "mortgage_debt": 0.0,
        "fixed_asset_count": 0,
        "debt_count": 0,
        "residence_value": 0.0,
    }

    cache_key = None

    try:
        # =================================================
        # Resolve workbook path
        # =================================================

        hfp_section = inputs.get(
            "household_financial_profile",
            {},
        )

        hfp_name = hfp_section.get(
            "HFP_file_name",
        )

        if hfp_name in (
            None,
            "",
            "None",
        ):
            return deepcopy(summary)

        case_path = Path(case_path).resolve()

        hfp_path = (case_path.parent / hfp_name).resolve()

        # =================================================
        # Workbook existence
        # =================================================

        if not hfp_path.exists():
            logger.warning(f"HFP file not found: {hfp_path}")

            return deepcopy(summary)

        # =================================================
        # Cache lookup
        # =================================================

        cache_key = (
            str(hfp_path),
            hfp_path.stat().st_mtime,
        )

        cached = _HFP_CACHE.get(
            cache_key,
        )

        if cached is not None:
            return deepcopy(cached)

        # =================================================
        # Build OWL inputs
        # =================================================

        basic = inputs.get(
            "basic_info",
            {},
        )

        names = basic.get(
            "names",
            [],
        )

        life_expectancy = basic.get(
            "life_expectancy",
            [],
        )

        if not names or not life_expectancy:
            _HFP_CACHE[cache_key] = deepcopy(summary)

            return deepcopy(summary)

        # =================================================
        # Load via OWL HFP subsystem
        # =================================================

        logger.debug(f"Loading HFP: {hfp_path}")

        mylog = Logger(logstreams=[StringIO(), StringIO()])
        (
            _finput,
            _time_lists,
            house_lists,
            _df_dict,
        ) = hfp_io.read(
            str(hfp_path),
            names,
            life_expectancy,
            mylog,
        )

        summary["has_hfp"] = True

        # =================================================
        # Fixed Assets
        # =================================================

        fixed_assets = house_lists.get(
            "Fixed Assets",
        )

        if fixed_assets is not None and not fixed_assets.empty:
            active_df = fixed_assets

            # ---------------------------------------------
            # Active filtering
            # ---------------------------------------------

            if "active" in active_df.columns:
                active_df = active_df[active_df["active"].astype(bool)]

            summary["fixed_asset_count"] = int(len(active_df))

            # ---------------------------------------------
            # Total value
            # ---------------------------------------------

            if "value" in active_df.columns:
                total = active_df["value"].fillna(0).sum()

                summary["total_fixed_assets"] = float(total)

            # ---------------------------------------------
            # Residence value
            # ---------------------------------------------

            if "type" in active_df.columns and "value" in active_df.columns:
                residence_df = active_df[active_df["type"].astype(str).str.lower() == "residence"]

                residence_total = residence_df["value"].fillna(0).sum()

                summary["residence_value"] = float(residence_total)

        # =================================================
        # Debts
        # =================================================

        debts = house_lists.get(
            "Debts",
        )

        if debts is not None and not debts.empty:
            active_df = debts

            # ---------------------------------------------
            # Active filtering
            # ---------------------------------------------

            if "active" in active_df.columns:
                active_df = active_df[active_df["active"].astype(bool)]

            summary["debt_count"] = int(len(active_df))

            # ---------------------------------------------
            # Total debt
            # ---------------------------------------------

            if "amount" in active_df.columns:
                total = active_df["amount"].fillna(0).sum()

                summary["total_debts"] = float(total)

            # ---------------------------------------------
            # Mortgage debt
            # ---------------------------------------------

            if "type" in active_df.columns and "amount" in active_df.columns:
                mortgage_df = active_df[active_df["type"].astype(str).str.lower() == "mortgage"]

                mortgage_total = mortgage_df["amount"].fillna(0).sum()

                summary["mortgage_debt"] = float(mortgage_total)

        # =================================================
        # Cache successful result
        # =================================================

        _HFP_CACHE[cache_key] = deepcopy(summary)

        return deepcopy(summary)

    except Exception as e:
        logger.warning(f"Failed to summarize HFP: {e}")

        # =================================================
        # Cache failure result
        # =================================================

        if cache_key is not None:
            _HFP_CACHE[cache_key] = deepcopy(summary)

        return deepcopy(summary)
