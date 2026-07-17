import numpy as np
import pandas as pd

from acs_rule_gap.stability import permutation_test_edges, stable_dependency_candidates


def test_stability_selection_recovers_repeated_dependency():
    rng = np.random.default_rng(8)
    x = rng.integers(0, 4, 4_000)
    data = pd.DataFrame(
        {
            "x": x,
            "y": np.array(["a", "b", "c", "d"])[x],
            "noise": rng.integers(0, 3, 4_000),
        }
    )
    candidates = stable_dependency_candidates(
        data,
        ["x", "y", "noise"],
        resamples=8,
        sample_size=2_000,
        top_k=2,
        min_avg_lhs_support=10,
        seed=9,
    )
    edge = candidates[(candidates["lhs"] == "x") & (candidates["rhs"] == "y")]
    assert not edge.empty
    assert edge.iloc[0]["selection_frequency"] == 1.0

    tested = permutation_test_edges(data, edge.head(1), permutations=19, sample_size=2_000, seed=10)
    assert tested.iloc[0]["TheilsU_observed"] > tested.iloc[0]["null_95"]
    assert tested.iloc[0]["permutation_p_value"] <= 0.05
