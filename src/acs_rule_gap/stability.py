"""Stability selection and permutation tests for raw-variable candidates."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from .metrics import pairwise_dependency_scores, theils_u


def stable_dependency_candidates(
    data: pd.DataFrame,
    columns: Sequence[str],
    resamples: int = 30,
    sample_size: int = 20_000,
    top_k: int = 20,
    max_rhs_cardinality: int = 30,
    min_avg_lhs_support: float = 20.0,
    seed: int = 42,
) -> pd.DataFrame:
    """Rank raw-variable edges by bootstrap selection frequency.

    Cardinality guards reduce the chance that near-unique identifiers dominate
    purely because each LHS value has very few observations.
    """
    rng = np.random.default_rng(seed)
    n = min(sample_size, len(data))
    selected_rows: list[pd.DataFrame] = []

    for replicate in range(resamples):
        positions = rng.choice(len(data), size=n, replace=True)
        sample = data.iloc[positions].reset_index(drop=True)
        scores = pairwise_dependency_scores(sample, columns)
        eligible = scores[
            (scores["rhs_cardinality"] <= max_rhs_cardinality)
            & (scores["avg_lhs_support"] >= min_avg_lhs_support)
        ].nlargest(top_k, "TheilsU")
        eligible = eligible.assign(replicate=replicate, selected=1)
        selected_rows.append(eligible)

    selected = pd.concat(selected_rows, ignore_index=True)
    summary = (
        selected.groupby(["lhs", "rhs"], as_index=False)
        .agg(
            selections=("selected", "sum"),
            TheilsU_median=("TheilsU", "median"),
            TheilsU_mean=("TheilsU", "mean"),
            TheilsU_std=("TheilsU", "std"),
            lhs_cardinality=("lhs_cardinality", "median"),
            rhs_cardinality=("rhs_cardinality", "median"),
            avg_lhs_support=("avg_lhs_support", "median"),
        )
    )
    summary["selection_frequency"] = summary["selections"] / resamples
    return summary.sort_values(
        ["selection_frequency", "TheilsU_median"], ascending=False
    ).reset_index(drop=True)


def _benjamini_hochberg(p_values: np.ndarray) -> np.ndarray:
    order = np.argsort(p_values)
    ranked = p_values[order]
    adjusted = ranked * len(ranked) / np.arange(1, len(ranked) + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    result = np.empty_like(adjusted)
    result[order] = np.clip(adjusted, 0.0, 1.0)
    return result


def permutation_test_edges(
    data: pd.DataFrame,
    edges: pd.DataFrame,
    permutations: int = 100,
    sample_size: int = 20_000,
    seed: int = 42,
) -> pd.DataFrame:
    """Test shortlisted directional edges and control FDR across the shortlist."""
    rng = np.random.default_rng(seed)
    n = min(sample_size, len(data))
    sample = data.iloc[rng.choice(len(data), size=n, replace=False)].reset_index(drop=True)
    rows = []
    for edge in edges[["lhs", "rhs"]].drop_duplicates().itertuples(index=False):
        observed = theils_u(sample, edge.lhs, edge.rhs)
        null = []
        original_rhs = sample[edge.rhs].to_numpy(copy=True)
        for _ in range(permutations):
            permuted = sample[[edge.lhs, edge.rhs]].copy()
            permuted[edge.rhs] = rng.permutation(original_rhs)
            null.append(theils_u(permuted, edge.lhs, edge.rhs))
        p_value = (1 + sum(value >= observed for value in null)) / (permutations + 1)
        rows.append(
            {
                "lhs": edge.lhs,
                "rhs": edge.rhs,
                "TheilsU_observed": observed,
                "permutation_p_value": p_value,
                "null_95": float(np.quantile(null, 0.95)),
            }
        )
    result = pd.DataFrame(rows)
    result["fdr_q_value"] = _benjamini_hochberg(result["permutation_p_value"].to_numpy())
    return result.sort_values(["fdr_q_value", "TheilsU_observed"]).reset_index(drop=True)
