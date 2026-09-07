"""
Ranking metrics for the fraud model, implemented by hand.

These are the same functions built step by step in analysis_notebooks/03_evaluation.ipynb.
Later notebooks import from here so every model is scored the same way.
Each one is checked against scikit-learn in the notebook.

Conventions: `scores` is a 1-D array of model outputs where higher means more suspicious.
`y` is a 1-D array of 0/1 labels. Both are the same length. NaN scores are not allowed;
fill them before calling.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def confusion_at(scores, y, threshold):
    """Counts of TP, FP, FN, TN when everything at or above `threshold` is flagged."""
    scores = np.asarray(scores, dtype=float)
    y = np.asarray(y, dtype=int)
    flagged = scores >= threshold
    tp = int(np.sum(flagged & (y == 1)))
    fp = int(np.sum(flagged & (y == 0)))
    fn = int(np.sum(~flagged & (y == 1)))
    tn = int(np.sum(~flagged & (y == 0)))
    return {"TP": tp, "FP": fp, "FN": fn, "TN": tn}


def roc_points(scores, y):
    """
    Walk the threshold from strictest to loosest and record (FPR, TPR) at each step.
    Returns three arrays: fpr, tpr, thresholds. Starts at (0, 0) and ends at (1, 1).
    Ties in score are handled by moving the threshold to each distinct score value.
    """
    scores = np.asarray(scores, dtype=float)
    y = np.asarray(y, dtype=int)
    n_pos = int(np.sum(y == 1))
    n_neg = int(np.sum(y == 0))

    order = np.argsort(-scores, kind="stable")      # highest score first
    s_sorted = scores[order]
    y_sorted = y[order]

    # cumulative counts of positives and negatives flagged as the threshold drops
    tp_cum = np.cumsum(y_sorted == 1)
    fp_cum = np.cumsum(y_sorted == 0)

    # only keep the last index of each distinct score (that is where the threshold "lands")
    distinct = np.r_[s_sorted[1:] != s_sorted[:-1], True]
    tpr = np.r_[0.0, tp_cum[distinct] / n_pos]
    fpr = np.r_[0.0, fp_cum[distinct] / n_neg]
    thresholds = np.r_[np.inf, s_sorted[distinct]]
    return fpr, tpr, thresholds


def auc_trapezoid(fpr, tpr):
    """Area under a curve given as x (fpr) and y (tpr) arrays, by the trapezoid rule."""
    fpr = np.asarray(fpr, dtype=float)
    tpr = np.asarray(tpr, dtype=float)
    return float(np.sum((fpr[1:] - fpr[:-1]) * (tpr[1:] + tpr[:-1]) / 2.0))


def auc_pairs(scores, y):
    """
    AUC as a probability: pick a random positive and a random negative, how often does the
    positive score higher? Ties count as half. This is the Mann-Whitney U statistic rescaled.
    Uses ranks so it runs in O(n log n) even on a million rows.
    """
    scores = np.asarray(scores, dtype=float)
    y = np.asarray(y, dtype=int)
    n_pos = int(np.sum(y == 1))
    n_neg = int(np.sum(y == 0))

    # average ranks, so tied scores share a rank (that is what gives ties half credit)
    ranks = pd.Series(scores).rank(method="average").to_numpy()

    rank_sum_pos = float(np.sum(ranks[y == 1]))
    u = rank_sum_pos - n_pos * (n_pos + 1) / 2.0     # pairs won by positives (ties = 0.5)
    return u / (n_pos * n_neg)


def precision_at_k(scores, y, k):
    """Of the k highest-scoring rows, what fraction are positives?"""
    scores = np.asarray(scores, dtype=float)
    y = np.asarray(y, dtype=int)
    top = np.argsort(-scores, kind="stable")[:k]
    return float(np.mean(y[top]))


def recall_at_k(scores, y, k):
    """Of all positives, what fraction land in the k highest-scoring rows?"""
    scores = np.asarray(scores, dtype=float)
    y = np.asarray(y, dtype=int)
    top = np.argsort(-scores, kind="stable")[:k]
    return float(np.sum(y[top]) / np.sum(y == 1))


def pr_points(scores, y):
    """
    Precision and recall at every distinct threshold, strictest first.
    Returns precision, recall, thresholds. Unlike ROC, this does not start at a fixed point:
    precision at the strictest threshold depends on whether the top-scored row is a positive.
    """
    scores = np.asarray(scores, dtype=float)
    y = np.asarray(y, dtype=int)
    n_pos = int(np.sum(y == 1))

    order = np.argsort(-scores, kind="stable")
    s_sorted = scores[order]
    y_sorted = y[order]
    tp_cum = np.cumsum(y_sorted == 1)
    n_flagged = np.arange(1, len(scores) + 1)

    distinct = np.r_[s_sorted[1:] != s_sorted[:-1], True]
    precision = tp_cum[distinct] / n_flagged[distinct]
    recall = tp_cum[distinct] / n_pos
    thresholds = s_sorted[distinct]
    return precision, recall, thresholds


def average_precision(scores, y):
    """
    Area under the precision-recall curve, computed the way scikit-learn does it:
    the sum over thresholds of (gain in recall) x (precision at that threshold).
    A random model scores roughly the positive rate. A perfect model scores 1.0.
    """
    precision, recall, _ = pr_points(scores, y)
    recall_prev = np.r_[0.0, recall[:-1]]
    return float(np.sum((recall - recall_prev) * precision))


def summarize(scores, y, ks=(100, 1000, 10000)):
    """One-row dict of the metrics every model in this project reports."""
    out = {
        "roc_auc": auc_pairs(scores, y),
        "avg_precision": average_precision(scores, y),
    }
    for k in ks:
        if k <= len(scores):
            out[f"precision@{k}"] = precision_at_k(scores, y, k)
            out[f"recall@{k}"] = recall_at_k(scores, y, k)
    return out
