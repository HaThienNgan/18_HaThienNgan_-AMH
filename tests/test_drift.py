import numpy as np
import pandas as pd

from acs_rule_gap.drift import (
    dependency_drift_score,
    leave_one_group_out_dds,
    paired_dependency_drift,
    theils_u_matrix,
)


def test_identical_dependency_matrices_have_zero_dds():
    data = pd.DataFrame({"x": [0, 0, 1, 1] * 20, "y": ["a", "a", "b", "b"] * 20})
    matrix = theils_u_matrix(data, ["x", "y"])
    assert dependency_drift_score(matrix, matrix) == 0.0
    assert paired_dependency_drift(data, data.copy(), ["x", "y"], seed=3) == 0.0


def test_leave_one_group_out_excludes_group_column():
    pattern = pd.DataFrame({"x": [0, 0, 1, 1] * 50, "y": ["a", "a", "b", "b"] * 50})
    data = pd.concat(
        [pattern.assign(state="A"), pattern.assign(state="B"), pattern.assign(state="C")],
        ignore_index=True,
    )
    result = leave_one_group_out_dds(
        data,
        group_col="state",
        columns=["x", "y", "state"],
        sample_size=150,
        permutation_reps=9,
        seed=4,
    )
    assert np.allclose(result["DDS_vs_other_groups"], 0.0)


def test_dds_detects_broken_dependency():
    clean = pd.DataFrame({"x": np.repeat([0, 1], 100), "y": np.repeat(["a", "b"], 100)})
    changed = clean.copy()
    changed.loc[::2, "y"] = "other"
    assert paired_dependency_drift(clean, changed, ["x", "y"], seed=2) > 0.1
