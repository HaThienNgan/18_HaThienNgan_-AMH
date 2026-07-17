"""Core methods for the ACSIncome business-rule-gap experiments."""

from .data import create_derived_variables, stratified_sample, stratified_train_test_split
from .drift import dependency_drift_score, leave_one_group_out_dds, theils_u_matrix
from .metrics import (
    cramers_v,
    exact_fd_score,
    normalized_mutual_information,
    pairwise_dependency_scores,
    q_strength,
    theils_u,
)
from .stability import permutation_test_edges, stable_dependency_candidates

__all__ = [
    "cramers_v",
    "create_derived_variables",
    "dependency_drift_score",
    "exact_fd_score",
    "leave_one_group_out_dds",
    "normalized_mutual_information",
    "pairwise_dependency_scores",
    "permutation_test_edges",
    "q_strength",
    "stable_dependency_candidates",
    "stratified_sample",
    "stratified_train_test_split",
    "theils_u",
    "theils_u_matrix",
]
