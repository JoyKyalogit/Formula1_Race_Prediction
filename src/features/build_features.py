import pandas as pd
from pathlib import Path
from src.utils.io_utils import read_df, save_df, ensure_dir


def main(processed_dir: str = "data/processed"):
    p = Path(processed_dir)
    df = read_df(p / "model_base.parquet").copy()

    df = df.sort_values(["driver_id", "season", "round"]).reset_index(drop=True)

    # Rolling form (past only)
    df["avg_finish_last5"] = (
        df.groupby("driver_id")["finish_position"]
          .transform(lambda s: s.shift(1).rolling(5, min_periods=1).mean())
    )

    # Consistency (std; lower is better)
    df["consistency_std_last5"] = (
        df.groupby("driver_id")["finish_position"]
          .transform(lambda s: s.shift(1).rolling(5, min_periods=2).std())
    )

    # Driver recent points
    df["driver_points_last5"] = (
        df.groupby("driver_id")["points"]
          .transform(lambda s: s.shift(1).rolling(5, min_periods=1).sum())
    )

    # Constructor team form
    df = df.sort_values(["constructor_id", "season", "round"])
    df["constructor_points_last5"] = (
        df.groupby("constructor_id")["points"]
          .transform(lambda s: s.shift(1).rolling(5, min_periods=1).sum())
    )

    # Track-specific history
    df = df.sort_values(["driver_id", "circuit_id", "season", "round"])
    df["track_avg_finish_hist"] = (
        df.groupby(["driver_id", "circuit_id"])["finish_position"]
          .transform(lambda s: s.shift(1).expanding(min_periods=1).mean())
    )

    # DNF trend (status-based approximation)
    dnf_flag = ~df["status"].astype(str).str.contains("Finished|\\+", case=False, na=False)
    df["dnf_flag"] = dnf_flag.astype(int)
    df["dnf_last5"] = (
        df.groupby("driver_id")["dnf_flag"]
          .transform(lambda s: s.shift(1).rolling(5, min_periods=1).mean())
    )

    # Fill engineered nulls
    feature_cols = [
        "avg_finish_last5", "consistency_std_last5", "driver_points_last5",
        "constructor_points_last5", "track_avg_finish_hist", "dnf_last5"
    ]
    for c in feature_cols:
        df[c] = df[c].fillna(df[c].median())

    save_df(df, p / "model_table.parquet")
    print("Saved data/processed/model_table.parquet")


if __name__ == "__main__":
    main()