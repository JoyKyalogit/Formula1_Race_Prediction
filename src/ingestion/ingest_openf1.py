import argparse
import requests
import pandas as pd
from src.utils.io_utils import ensure_dir, save_df

BASE_URL = "https://api.openf1.org/v1"


def fetch(endpoint: str, params: dict | None = None) -> list[dict]:
    url = f"{BASE_URL}/{endpoint}"
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def main(year: int, out_dir: str):
    out_path = ensure_dir(out_dir)

    print(f"Fetching OpenF1 meetings for {year}...")
    meetings = fetch("meetings", {"year": year})
    meetings_df = pd.DataFrame(meetings)
    save_df(meetings_df, out_path / f"openf1_meetings_{year}.parquet")

    print(f"Fetching OpenF1 sessions for {year}...")
    sessions = fetch("sessions", {"year": year})
    sessions_df = pd.DataFrame(sessions)
    save_df(sessions_df, out_path / f"openf1_sessions_{year}.parquet")

    all_laps = []
    if "session_key" in sessions_df.columns:
        race_sessions = sessions_df[sessions_df["session_name"].astype(str).str.contains("Race", case=False, na=False)]
        for sk in race_sessions["session_key"].dropna().unique().tolist():
            print(f"Fetching laps for session_key={sk}...")
            try:
                laps = fetch("laps", {"session_key": int(sk)})
            except requests.HTTPError as e:
                # Some sessions may legitimately have no laps endpoint yet.
                if e.response is not None and e.response.status_code == 404:
                    print(f"Skipping session_key={sk}: laps not found (404).")
                    continue
                raise
            if laps:
                laps_df = pd.DataFrame(laps)
                laps_df["session_key"] = int(sk)
                all_laps.append(laps_df)

    if all_laps:
        laps_df = pd.concat(all_laps, ignore_index=True)
    else:
        laps_df = pd.DataFrame()

    save_df(laps_df, out_path / f"openf1_laps_{year}.parquet")
    print("Saved OpenF1 ingestion files.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--out-dir", type=str, default="data/raw")
    args = parser.parse_args()

    main(args.year, args.out_dir)