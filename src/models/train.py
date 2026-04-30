import argparse
from pathlib import Path
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from xgboost import XGBClassifier
from src.utils.io_utils import read_df, ensure_dir


def main(target: str = "is_top3", processed_dir: str = "data/processed", artifacts_dir: str = "artifacts"):
    df = read_df(Path(processed_dir) / "model_table.parquet")

    # Time-aware split: train < 2025, test >= 2025
    train_df = df[df["season"] < 2025].copy()
    test_df = df[df["season"] >= 2025].copy()

    features_num = [
        "grid", "qualifying_position", "avg_finish_last5", "consistency_std_last5",
        "driver_points_last5", "constructor_points_last5", "track_avg_finish_hist", "dnf_last5"
    ]
    features_cat = ["constructor_name", "circuit_id"]

    use_cols = features_num + features_cat + [target]
    train_df = train_df[use_cols].dropna(subset=[target])
    test_df = test_df[use_cols].dropna(subset=[target])

    X_train, y_train = train_df.drop(columns=[target]), train_df[target].astype(int)

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler())
            ]), features_num),
            ("cat", Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("ohe", OneHotEncoder(handle_unknown="ignore"))
            ]), features_cat),
        ]
    )

    model = XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        eval_metric="logloss",
        random_state=42
    )

    pipe = Pipeline([("prep", preprocessor), ("model", model)])
    pipe.fit(X_train, y_train)

    out = ensure_dir(artifacts_dir)
    model_name = "xgb"
    output_path = Path(out) / f"{target}_{model_name}.pkl"
    joblib.dump(pipe, output_path)
    print(f"Saved {output_path}")

    # Save holdout for evaluate.py
    test_df.to_parquet(Path(processed_dir) / f"holdout_{target}.parquet", index=False)
    print(f"Saved holdout_{target}.parquet")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=str, default="is_top3", choices=["is_top3", "is_winner"])
    args = parser.parse_args()
    main(target=args.target)