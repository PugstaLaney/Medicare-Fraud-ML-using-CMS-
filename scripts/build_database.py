"""
Build the DuckDB database from the three raw CSVs.

Run from the project root:
    C:/Users/palla/venvs/medicare-fraud/Scripts/python.exe scripts/build_database.py

Creates three tables:
    provider          one row per NPI (2024 totals, demographics, chronic conditions)
    provider_service  one row per NPI x HCPCS code x place of service (2024)
    leie              OIG exclusion list, one row per exclusion

DuckDB reads the CSVs directly and infers types. The 3.2 GB file takes
a couple of minutes; nothing is loaded into Python memory.
"""
from pathlib import Path
import time
import duckdb

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data_raw"
DB = ROOT / "database" / "medicare_fraud.duckdb"

FILES = {
    "provider":         RAW / "MUP_PHY_R26_P05_V10_D24_Prov.csv",
    "provider_service": RAW / "PHY_R26_P05_V10_D24_Prov_Svc.csv",
    "leie":             RAW / "UPDATED.csv",
}


def build():
    for name, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(path)

    if DB.exists():
        DB.unlink()
    con = duckdb.connect(str(DB))

    for name, path in FILES.items():
        t0 = time.time()
        # all_varchar for LEIE: NPI and dates are zero-padded strings and
        # must not be parsed as integers (leading zeros, 00000000 dates).
        opts = ", all_varchar=true" if name == "leie" else ""
        con.execute(
            f"CREATE TABLE {name} AS "
            f"SELECT * FROM read_csv('{path.as_posix()}', header=true{opts})"
        )
        n = con.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
        print(f"{name:17s} {n:>12,} rows   {time.time() - t0:6.1f}s")

    # Indexes on the join keys.
    con.execute("CREATE INDEX idx_provider_npi ON provider(Rndrng_NPI)")
    con.execute("CREATE INDEX idx_psvc_npi ON provider_service(Rndrng_NPI)")
    con.execute("CREATE INDEX idx_leie_npi ON leie(NPI)")

    con.close()
    print(f"\nwrote {DB}  ({DB.stat().st_size / 1e9:.2f} GB)")


if __name__ == "__main__":
    build()
