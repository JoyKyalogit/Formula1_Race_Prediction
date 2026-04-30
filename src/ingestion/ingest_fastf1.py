import argparse
from pathlib import Path
import pandas as pd
import fastf1
from src.utils.io_utils import ensure_dir, save_df


def _to_seconds(series: pd.Series) -> pd.Series:
    td = pd.to_timedelta(series, errors="coerce")
    return td.dt.total_seconds().astype("float32")


def main(
    year: int,
    session_code: str,
    out_dir: str,
    cache_dir: str = "data/raw/fastf1_cache",
    max_round: int | None = None,
):
    out_path = ensure_dir(out_dir)
    ensure_dir(cache_dir)
    fastf1.Cache.enable_cache(cache_dir)

    schedule = fastf1.get_event_schedule(year)
    all_laps = []
    all_weather = []

    for _, event in schedule.iterrows():
        round_number = int(event["RoundNumber"])
        event_name = str(event["EventName"])

        # Skip testing
        if round_number == 0:
            print(f"Skipping round 0 ({event_name})")
            continue

        # Optional cap for smaller runs
        if max_round is not None and round_number > max_round:
            continue

        try:
            print(f"Loading FastF1 {year} round {round_number} ({event_name}) session {session_code}...")
            session = fastf1.get_session(year, round_number, session_code)
            session.load()

            laps = session.laps.copy()
            if not laps.empty:
                keep_cols = [c for c in [
                    "Driver", "DriverNumber", "Team", "LapNumber",
                    "LapTime", "Sector1Time", "Sector2Time", "Sector3Time",
                    "Compound", "IsAccurate"
                ] if c in laps.columns]
                laps = laps[keep_cols].copy()

                # Convert timedeltas to compact float seconds
                for c in ["LapTime", "Sector1Time", "Sector2Time", "Sector3Time"]:
                    if c in laps.columns:
                        laps[c] = _to_seconds(laps[c])

                # Compact dtypes
                if "LapNumber" in laps.columns:
                    laps["LapNumber"] = pd.to_numeric(laps["LapNumber"], errors="coerce").astype("Int16")
                if "DriverNumber" in laps.columns:
                    laps["DriverNumber"] = pd.to_numeric(laps["DriverNumber"], errors="coerce").astype("Int16")
                if "IsAccurate" in laps.columns:
                    laps["IsAccurate"] = laps["IsAccurate"].fillna(False).astype("bool")

                laps["season"] = year
                laps["round"] = round_number
                laps["event_name"] = event_name
                all_laps.append(laps)

            weather = session.weather_data.copy()
            if not weather.empty:
                keep_weather = [c for c in ["Time", "AirTemp", "Humidity", "Pressure", "Rainfall", "TrackTemp", "WindDirection", "WindSpeed"] if c in weather.columns]
                weather = weather[keep_weather].copy()
                if "Time" in weather.columns:
                    weather["Time"] = _to_seconds(weather["Time"])
                weather["season"] = year
                weather["round"] = round_number
                weather["event_name"] = event_name
                all_weather.append(weather)

        except Exception as e:
            print(f"Skipping round {round_number}: {e}")

    laps_df = pd.concat(all_laps, ignore_index=True) if all_laps else pd.DataFrame()
    weather_df = pd.concat(all_weather, ignore_index=True) if all_weather else pd.DataFrame()

    save_df(laps_df, Path(out_path) / f"fastf1_laps_{year}_{session_code}.parquet")
    save_df(weather_df, Path(out_path) / f"fastf1_weather_{year}_{session_code}.parquet")
    print("Saved FastF1 ingestion files.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--session", type=str, default="R", help="R=Race, Q=Qualifying")
    parser.add_argument("--out-dir", type=str, default="data/raw")
    parser.add_argument("--max-round", type=int, default=12, help="Limit rounds to reduce storage")
    args = parser.parse_args()

    main(args.year, args.session, args.out_dir, max_round=args.max_round)