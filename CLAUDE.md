# Medicare Fraud ML

Interview prep project for the GDIT Healthcare Data Scientist (Medicare/Medicaid program
integrity) role. Purpose: relearn ML fundamentals by building a provider-level fraud risk
model on real CMS data, then add a small retrieval layer. Portfolio artifact second.

## Environment
- venv: `C:\Users\palla\venvs\medicare-fraud\` (Python 3.11). Run with
  `C:\Users\palla\venvs\medicare-fraud\Scripts\python.exe`, never bare `python`.
- Jupyter kernel name: `medicare-fraud` (display "Python (medicare-fraud)").
- On Windows set `PYTHONIOENCODING=utf-8` when printing DuckDB tables from a script.

## Layout
- `data_raw/` and `database/` are **junctions to D:\Medicare_Fraud_ML\**. Big files stay
  off OneDrive and off the nearly full C: drive. Paths inside the project are unchanged.
- `scripts/build_database.py` rebuilds `database/medicare_fraud.duckdb` from the three CSVs.
- `analysis_notebooks/01_load_and_label.ipynb` loads, explores, and writes the `labels` table.
- `analysis_notebooks/02_features.ipynb` builds `provider_features` (incl. n_extreme, max_abs_z flags).
- `analysis_notebooks/03_evaluation.ipynb` hand-implements ROC/AUC/precision@k/AP, checks vs sklearn,
  scores the rule-based flags as the baseline.
- `analysis_notebooks/04_unsupervised_iforest.ipynb` isolation forest on the 16 z-scores + has_em.
  Writes `scores_iforest` (npi, iforest_score; higher = more anomalous).
- `analysis_notebooks/05_supervised_gbm.ipynb` HistGradientBoosting, stratified 5-fold OOF, permutation
  importance, isotonic calibration. Writes `scores_gbm` (npi, gbm_score, gbm_calibrated) and
  `database/models/gbm.joblib`.
- `analysis_notebooks/06_langchain_explain.ipynb` Chroma store of HCPCS descriptions at
  `database/chroma_hcpcs` (fastembed bge-small, CPU), retriever, LCEL chain to claude-opus-5 via
  langchain-anthropic, bind_tools agent loop. Needs `.env` with ANTHROPIC_API_KEY (gitignored).
- `src/metrics.py` is the fast version of those functions. Later notebooks `import metrics as M`
  after `sys.path.insert(0, <project>/src)`. `M.summarize(scores, y)` is the standard report.
- `Docs/data_dictionary.md` explains every raw column.

## Data (all 2024 unless noted)
- `provider` (1.30M rows): CMS Medicare Physician & Other Practitioners by Provider.
- `provider_service` (9.78M rows): same, by Provider and Service (NPI x HCPCS x place).
- `leie` (84K rows): OIG exclusion list, downloaded 2026-09-06. Only ~8.8K rows have a real NPI.
- `provider_features` (1.30M rows): built in 02_features.ipynb. Keys (npi, provider_type,
  state, entity_code, label, has_peer_group), 16 raw features, 16 robust peer z-scores
  (median/MAD within provider_type, min group 100, stddev fallback when MAD is 0).
  Service-derived features are null for ~89K providers with no provider_service rows;
  em_high_share is null for ~785K providers who bill no office visits.
- `labels`: built in 01_load_and_label.ipynb. label=1 if section 1128(a) or 1128b7 exclusion dated
  2024 or later; label=0 if never excluded; NULL (dropped) for license-type 1128b4 and
  pre-2024 exclusions.

## Baseline to beat (03_evaluation, 2026-09-07)
Best single column is max_abs_z: ROC AUC 0.604, AP 0.00012, precision@1000 = 0, precision@10000 = 0.0004
(4 of 68 positives). All single-column scores have zero positives in their top 1,000.

## Isolation forest result (04, 2026-09-09)
AUC 0.629, AP 0.00011, precision@1000 = 0, 2 of 68 in top 10K. Median positive percentile 68.
Clipping/log/rank transforms of z make no difference. Top of ranking = infusion pharmacies and
oncologists (legit drug-unit billing). Lesson: anomalous != fraudulent.

## Gradient boosting result (05, 2026-09-09)
OOF AUC 0.73 (folds 0.64 to 0.82, sd 0.09; a prior run gave 0.71, not bitwise reproducible),
AP 0.00017, precision@1000 = 0, 2 of 68 in top 10K, median positive percentile 82. provider_type categorical is the top importance; ablation without it
drops AUC to ~0.62, about one fold sd. class_weight=balanced makes raw probs ~0.9 at the top vs
observed 0; isotonic collapses them to ~0.0003. Same-year feature/label leakage noted; temporal
split with 2023 files is the next step.

## LangChain notes (06)
claude-opus-5 rejects `temperature` (400). Do not pass sampling params. fastembed downloads
bge-small on first run. Chroma build ~6 min first time, cached after.

## Conventions
- Unit of analysis is the provider (NPI), never a single claim row.
- Aggregate in DuckDB SQL, bring results into pandas.
- Hand-implement the evaluation metrics (pair-counting AUC, precision@k) before using sklearn.
- Absolute DB path in notebooks.
- No em dashes in any text.
