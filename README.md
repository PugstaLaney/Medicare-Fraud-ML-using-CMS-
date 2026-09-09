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
5. **Model.** Isolation forest as the unsupervised baseline, then gradient boosting on the
   labels with stratified 5-fold cross-validation and isotonic calibration.
6. **Explain.** A LangChain retrieval layer over HCPCS code descriptions (Chroma, fastembed) and
   an LCEL chain that merges database facts with retrieved context so Claude can brief an
   investigator on a flagged provider. Plus a small tool-calling agent.

## Results

Out-of-fold, all 1.3M providers, 68 known positives.

| model | ROC AUC | positives in top 1,000 | positives in top 10,000 | median percentile of positives |
|---|---|---|---|---|
| best single rule (max peer z-score) | 0.60 | 0 | 4 | 60 |
| isolation forest, unsupervised | 0.63 | 0 | 2 | 68 |
| gradient boosting, 5-fold OOF | 0.73 (fold sd 0.09) | 0 | 2 | 82 |

Each step ranks the population better. None builds a short investigation queue. The most
anomalous providers in Medicare are legitimate high-volume drug billers; the known fraud sits
modestly off-normal on several features at once. The public files carry no claim dates,
diagnoses, or beneficiary detail, which is where the next order of magnitude would come from.

## Layout

```
analysis_notebooks/01_load_and_label   load, explore, build labels table
analysis_notebooks/02_features         build provider_features, rule-based flags
analysis_notebooks/03_evaluation       metrics by hand, checked against sklearn, baseline
analysis_notebooks/04_unsupervised     isolation forest, scored against labels
analysis_notebooks/05_supervised       gradient boosting, stratified 5-fold, calibration
analysis_notebooks/06_langchain        Chroma vector store, retriever, LCEL chain, tool agent
src/metrics.py                         the metric functions later notebooks import
scripts/build_database.py        rebuild the DuckDB from raw CSVs
Docs/data_dictionary.md          every raw column, one line each
```

## Setup

Python 3.11. Install with `pip install -r requirements.txt`, download the three files above into
`data_raw/`, run `scripts/build_database.py`, then the notebooks in order. Notebook 06 needs an
`ANTHROPIC_API_KEY` in a `.env` file at the project root; without one it prints the prompts
it would have sent.

## Early findings

After peer adjustment, excluded providers show more services per patient, a higher share of
high-level office visits, and payment less explained by patient risk. They also bill *closer* to
the Medicare fee schedule than their peers, not further from it. No single feature separates
them cleanly, which is the case for a model.

An isolation forest on the peer-adjusted features ranks known-fraud providers above the
median but puts none in its top 1,000. The most anomalous providers in Medicare are
legitimate high-volume drug billers. Anomalous is not fraudulent, and unsupervised detection
alone does not find this kind of fraud.
