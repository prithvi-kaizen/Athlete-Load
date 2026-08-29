import os
import json
import zipfile
import argparse
import requests
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any

ZENODO_ZIP_URL = "https://zenodo.org/records/10033832/files/subjective.zip"

def download_soccermon_subjective(raw_dir: str = "data/raw") -> str:
    """
    Download and extract the subjective component of SoccerMon from Zenodo.
    
    Parameters
    ----------
    raw_dir : str
        Directory to store the raw zip and extracted files.
        
    Returns
    -------
    str
        Path to the extracted subjective directory.
    """
    os.makedirs(raw_dir, exist_ok=True)
    zip_path = os.path.join(raw_dir, "subjective.zip")
    extracted_dir = os.path.join(raw_dir, "subjective")
    
    if not os.path.exists(zip_path):
        print(f"Downloading subjective.zip from Zenodo ({ZENODO_ZIP_URL})...")
        response = requests.get(ZENODO_ZIP_URL, stream=True, timeout=120)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to download subjective.zip: HTTP {response.status_code}")
        
        with open(zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=16384):
                if chunk:
                    f.write(chunk)
        print(f"Downloaded {os.path.getsize(zip_path):,} bytes to {zip_path}.")
    
    if not os.path.exists(extracted_dir):
        print(f"Extracting {zip_path} to {raw_dir}...")
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(raw_dir)
        print("Extraction complete.")
        
    return extracted_dir


def _melt_wide_matrix(csv_path: str, value_name: str) -> pd.DataFrame:
    """Helper to convert wide SoccerMon matrix CSV (Date x Player columns) to long format."""
    df = pd.read_csv(csv_path)
    date_col = df.columns[0]
    df["date"] = pd.to_datetime(df[date_col], format="%d.%m.%Y")
    df = df.drop(columns=[date_col])
    long_df = df.melt(id_vars=["date"], var_name="player_id", value_name=value_name)
    return long_df


def load_raw_subjective_tables(raw_dir: str = "data/raw") -> pd.DataFrame:
    """
    Load all subjective metrics and merge them on (player_id, date).
    
    Parameters
    ----------
    raw_dir : str
        Directory containing the extracted subjective data.
        
    Returns
    -------
    pd.DataFrame
        Longitudinal player-day dataframe.
    """
    subj_dir = os.path.join(raw_dir, "subjective")
    if not os.path.exists(subj_dir):
        download_soccermon_subjective(raw_dir=raw_dir)
    
    # 1. Subjective wellness metrics
    wellness_files = {
        "fatigue": os.path.join(subj_dir, "wellness", "fatigue.csv"),
        "soreness": os.path.join(subj_dir, "wellness", "soreness.csv"),
        "mood": os.path.join(subj_dir, "wellness", "mood.csv"),
        "readiness": os.path.join(subj_dir, "wellness", "readiness.csv"),
        "sleep_duration": os.path.join(subj_dir, "wellness", "sleep_duration.csv"),
        "sleep_quality": os.path.join(subj_dir, "wellness", "sleep_quality.csv"),
        "stress": os.path.join(subj_dir, "wellness", "stress.csv"),
    }
    
    # 2. Subjective training load metrics
    load_files = {
        "daily_load": os.path.join(subj_dir, "training-load", "daily_load.csv"),
        "weekly_load": os.path.join(subj_dir, "training-load", "weekly_load.csv"),
        "atl": os.path.join(subj_dir, "training-load", "atl.csv"),
        "ctl28": os.path.join(subj_dir, "training-load", "ctl28.csv"),
        "ctl42": os.path.join(subj_dir, "training-load", "ctl42.csv"),
        "acwr": os.path.join(subj_dir, "training-load", "acwr.csv"),
        "monotony": os.path.join(subj_dir, "training-load", "monotony.csv"),
        "strain": os.path.join(subj_dir, "training-load", "strain.csv"),
    }
    
    all_files = {**wellness_files, **load_files}
    merged_df: Optional[pd.DataFrame] = None
    
    for metric_name, path in all_files.items():
        if not os.path.exists(path):
            raise FileNotFoundError(f"Expected file {path} not found.")
        long_df = _melt_wide_matrix(path, metric_name)
        if merged_df is None:
            merged_df = long_df
        else:
            merged_df = pd.merge(merged_df, long_df, on=["date", "player_id"], how="outer")
            
    # 3. Session details (session.json)
    session_json_path = os.path.join(subj_dir, "training-load", "session.json")
    if os.path.exists(session_json_path):
        with open(session_json_path, "r") as f:
            session_dict = json.load(f)
            
        session_records = []
        for player_id, sessions in session_dict.items():
            for s in sessions:
                session_records.append({
                    "player_id": player_id,
                    "date": pd.to_datetime(s["date"], format="%d.%m.%Y"),
                    "duration": s.get("duration", 0),
                    "rpe": s.get("rpe", 0),
                    "srpe": s.get("srpe", 0)
                })
        if session_records:
            sess_df = pd.DataFrame(session_records)
            daily_sess = sess_df.groupby(["player_id", "date"]).agg(
                session_count=("srpe", "count"),
                session_duration=("duration", "sum"),
                session_rpe=("rpe", "mean"),
                session_srpe=("srpe", "sum")
            ).reset_index()
            merged_df = pd.merge(merged_df, daily_sess, on=["player_id", "date"], how="left")
            merged_df["session_count"] = merged_df["session_count"].fillna(0).astype(int)
            merged_df["session_duration"] = merged_df["session_duration"].fillna(0)
            merged_df["session_rpe"] = merged_df["session_rpe"].fillna(0)
            merged_df["session_srpe"] = merged_df["session_srpe"].fillna(0)

    # 4. Injury reports
    injury_csv_path = os.path.join(subj_dir, "injury", "injury.csv")
    if os.path.exists(injury_csv_path):
        inj_df = pd.read_csv(injury_csv_path)
        inj_df["date"] = pd.to_datetime(inj_df["timestamp"], format="%d.%m.%Y")
        inj_df["injury_reported"] = 1
        
        # Parse injury locations and severities
        def parse_injury_details(type_str: str) -> Dict[str, Any]:
            locations = []
            major_count = 0
            minor_count = 0
            try:
                data = json.loads(type_str)
                for loc, sev in data.items():
                    locations.append(loc)
                    if sev == "major":
                        major_count += 1
                    else:
                        minor_count += 1
            except Exception:
                pass
            return {
                "injury_locations": ";".join(locations),
                "has_major_injury": int(major_count > 0),
                "injury_count": len(locations)
            }
            
        details = inj_df["type"].apply(parse_injury_details).apply(pd.Series)
        inj_df = pd.concat([inj_df, details], axis=1)
        
        inj_daily = inj_df.groupby(["date", "player_name"]).agg(
            injury_reported=("injury_reported", "max"),
            has_major_injury=("has_major_injury", "max"),
            injury_count=("injury_count", "sum"),
            injury_locations=("injury_locations", lambda s: ";".join([x for x in s if x]))
        ).reset_index().rename(columns={"player_name": "player_id"})
        
        merged_df = pd.merge(merged_df, inj_daily, on=["date", "player_id"], how="left")
        merged_df["injury_reported"] = merged_df["injury_reported"].fillna(0).astype(int)
        merged_df["has_major_injury"] = merged_df["has_major_injury"].fillna(0).astype(int)
        merged_df["injury_count"] = merged_df["injury_count"].fillna(0).astype(int)
        merged_df["injury_locations"] = merged_df["injury_locations"].fillna("none")

    # 5. Extract team label from player_id
    merged_df["team"] = merged_df["player_id"].apply(lambda x: x.split("-")[0] if "-" in x else "Unknown")
    
    # Sort chronologically by player and date
    merged_df = merged_df.sort_values(["player_id", "date"]).reset_index(drop=True)
    return merged_df


