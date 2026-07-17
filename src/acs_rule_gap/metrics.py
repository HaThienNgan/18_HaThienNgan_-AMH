"""Dependency metrics with consistent normalization and finite-sample guards."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from scipy.stats import entropy
from sklearn.metrics import mutual_info_score


def _as_category(series: pd.Series) -> pd.Series:
    return series.astype("object").where(series.notna(), "__MISSING__").astype(str)


def exact_fd_score(data: pd.DataFrame, lhs: str, rhs: str) -> float:
    pairs = pd.DataFrame({"lhs": _as_category(data[lhs]), "rhs": _as_category(data[rhs])})
    return float(pairs.groupby("lhs", observed=True)["rhs"].nunique(dropna=False).max() == 1)


def q_strength(data: pd.DataFrame, lhs: str, rhs: str) -> float:
    """Normalized dependency quality in [0, 1], with an FD scoring 1.

    The original implementation returned ``1 - 1 / |dom(rhs)|`` for a perfect
    dependency. Here each group's extra RHS diversity is normalized by the
    largest possible extra diversity, so scores are comparable across RHS
    cardinalities.
    """
    x, y = _as_category(data[lhs]), _as_category(data[rhs])
    rhs_domain = y.nunique(dropna=False)
    if rhs_domain <= 1:
        return 1.0

    grouped = pd.DataFrame({"x": x, "y": y}).groupby("x", observed=True)
    penalty = sum(
        (len(group) / len(data))
        * ((group["y"].nunique(dropna=False) - 1) / (rhs_domain - 1))
        for _, group in grouped
    )
    return float(np.clip(1.0 - penalty, 0.0, 1.0))


def theils_u(data: pd.DataFrame, lhs: str, rhs: str) -> float:
    """Directional uncertainty coefficient U(rhs | lhs).

    Both mutual information and entropy use natural logarithms. The previous
    notebook divided MI in nats by entropy in bits, capping perfect relations at
    ln(2) ~= 0.693 instead of 1.
    """
    x, y = _as_category(data[lhs]), _as_category(data[rhs])
    h_y = entropy(y.value_counts(normalize=True))
    if np.isclose(h_y, 0.0):
        return 1.0
    return float(np.clip(mutual_info_score(x, y) / h_y, 0.0, 1.0))


def normalized_mutual_information(data: pd.DataFrame, col1: str, col2: str) -> float:
    """Symmetric NMI using max(H(X), H(Y)) as the normalizer."""
    x, y = _as_category(data[col1]), _as_category(data[col2])
    h_x = entropy(x.value_counts(normalize=True))
    h_y = entropy(y.value_counts(normalize=True))
    denominator = max(h_x, h_y)
    if np.isclose(denominator, 0.0):
        return 1.0
    return float(np.clip(mutual_info_score(x, y) / denominator, 0.0, 1.0))


def cramers_v(data: pd.DataFrame, col1: str, col2: str) -> float:
    """Bias-corrected Cramer's V for categorical association."""
    table = pd.crosstab(_as_category(data[col1]), _as_category(data[col2])).to_numpy()
    if table.size == 0 or table.sum() <= 1:
        return 0.0

    n = table.sum()
    expected = table.sum(axis=1, keepdims=True) @ table.sum(axis=0, keepdims=True) / n
    valid = expected > 0
    chi2 = (((table - expected) ** 2) / np.where(valid, expected, 1.0))[valid].sum()
    phi2 = chi2 / n
    rows, cols = table.shape
    phi2_corrected = max(0.0, phi2 - ((cols - 1) * (rows - 1)) / (n - 1))
    rows_corrected = rows - ((rows - 1) ** 2) / (n - 1)
    cols_corrected = cols - ((cols - 1) ** 2) / (n - 1)
    denominator = min(rows_corrected - 1, cols_corrected - 1)
    return float(np.sqrt(phi2_corrected / denominator)) if denominator > 0 else 0.0


def pairwise_dependency_scores(data: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    """Score every directed pair and retain cardinality diagnostics."""
    rows: list[dict[str, float | int | str]] = []
    for lhs in columns:
        for rhs in columns:
            if lhs == rhs:
                continue
            lhs_cardinality = data[lhs].nunique(dropna=False)
            rows.append(
                {
                    "lhs": lhs,
                    "rhs": rhs,
                    "ExactFD": exact_fd_score(data, lhs, rhs),
                    "QStrength": q_strength(data, lhs, rhs),
                    "TheilsU": theils_u(data, lhs, rhs),
                    "lhs_cardinality": lhs_cardinality,
                    "rhs_cardinality": data[rhs].nunique(dropna=False),
                    "avg_lhs_support": len(data) / max(lhs_cardinality, 1),
                }
            )
    return pd.DataFrame(rows)
