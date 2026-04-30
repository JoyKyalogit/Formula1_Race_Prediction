from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="F1 Race Predictor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_PATH = Path("data/processed/model_table.parquet")
FEATURES_NUM = [
    "grid",
    "qualifying_position",
    "avg_finish_last5",
    "consistency_std_last5",
    "driver_points_last5",
    "constructor_points_last5",
    "track_avg_finish_hist",
    "dnf_last5",
]
FEATURES_CAT = ["constructor_name", "circuit_id"]
MODEL_FEATURES = FEATURES_NUM + FEATURES_CAT


def load_df() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise HTTPException(status_code=404, detail="No processed data found. Run pipeline first.")
    return pd.read_parquet(DATA_PATH)


def df_to_json_rows(df: pd.DataFrame):
    # FastAPI JSON responses fail on NaN/inf; normalize to None.
    safe = df.copy().replace([float("inf"), float("-inf")], pd.NA)
    safe = safe.where(pd.notnull(safe), None)
    return safe.to_dict(orient="records")


class PredictRequest(BaseModel):
    season: int
    round: int
    target: Literal["is_top3", "is_winner"]


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/seasons")
def get_seasons():
    df = load_df()
    seasons = sorted(df["season"].dropna().unique().tolist())
    return {"seasons": [int(s) for s in seasons]}


@app.get("/api/rounds")
def get_rounds(season: int):
    df = load_df()
    rounds = sorted(df[df["season"] == season]["round"].dropna().unique().tolist())
    return {"rounds": [int(r) for r in rounds]}


@app.get("/api/driver-summary")
def get_driver_summary(limit: int = 20, season: int | None = None, round: int | None = None):
    df = load_df()
    if season is not None:
        df = df[df["season"] == season]
        if round is not None:
            df = df[df["round"] <= round]

    if df.empty:
        return {"rows": []}

    summary = (
        df.sort_values(["season", "round"])
        .groupby("driver_name", as_index=False)
        .tail(5)
        .groupby("driver_name", as_index=False)
        .agg(
            avg_finish_last5=("finish_position", "mean"),
            points_last5=("points", "sum"),
        )
        .sort_values("points_last5", ascending=False)
        .head(limit)
    )
    return {"rows": df_to_json_rows(summary)}


@app.post("/api/predict")
def predict(req: PredictRequest):
    try:
        df = load_df()
        race_df = df[(df["season"] == req.season) & (df["round"] == req.round)].copy()

        if race_df.empty:
            raise HTTPException(status_code=404, detail="No race rows found for selected season/round.")

        model_name = "xgb"
        model_path = Path("artifacts") / f"{req.target}_{model_name}.pkl"
        if not model_path.exists():
            raise HTTPException(status_code=404, detail=f"Model not found: {model_path}")

        model = joblib.load(model_path)
        # Align inference features with training schema.
        x = race_df.reindex(columns=MODEL_FEATURES)
        probs = model.predict_proba(x)[:, 1]
        race_df["pred_prob"] = probs

        show = race_df[
            ["driver_name", "constructor_name", "grid", "qualifying_position", "pred_prob"]
        ].sort_values("pred_prob", ascending=False).head(10)

        return {"rows": df_to_json_rows(show)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed [{type(exc).__name__}]: {repr(exc)}",
        ) from exc


# Mount static frontend last so /api routes are matched first.
if Path("frontend").exists():
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")