def generate_causal_targets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construct forward-looking prediction targets ensuring zero temporal data leakage.
    
    Targets:
    1. injury_next_7_days: Binary indicator equal to 1 if the player logs an injury
       report in the future window (t+1 to t+7), 0 otherwise.
    2. readiness_next_day: Player-reported readiness value on day t+1.
    3. low_readiness_next_day: Binary indicator equal to 1 if readiness <= 4 on day t+1.
    
    Parameters
    ----------
    df : pd.DataFrame
        Longitudinal player-day dataframe sorted by (player_id, date).
        
    Returns
    -------
    pd.DataFrame
        Dataframe with added target columns.
    """
    df = df.sort_values(["player_id", "date"]).reset_index(drop=True)
    
    # Causal 7-day forward injury target: look at t+1 to t+7
    # For day t, shift -1 (day t+1), then roll 7 days looking ahead
    def forward_max_7d(series: pd.Series) -> pd.Series:
        # Reversing series allows standard rolling window looking backwards
        # Reversing twice returns strictly future forward window [t+1, t+7]
        shifted = series.shift(-1)
        # 7-day rolling window on shifted future values
        future_window = shifted.iloc[::-1].rolling(window=7, min_periods=1).max().iloc[::-1]
        return future_window.fillna(0).astype(int)
        
    df["injury_next_7_days"] = df.groupby("player_id")["injury_reported"].transform(forward_max_7d)
    
    # Next day readiness targets
    df["readiness_next_day"] = df.groupby("player_id")["readiness"].shift(-1)
    df["low_readiness_next_day"] = (df["readiness_next_day"] <= 4.0).astype(float)
    df.loc[df["readiness_next_day"].isna(), "low_readiness_next_day"] = np.nan
    
    return df


def load_and_preprocess_soccermon(
    raw_dir: str = "data/raw",
    output_path: str = "data/processed/player_daily.csv"
) -> pd.DataFrame:
    """
    Run full data ingestion, cleaning, multi-session aggregation, and causal target generation.
    
    Parameters
    ----------
    raw_dir : str
        Directory where raw data resides.
    output_path : str
        Destination CSV file path for cleaned master table.
        
    Returns
    -------
    pd.DataFrame
        Processed longitudinal player-day master dataset.
    """
    print("Loading raw SoccerMon subjective tables...")
    df = load_raw_subjective_tables(raw_dir=raw_dir)
    
    print("Generating forward-looking causal targets...")
    df = generate_causal_targets(df)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved processed dataset ({df.shape[0]:,} rows, {df.shape[1]} columns) to {output_path}.")
    
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SoccerMon Data Processing Pipeline")
    parser.add_argument("--raw-dir", type=str, default="data/raw", help="Path to raw data directory")
    parser.add_argument("--output", type=str, default="data/processed/player_daily.csv", help="Path to output CSV")
    parser.add_argument("--download", action="store_true", help="Force download dataset from Zenodo")
    args = parser.parse_args()
    
    if args.download:
        download_soccermon_subjective(raw_dir=args.raw_dir)
        
    load_and_preprocess_soccermon(raw_dir=args.raw_dir, output_path=args.output)
