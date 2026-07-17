import numpy as np
import pandas as pd

from acs_rule_gap.metrics import (
    cramers_v,
    exact_fd_score,
    normalized_mutual_information,
    q_strength,
    theils_u,
)


def test_perfect_dependency_scores_one():
    data = pd.DataFrame(
        {
            "x": np.repeat(["a", "b", "c"], 20),
            "y": np.repeat([1, 2, 3], 20),
        }
    )
    assert exact_fd_score(data, "x", "y") == 1.0
    assert np.isclose(q_strength(data, "x", "y"), 1.0)
    assert np.isclose(theils_u(data, "x", "y"), 1.0)
    assert np.isclose(normalized_mutual_information(data, "x", "y"), 1.0)
    assert np.isclose(cramers_v(data, "x", "y"), 1.0)


def test_theils_u_uses_consistent_log_base():
    data = pd.DataFrame({"binary": [0, 0, 1, 1] * 100})
    data["copy"] = data["binary"]
    assert np.isclose(theils_u(data, "binary", "copy"), 1.0)


def test_independent_variables_have_low_association():
    rng = np.random.default_rng(42)
    data = pd.DataFrame(
        {
            "x": rng.integers(0, 4, 20_000),
            "y": rng.integers(0, 3, 20_000),
        }
    )
    assert theils_u(data, "x", "y") < 0.01
    assert normalized_mutual_information(data, "x", "y") < 0.01
    assert cramers_v(data, "x", "y") < 0.03
