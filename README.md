# Formula 1 Race Prediction Project

An end-to-end machine learning project that predicts race outcomes in Formula 1 using historical race data, qualifying data, and engineered form features.

The app provides:
- A data pipeline from ingestion to model-ready tables
- Binary prediction models for `top 3 finish` and `race winner`
- A FastAPI backend for inference
- A frontend dashboard for interactive predictions and driver form insights

## Overview

- Helps compare drivers before a race using data-driven probabilities
- Turns raw motorsport data into practical race intelligence
- Demonstrates a full production-style ML workflow:
  - data ingestion
  - cleaning and feature engineering
  - model training and evaluation
  - API serving and UI delivery
- Easy to extend with additional sources (OpenF1/FastF1) and features

## Project Structure

`app/`
- `api.py`: FastAPI backend with endpoints for seasons, rounds, driver summary, and predictions

`src/ingestion/`
- `ingest_jolpica.py`: Pulls race results and qualifying from Jolpica (Ergast mirror)
- `ingest_openf1.py`: Pulls meetings, sessions, and laps from OpenF1
- `ingest_fastf1.py`: Pulls lap and weather data via FastF1

`src/processing/`
- `clean_data.py`: Merges/cleans ingested data and creates modeling targets

`src/features/`
- `build_features.py`: Creates historical and rolling-performance features

`src/models/`
- `train.py`: Trains XGBoost pipelines and saves model artifacts
- `evaluate.py`: Evaluates holdout data and writes metrics

`frontend/`
- `index.html`, `styles.css`, `app.js`: Dashboard UI

`data/`
- `raw/`: downloaded source datasets
- `processed/`: cleaned and feature-engineered datasets

`artifacts/`
- Saved model files (`*.pkl`)

`metrics/`
- Evaluation JSON outputs

`config/`
- `settings.yaml`: base settings and paths

## How It Works (End-to-End)

### 1) Data Ingestion

The pipeline starts by collecting historical F1 data:

- `ingest_jolpica.py`
  - Pulls race results (`grid`, `finish_position`, `points`, status, etc.)
  - Pulls qualifying positions
  - Saves parquet files into `data/raw/`

- Optional enrichment:
  - `ingest_openf1.py` for sessions/laps
  - `ingest_fastf1.py` for detailed laps/weather

### 2) Data Cleaning and Modeling Base Table

`clean_data.py`:
- Loads latest Jolpica result and qualifying parquet files
- Deduplicates race-driver rows
- Merges qualifying onto results
- Converts key columns to numeric types
- Handles missing values
- Builds target columns:
  - `is_top3` (1 if finish position <= 3)
  - `is_winner` (1 if finish position == 1)
- Saves `data/processed/model_base.parquet`

### 3) Feature Engineering

`build_features.py` creates historical features using past-only windows (no leakage):

- `avg_finish_last5`
- `consistency_std_last5`
- `driver_points_last5`
- `constructor_points_last5`
- `track_avg_finish_hist`
- `dnf_last5`

Then saves `data/processed/model_table.parquet`.

### 4) Model Training

`train.py`:
- Uses a time-aware split:
  - train: seasons `< 2025`
  - holdout: seasons `>= 2025`
- Features include:
  - Numeric: grid, qualifying, rolling form, constructor form, track history, DNF trend
  - Categorical: constructor, circuit
- Builds a preprocessing + model pipeline:
  - numeric imputation + scaling
  - categorical imputation + one-hot encoding
  - XGBoost classifier
- Saves:
  - model artifact in `artifacts/` (`is_top3_xgb.pkl`, `is_winner_xgb.pkl`)
  - holdout dataset for evaluation

### 5) Evaluation

`evaluate.py`:
- Loads holdout data
- Scores each saved model for a target
- Writes metrics to `metrics/{target}_metrics.json`:
  - accuracy
  - precision
  - recall
  - confusion matrix

### 6) API Inference

`app/api.py` serves:
- `GET /api/health`
- `GET /api/seasons`
- `GET /api/rounds?season=YYYY`
- `GET /api/driver-summary?season=YYYY&round=R`
- `POST /api/predict`

Prediction flow:
- Filters selected season and round
- Loads target-specific model artifact
- Aligns inference features with training schema
- Runs `predict_proba` and returns top drivers by predicted probability

### 7) Frontend Dashboard

The frontend:
- Loads available seasons and rounds from API
- Shows recent driver form for selected season and round
- Sends prediction requests based on selected target
- Displays ranked probabilities in a prediction table

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows PowerShell

pip install -r requirements.txt
```

## Typical Run Workflow

### A) Build datasets

```bash
python -m src.ingestion.ingest_jolpica --start-season 2018 --end-season 2025 --out-dir data/raw
python -m src.processing.clean_data
python -m src.features.build_features
```

### B) Train models

```bash
python -m src.models.train --target is_top3
python -m src.models.train --target is_winner
```

### C) Evaluate models

```bash
python -m src.models.evaluate --target is_top3
python -m src.models.evaluate --target is_winner
```

### D) Start API + UI

```bash
uvicorn app.api:app --reload
```

Then open the local app URL printed by Uvicorn (usually `http://127.0.0.1:8000`).

## Notes and Limitations

- Predictions are probabilistic estimates, not guaranteed outcomes.
- Performance depends on data freshness and feature quality.
- Current model is classification-focused (`top3` / `winner`), not full finishing order simulation.
- Optional OpenF1/FastF1 ingestion is included for future enrichment but not required for the current baseline pipeline.

## Future Improvements

- Add uncertainty calibration and probability reliability plots
- Include weather/session features in final model table
- Add circuit-type or team strategy features
- Automate end-to-end pipeline with one orchestrated command
