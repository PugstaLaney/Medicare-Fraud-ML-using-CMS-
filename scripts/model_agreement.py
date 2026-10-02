"""Which providers do the two models agree on?

Builds a set of NPIs in the top k under each model, then uses set operations to count the overlap.
Run from the project root:
    C:/Users/palla/venvs/medicare-fraud/Scripts/python.exe scripts/model_agreement.py
"""

from pathlib import Path
import duckdb

DB_PATH = Path(__file__).resolve().parents[1] / "database" / "medicare_fraud.duckdb"

TOP_K = 1000

connection = duckdb.connect(database=DB_PATH, read_only=True)

# Each query returns a list of one-element tuples like [(1003000126,), (1003000127,), ...]
# The comprehension unpacks each tuple and collects the NPIs into a set for fast membership testing.

top_by_boosting = {npi for (npi,) in connection.execute(
    f"SELECT npi FROM scores_gbm ORDER BY gbm_score DESC LIMIT {TOP_K}").fetchall()}
    
top_by_anomaly = {npi for (npi,) in connection.execute(
    f"SELECT npi FROM scores_iforest ORDER BY iforest_score DESC LIMIT {TOP_K}").fetchall()}

known_positives = {npi for (npi,) in connection.execute(
    "SELECT npi FROM labels WHERE label = 1").fetchall()}



flagged_by_both = top_by_boosting & top_by_anomaly

flagged_by_either = top_by_boosting | top_by_anomaly

only_boosting = top_by_boosting - top_by_anomaly

only_anomaly = top_by_anomaly - top_by_boosting

print(f"top {TOP_K} under each model")
print(f"  flagged by both   : {len(flagged_by_both):5d}")
print(f"  flagged by either : {len(flagged_by_either):5d}")
print(f"  only boosting     : {len(only_boosting):5d}")
print(f"  only anomaly      : {len(only_anomaly):5d}")


# A tuple as a dictionary key: (model name, k) -> how many known positives landed in that set.
positives_caught = {
    ("boosting", TOP_K): len(top_by_boosting & known_positives),
    ("anomaly", TOP_K): len(top_by_anomaly & known_positives),
    ("both", TOP_K): len(flagged_by_both & known_positives),
}
print(f"\nknown positives caught, of {len(known_positives)}:")
for (model_name, k), count in positives_caught.items():
    print(f"  {model_name:9s} top {k}: {count}")