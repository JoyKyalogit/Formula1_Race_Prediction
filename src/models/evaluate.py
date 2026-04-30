import argparse
from pathlib import Path
import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix
from src.utils.io_utils import save_json, read_df, ensure_dir


def evaluate_model(model, X, y):
    pred = model.predict(X)
    return {
        "accuracy": float(accuracy_score(y, pred)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y, pred).tolist(),
    }


def main(target: str = "is_top3", processed_dir: str = "data/processed", artifacts_dir: str = "artifacts", metrics_dir: str = "metrics"):
    holdout = read_df(Path(processed_dir) / f"holdout_{target}.parquet")

    y = holdout[target].astype(int)
    X = holdout.drop(columns=[target])

    out = ensure_dir(metrics_dir)
    results = {}

    for model_file in Path(artifacts_dir).glob(f"{target}_*.pkl"):
        model_name = model_file.stem.replace(f"{target}_", "")
        model = joblib.load(model_file)
        results[model_name] = evaluate_model(model, X, y)

    save_json(results, Path(out) / f"{target}_metrics.json")
    print(f"Saved metrics/{target}_metrics.json")
    print(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=str, default="is_top3", choices=["is_top3", "is_winner"])
    args = parser.parse_args()
    main(target=args.target)