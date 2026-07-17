"""Data preparation helpers shared by notebooks and tests."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit, train_test_split


def stratified_sample(
    data: pd.DataFrame,
    n: int | None,
    strata_cols: Sequence[str],
    seed: int = 42,
) -> pd.DataFrame:
    """Return exactly ``n`` rows while approximately preserving all strata.

    ``StratifiedShuffleSplit`` avoids the index-reset/top-up issue in the first
    notebook, where the sampled frame's reset index was compared with the
    original frame's index.
    """
    if n is None or n >= len(data):
        return data.sample(frac=1, random_state=seed).reset_index(drop=True)
    if n <= 0:
        raise ValueError("n must be positive")

    strata = data.loc[:, list(strata_cols)].astype("string").agg("__".join, axis=1)
    if strata.value_counts().min() < 2:
        raise ValueError("Each stratum needs at least two rows for stratified sampling")

    splitter = StratifiedShuffleSplit(n_splits=1, train_size=n, random_state=seed)
    selected, _ = next(splitter.split(np.zeros(len(data)), strata))
    return data.iloc[selected].sample(frac=1, random_state=seed).reset_index(drop=True)


def stratified_train_test_split(
    data: pd.DataFrame,
    strata_cols: Sequence[str],
    test_size: float = 0.2,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split once and keep discovery strictly on train."""
    strata = data.loc[:, list(strata_cols)].astype("string").agg("__".join, axis=1)
    train_idx, test_idx = train_test_split(
        np.arange(len(data)),
        test_size=test_size,
        random_state=seed,
        stratify=strata,
    )
    return (
        data.iloc[train_idx].reset_index(drop=True),
        data.iloc[test_idx].reset_index(drop=True),
    )


def create_derived_variables(data: pd.DataFrame) -> pd.DataFrame:
    """Create the six deterministic variables used by the controlled benchmark.

    These columns are synthetic evaluation fixtures. They must not be presented
    as official ACS business rules or as independently discovered domain facts.
    """
    out = data.copy()
    for column in ["AGEP", "SCHL", "MAR", "WKHP", "SEX", "RELP", "COW", "income_label"]:
        if column in out:
            out[column] = pd.to_numeric(out[column], errors="coerce")

    def select_text(conditions: list[pd.Series], choices: list[str]) -> pd.Series:
        return pd.Series(
            np.select(conditions, choices, default=None),
            index=out.index,
            dtype="string",
        )

    out["age_group"] = select_text(
        [out["AGEP"] < 18, out["AGEP"].between(18, 64), out["AGEP"] >= 65],
        ["Under18", "WorkingAge", "Senior"],
    )
    out["education_group"] = select_text(
        [out["SCHL"] <= 15, out["SCHL"].between(16, 20), out["SCHL"] >= 21],
        ["BelowHS", "HS_College", "BachelorPlus"],
    )
    out["working_hours_group"] = select_text(
        [
            out["WKHP"].between(1, 14),
            out["WKHP"].between(15, 34),
            out["WKHP"].between(35, 45),
            out["WKHP"] > 45,
        ],
        ["VeryLow", "PartTime", "Standard", "Overtime"],
    )

    out["fulltime_status"] = pd.Series(pd.NA, index=out.index, dtype="string")
    valid_hours = out["WKHP"].notna()
    out.loc[valid_hours, "fulltime_status"] = np.where(
        out.loc[valid_hours, "WKHP"] >= 35,
        "Fulltime",
        "NonFulltime",
    )
    out["marital_group"] = select_text(
        [out["MAR"] == 1, out["MAR"].isin([2, 3, 4, 5])],
        ["Married", "NotMarried"],
    )
    out["income_group"] = select_text(
        [out["income_label"] == 1, out["income_label"] == 0],
        ["HighIncome", "LowIncome"],
    )
    return out
