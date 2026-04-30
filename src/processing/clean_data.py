import pandas as pd
from pathlib import Path
from src.utils.io_utils import read_df, save_df, ensure_dir


def time_to_ms(series: pd.Series) -> pd.Series:
    # Handles strings like '1:23.456'
    td = pd.to_timedelta(series, errors="coerce")
    return td.dt.total_seconds() * 1000


def main(raw_dir: str = "data/raw", processed_dir: str = "data/processed"):
    raw = Path(raw_dir)
    out = ensure_dir(processed_dir)

    results_files = sorted(raw.glob("jolpica_results_*.parquet"))
    quali_files = sorted(raw.glob("jolpica_qualifying_*.parquet"))

    if not results_files:
        raise FileNotFoundError("No Jolpica results file found. Run ingest_jolpica.py first.")

    results = read_df(results_files[-1])
    quali = read_df(quali_files[-1]) if quali_files else pd.DataFrame()

    # Deduplicate core labels
    results = results.drop_duplicates(subset=["season", "round", "driver_id"])

    # Merge qualifying
    if not quali.empty:
        model_df = results.merge(quali[["season", "round", "driver_id", "qualifying_position"]],
                                 on=["season", "round", "driver_id"], how="left")
    else:
        model_df = results.copy()
        model_df["qualifying_position"] = None

    # Type fixes
    for col in ["grid", "finish_position", "points", "qualifying_position"]:
        model_df[col] = pd.to_numeric(model_df[col], errors="coerce")

    # Missing value handling
    model_df["qualifying_position"] = model_df["qualifying_position"].fillna(model_df["grid"])
    model_df["qualifying_position"] = model_df["qualifying_position"].fillna(model_df["qualifying_position"].median())

    model_df["constructor_name"] = model_df["constructor_name"].fillna("Unknown")
    model_df["status"] = model_df["status"].fillna("Unknown")

    # Targets
    model_df["is_top3"] = (model_df["finish_position"] <= 3).astype(int)
    model_df["is_winner"] = (model_df["finish_position"] == 1).astype(int)

    save_df(model_df, Path(out) / "model_base.parquet")
    print("Saved data/processed/model_base.parquet")


if __name__ == "__main__":
    main()