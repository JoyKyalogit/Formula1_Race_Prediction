import argparse
import requests
import pandas as pd
from pathlib import Path
from src.utils.io_utils import ensure_dir, save_df

BASE_URL = "https://api.jolpi.ca/ergast/f1"


def fetch_json(url: str) -> dict:
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.json()


def get_results_for_season(season: int) -> pd.DataFrame:
    url = f"{BASE_URL}/{season}/results.json?limit=2000"
    data = fetch_json(url)
    races = data["MRData"]["RaceTable"]["Races"]

    rows = []
    for race in races:
        season_ = int(race["season"])
        round_ = int(race["round"])
        race_name = race["raceName"]
        circuit_id = race["Circuit"]["circuitId"]
        race_date = race["date"]

        for res in race.get("Results", []):
            driver = res["Driver"]
            constructor = res["Constructor"]

            rows.append({
                "season": season_,
                "round": round_,
                "race_name": race_name,
                "circuit_id": circuit_id,
                "race_date": race_date,
                "driver_id": driver["driverId"],
                "driver_code": driver.get("code"),
                "driver_number": driver.get("permanentNumber"),
                "driver_name": f'{driver.get("givenName", "")} {driver.get("familyName", "")}'.strip(),
                "constructor_id": constructor["constructorId"],
                "constructor_name": constructor["name"],
                "grid": pd.to_numeric(res.get("grid"), errors="coerce"),
                "finish_position": pd.to_numeric(res.get("position"), errors="coerce"),
                "points": pd.to_numeric(res.get("points"), errors="coerce"),
                "status": res.get("status"),
            })

    return pd.DataFrame(rows)


def get_qualifying_for_season(season: int) -> pd.DataFrame:
    url = f"{BASE_URL}/{season}/qualifying.json?limit=2000"
    data = fetch_json(url)
    races = data["MRData"]["RaceTable"]["Races"]

    rows = []
    for race in races:
        season_ = int(race["season"])
        round_ = int(race["round"])
        for q in race.get("QualifyingResults", []):
            driver = q["Driver"]
            rows.append({
                "season": season_,
                "round": round_,
                "driver_id": driver["driverId"],
                "qualifying_position": pd.to_numeric(q.get("position"), errors="coerce"),
                "q1": q.get("Q1"),
                "q2": q.get("Q2"),
                "q3": q.get("Q3"),
            })
    return pd.DataFrame(rows)


def main(start_season: int, end_season: int, out_dir: str):
    out_path = ensure_dir(out_dir)
    all_results = []
    all_quali = []

    for season in range(start_season, end_season + 1):
        print(f"Fetching Jolpica season {season}...")
        all_results.append(get_results_for_season(season))
        all_quali.append(get_qualifying_for_season(season))

    results_df = pd.concat(all_results, ignore_index=True)
    quali_df = pd.concat(all_quali, ignore_index=True)

    save_df(results_df, out_path / f"jolpica_results_{start_season}_{end_season}.parquet")
    save_df(quali_df, out_path / f"jolpica_qualifying_{start_season}_{end_season}.parquet")
    print("Saved Jolpica ingestion files.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-season", type=int, required=True)
    parser.add_argument("--end-season", type=int, required=True)
    parser.add_argument("--out-dir", type=str, default="data/raw")
    args = parser.parse_args()

    main(args.start_season, args.end_season, args.out_dir)