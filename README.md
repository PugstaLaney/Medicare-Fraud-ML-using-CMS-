# Medicare Fraud ML using CMS

Provider-level fraud, waste, and abuse (FWA) detection on public Medicare billing data.
Built as a working refresher on ML fundamentals for program-integrity analytics: peer-group
feature engineering, ranking metrics under extreme class imbalance, unsupervised anomaly
detection, and supervised scoring against real exclusion outcomes.

## Data

All sources are public and free.

| source | grain | rows | use |
|---|---|---|---|
| [CMS Medicare Physician & Other Practitioners, by Provider](https://data.cms.gov/provider-summary-by-type-of-service/medicare-physician-other-practitioners/medicare-physician-other-practitioners-by-provider) (2024) | one row per NPI | 1.30M | yearly totals, patient panel |
| [CMS Medicare Physician & Other Practitioners, by Provider and Service](https://data.cms.gov/provider-summary-by-type-of-service/medicare-physician-other-practitioners/medicare-physician-other-practitioners-by-provider-and-service) (2024) | NPI x HCPCS x place of service | 9.78M | billing mix |
| [OIG List of Excluded Individuals and Entities](https://oig.hhs.gov/exclusions/leie-database-supplement-downloads/) | one row per exclusion | 84K | weak labels |

Raw files and the DuckDB database are not in the repo. See `Docs/data_dictionary.md` for every column.

## Approach

1. **Load.** Three CSVs into DuckDB. Aggregation happens in SQL; pandas only sees results.
2. **Label.** A provider is a positive if they carry a section 1128(a) or 1128(b)(7) exclusion
   dated 2024 or later, meaning their 2024 billing happened before the conduct was caught.
   License-only exclusions are dropped as ambiguous. Result: 68 positives among 1.3M providers.
3. **Features.** Sixteen size-independent ratios (services per beneficiary, E&M upcoding share,
   same-day repeat billing, charge-to-allowed, payment per beneficiary per risk score, and so on),
   each paired with a robust z-score computed within provider specialty.
4. **Evaluate.** ROC AUC and precision@k implemented by hand and checked against scikit-learn,
   because at a 1-in-20,000 base rate the choice of metric is the whole problem.
5. **Model.** Isolation forest as the unsupervised baseline, gradient boosting on the labels.
6. **Retrieve.** A small retrieval layer over HCPCS descriptions and exclusion narratives so a
   flagged provider can be explained in plain language.

## Layout

```
analysis_notebooks/01_load_and_label   load, explore, build labels table
analysis_notebooks/02_features         build provider_features, rule-based flags
analysis_notebooks/03_evaluation       metrics by hand, checked against sklearn, baseline
src/metrics.py                         the metric functions later notebooks import
scripts/build_database.py        rebuild the DuckDB from raw CSVs
Docs/data_dictionary.md          every raw column, one line each
```

## Setup

Python 3.11. Install with `pip install -r requirements.txt`, download the three files above into
`data_raw/`, run `scripts/build_database.py`, then the notebooks in order.

## Early findings

After peer adjustment, excluded providers show more services per patient, a higher share of
high-level office visits, and payment less explained by patient risk. They also bill *closer* to
the Medicare fee schedule than their peers, not further from it. No single feature separates
them cleanly, which is the case for a model.
