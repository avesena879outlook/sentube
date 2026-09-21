"""Scikit-learn compatible mRMR feature selector for sparse text features."""

from __future__ import annotations

import numpy as np
from scipy import sparse
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_selection import mutual_info_classif
from sklearn.utils.validation import check_array, check_is_fitted


class MRMRSelector(BaseEstimator, TransformerMixin):
    """Select features using mutual-information difference (MID).

    Relevance is mutual information between binary term occurrence and the
    target. Redundancy is the mean mutual information between a candidate and
    the already selected terms. TF-IDF values are binarized only while scores
    are calculated; ``transform`` returns the original TF-IDF values.
    """

    def __init__(self, k: int = 100, random_state: int | None = 42):
        self.k = k
        self.random_state = random_state

    @staticmethod
    def _binary_mutual_information_all(
        features: sparse.csc_matrix, selected_column: sparse.csc_matrix
    ) -> np.ndarray:
        n_samples = features.shape[0]
        feature_ones = np.asarray(features.sum(axis=0)).ravel()
        selected_ones = float(selected_column.sum())
        both_one = np.asarray(features.T @ selected_column).ravel()

        counts = (
            both_one,
            feature_ones - both_one,
            selected_ones - both_one,
            n_samples - feature_ones - selected_ones + both_one,
        )
        row_totals = (selected_ones, n_samples - selected_ones)
        col_totals = (feature_ones, n_samples - feature_ones)
        mi = np.zeros(features.shape[1], dtype=float)

        for index, joint_count in enumerate(counts):
            row_total = row_totals[0 if index in (0, 2) else 1]
            col_total = col_totals[0 if index in (0, 1) else 1]
            valid = joint_count > 0
            probability = joint_count[valid] / n_samples
            expected = (row_total / n_samples) * (col_total[valid] / n_samples)
            mi[valid] += probability * np.log(probability / expected)

        return mi

    def fit(self, X, y):
        X = check_array(X, accept_sparse=("csr", "csc"), dtype=None)
        if self.k <= 0:
            raise ValueError("k must be greater than zero")

        feature_count = X.shape[1]
        select_count = min(int(self.k), feature_count)
        binary = sparse.csc_matrix(X)
        binary.data = np.ones_like(binary.data, dtype=np.uint8)
        binary.eliminate_zeros()

        relevance = mutual_info_classif(
            binary,
            y,
            discrete_features=True,
            random_state=self.random_state,
        )
        selected = [int(np.argmax(relevance))]
        available = np.ones(feature_count, dtype=bool)
        available[selected[0]] = False
        redundancy_sum = np.zeros(feature_count, dtype=float)

        while len(selected) < select_count:
            latest = binary[:, selected[-1]]
            redundancy_sum += self._binary_mutual_information_all(binary, latest)
            score = relevance - (redundancy_sum / len(selected))
            score[~available] = -np.inf
            next_feature = int(np.argmax(score))
            selected.append(next_feature)
            available[next_feature] = False

        self.selected_indices_ = np.asarray(selected, dtype=int)
        self.relevance_scores_ = relevance
        self.n_features_in_ = feature_count
        return self

    def transform(self, X):
        check_is_fitted(self, "selected_indices_")
        X = check_array(X, accept_sparse=("csr", "csc"), dtype=None)
        return X[:, self.selected_indices_]

    def get_support(self, indices: bool = False):
        check_is_fitted(self, "selected_indices_")
        if indices:
            return self.selected_indices_.copy()
        mask = np.zeros(self.n_features_in_, dtype=bool)
        mask[self.selected_indices_] = True
        return mask

