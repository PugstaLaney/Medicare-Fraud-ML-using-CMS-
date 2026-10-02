import sys
from pathlib import Path
import numpy as np
from sklearn import metrics as sklearn_metrics

#Make src/ importable from the tests folder
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import metrics

#The ten-provider example from notebook 03. Four fraud, six clean score in order.
toy_scores = np.array([0.95, 0.90, 0.85, 0.80, 0.70, 0.60, 0.55, 0.40, 0.30, 0.10])
toy_labels = np.array([1,    1,    0,    1,    0,    0,    1,    0,    0,    0])


def test_auc_matches_sklearn_on_toy_example():
    hand_written_auc = metrics.auc_pairs(toy_scores, toy_labels)
    library_auc = sklearn_metrics.roc_auc_score(toy_labels, toy_scores)
    assert abs(hand_written_auc - library_auc) < 1e-9

def test_auc_is_twenty_of_twenty_four_pairs():
    # 4 fraud x 6 clean = 24 pairs, so AUC should be 20/24 = 0.8333333
    assert abs(metrics.auc_pairs(toy_scores, toy_labels) - 20/24) < 1e-9

def test_precision_at_k_counts_positives_in_the_top_k():
     # Top 3 by score are 0.95, 0.90, 0.85 with labels 1, 1, 0: two of three are fraud.
    assert metrics.precision_at_k(toy_scores, toy_labels, 3) == 2 / 3

def test_perfect_ranking_gives_auc_of_one():
    perfect_scores = np.array([0.9, 0.8, 0.2, 0.1])
    perfect_labels = np.array([1, 1, 0, 0])
    assert metrics.auc_pairs(perfect_scores, perfect_labels) == 1.0