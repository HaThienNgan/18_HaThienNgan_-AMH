import pandas as pd

from acs_rule_gap.data import create_derived_variables, stratified_sample


def test_stratified_sample_has_exact_size_and_no_duplicate_source_rows():
    data = pd.DataFrame(
        {
            "row_id": range(200),
            "state": ["A"] * 100 + ["B"] * 100,
            "label": [0, 1] * 100,
        }
    )
    sampled = stratified_sample(data, 80, ["state", "label"], seed=7)
    assert len(sampled) == 80
    assert sampled["row_id"].nunique() == 80
    assert set(sampled.groupby(["state", "label"]).size()) == {20}


def test_derived_variables_are_explicit_synthetic_fixtures():
    data = pd.DataFrame(
        {
            "AGEP": [17, 30, 70],
            "SCHL": [10, 18, 22],
            "MAR": [1, 2, 5],
            "WKHP": [10, 40, 55],
            "SEX": [1, 2, 1],
            "RELP": [0, 1, 2],
            "COW": [1, 2, 3],
            "income_label": [0, 1, 0],
        }
    )
    result = create_derived_variables(data)
    assert result["age_group"].tolist() == ["Under18", "WorkingAge", "Senior"]
    assert result["fulltime_status"].tolist() == ["NonFulltime", "Fulltime", "Fulltime"]
