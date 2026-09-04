# Formula 1 Race Predictor

**Live app:** [https://f1-race-predictor-t21v.onrender.com/](https://f1-race-predictor-t21v.onrender.com/)

An end-to-end ML product that predicts Formula 1 race outcomes (podium / race win) using historical results, qualifying data, and engineered driver form features — then serves those predictions through a FastAPI backend and interactive dashboard.

Built to demonstrate a full production-style workflow: **data → features → models → API → UI → cloud deploy**.

---

## Highlights

- End-to-end ML pipeline: ingestion, cleaning, leakage-aware features, training, evaluation
- FastAPI inference API with season/round selection
- Interactive dashboard for predictions and recent driver form
- Deployed on Render with model artifacts included in the repo

---

## Try it in 30 seconds

1. Open the live demo: [f1-race-predictor-t21v.onrender.com](https://f1-race-predictor-t21v.onrender.com/)
2. Go to the dashboard
3. Pick a **season**, **round**, and target (**Top 3** or **Win**)
4. Click **Predict Results** to see ranked driver probabilities

> Free Render hosting may sleep when idle — the first load can take ~30–60 seconds.

---

## What it does

| Capability | Detail |
| --- | --- |
| Predictions | Probability a driver finishes **top 3** or **wins** a selected race |
| Form insights | Recent average finish and points over the last 5 races |
| Data pipeline | Public F1 data → cleaned tables → feature matrix → trained models |
| Serving | REST API + home page + prediction dashboard |

---

## Tech stack

**ML / Data:** Python, pandas, scikit-learn, XGBoost, Parquet  
**API:** FastAPI, Uvicorn  
**Frontend:** HTML, CSS, JavaScript  
**Data source:** Jolpica (public Ergast-compatible F1 API)  
**Deploy:** Render (`render.yaml`)

---

## Architecture

```text
Jolpica API
    ↓
Ingestion → Cleaning → Feature engineering
    ↓
XGBoost models (top-3 / winner)
    ↓
FastAPI  →  Home + Dashboard UI
    ↓
Render (production)
```

**Training design (high level):**
- Source: historical race results + qualifying (typically 2018–2025)
- Split: train on seasons before 2025; hold out 2025+
- Features: grid, qualifying, rolling form, constructor form, track history, DNF trend
- Targets: `is_top3`, `is_winner`

No API keys are required for the baseline Jolpica pipeline.

---

## Repository layout

```text
app/           FastAPI service
frontend/      Home + prediction dashboard
src/           Ingestion, processing, features, training, evaluation
artifacts/     Trained model files (*.pkl)
data/processed Model table used for inference
config/        Paths and public API settings
render.yaml    Render deployment config
```

---

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.api:app --reload
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000).

Model artifacts are already in the repo for local/demo use. To rebuild from scratch:

```bash
python -m src.ingestion.ingest_jolpica --start-season 2018 --end-season 2025 --out-dir data/raw
python -m src.processing.clean_data
python -m src.features.build_features
python -m src.models.train --target is_top3
python -m src.models.train --target is_winner
```

---

## API snapshot

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Health check |
| `GET` | `/api/seasons` | List seasons |
| `GET` | `/api/rounds?season=YYYY` | List rounds |
| `GET` | `/api/driver-summary` | Recent driver form |
| `POST` | `/api/predict` | Ranked race probabilities |

```json
{ "season": 2024, "round": 5, "target": "is_top3" }
```

---

## Limitations 

- Predictions are **probabilities**, not guaranteed outcomes
- Focus is podium / win classification — not full finishing-order simulation
- Weather and detailed telemetry are not in the baseline feature set

---

## Next improvements

- Probability calibration
- Weather / session features
- One-command pipeline orchestration

---

