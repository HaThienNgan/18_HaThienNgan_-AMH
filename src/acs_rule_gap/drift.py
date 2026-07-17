"""Dependency-distribution drift with paired comparisons and group-safe LOO."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from .metrics import theils_u


def theils_u_matrix(data: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    matrix = pd.DataFrame(index=columns, columns=columns, dtype=float)
    for lhs in columns:
        for rhs in columns:
            matrix.loc[lhs, rhs] = 1.0 if lhs == rhs else theils_u(data, lhs, rhs)
    return matrix


def dependency_drift_score(matrix_a: pd.DataFrame, matrix_b: pd.DataFrame) -> float:
    """Mean absolute off-diagonal change between aligned dependency matrices."""
    if list(matrix_a.index) != list(matrix_b.index) or list(matrix_a.columns) != list(matrix_b.columns):
        raise ValueError("DDS matrices must have identical labels and ordering")
    difference = np.abs(matrix_a.to_numpy(dtype=float) - matrix_b.to_numpy(dtype=float))
    mask = ~np.eye(len(difference), dtype=bool)
    return float(difference[mask].mean()) if mask.any() else 0.0


def paired_dependency_drift(
    clean: pd.DataFrame,
    changed: pd.DataFrame,
    columns: Sequence[str],
    sample_size: int | None = None,
    seed: int = 42,
) -> float:
    """Compare the same row positions before and after a transformation."""
    if len(clean) != len(changed):
        raise ValueError("Paired DDS needs clean and changed frames with equal length")
    n = len(clean) if sample_size is None else min(sample_size, len(clean))
    positions = np.random.default_rng(seed).choice(len(clean), size=n, replace=False)
    clean_sample = clean.iloc[positions].reset_index(drop=True)
    changed_sample = changed.iloc[positions].reset_index(drop=True)
    return dependency_drift_score(
        theils_u_matrix(clean_sample, columns),
        theils_u_matrix(changed_sample, columns),
    )


def clean_dds_threshold(
    data: pd.DataFrame,
    columns: Sequence[str],
    sample_size: int = 5_000,
    repetitions: int = 100,
    quantile: float = 0.95,
    seed: int = 42,
) -> tuple[float, np.ndarray]:
    """Sampling-only reference distribution for DDS."""
    rng = np.random.default_rng(seed)
    n = min(sample_size, len(data))
    scores = []
    for _ in range(repetitions):
        a = data.iloc[rng.choice(len(data), size=n, replace=True)].reset_index(drop=True)
        b = data.iloc[rng.choice(len(data), size=n, replace=True)].reset_index(drop=True)
        scores.append(dependency_drift_score(theils_u_matrix(a, columns), theils_u_matrix(b, columns)))
    values = np.asarray(scores, dtype=float)
    return float(np.quantile(values, quantile)), values


def leave_one_group_out_dds(
    data: pd.DataFrame,
    group_col: str,
    columns: Sequence[str],
    sample_size: int = 5_000,
    permutation_reps: int = 50,
    seed: int = 42,
) -> pd.DataFrame:
    """Compare each group with the other groups and estimate a permutation p-value.

    The grouping column is always excluded from the dependency matrix. Including
    it made the original state LOO comparison mechanically large because it was
    constant on one side and multi-valued on the other.
    """
    analysis_columns = [column for column in columns if column != group_col]
    rng = np.random.default_rng(seed)
    rows = []

    for group in sorted(data[group_col].dropna().unique()):
        in_group = data[data[group_col] == group]
        out_group = data[data[group_col] != group]
        n = min(sample_size, len(in_group), len(out_group))
        a = in_group.sample(n=n, random_state=seed).reset_index(drop=True)
        b = out_group.sample(n=n, random_state=seed).reset_index(drop=True)
        observed = dependency_drift_score(
            theils_u_matrix(a, analysis_columns),
            theils_u_matrix(b, analysis_columns),
        )

        pooled = pd.concat([a, b], ignore_index=True)
        null_scores = []
        for _ in range(permutation_reps):
            order = rng.permutation(len(pooled))
            perm_a = pooled.iloc[order[:n]]
            perm_b = pooled.iloc[order[n : 2 * n]]
            null_scores.append(
                dependency_drift_score(
                    theils_u_matrix(perm_a, analysis_columns),
                    theils_u_matrix(perm_b, analysis_columns),
                )
            )
        p_value = (1 + sum(score >= observed for score in null_scores)) / (permutation_reps + 1)
        rows.append(
            {
                group_col: group,
                "group_rows": len(in_group),
                "balanced_rows_used": n,
                "DDS_vs_other_groups": observed,
                "permutation_p_value": p_value,
                "null_DDS_95": float(np.quantile(null_scores, 0.95)),
            }
        )
    return pd.DataFrame(rows).sort_values("DDS_vs_other_groups", ascending=False).reset_index(drop=True)
