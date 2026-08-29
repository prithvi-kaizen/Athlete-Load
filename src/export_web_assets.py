import json
import pandas as pd
import numpy as np

def export_web_data():
    df = pd.read_csv("data/processed/player_daily_features.csv")
    df["date"] = pd.to_datetime(df["date"])
    
    # 1. Representative athletes
    athletes = {
        "TeamA-5cd7a61b (Forward, High Load)": "TeamA-5cd7a61b-88b2-46d2-94f8-5a0d4f682d93",
        "TeamA-d7299614 (Midfielder, Consistent)": "TeamA-d7299614-fa73-4f69-b5e9-f913e3154ff6",
        "TeamA-4051bba7 (Defender, Multiple Reports)": "TeamA-4051bba7-1170-4c43-b912-8c38815a7625",
        "TeamB-4405bb1f (Team B Athlete)": "TeamB-4405bb1f-56f7-48ba-bfa8-e795e4006952"
    }
    
    timelines = {}
    for label, aid in athletes.items():
        sub = df[df["player_id"] == aid].sort_values("date")
        timelines[label] = {
            "dates": sub["date"].dt.strftime("%Y-%m-%d").tolist(),
            "daily_load": sub["daily_load"].fillna(0).round(1).tolist(),
            "atl_7d": sub["atl_7d"].fillna(0).round(1).tolist(),
            "ctl_28d": (sub["ctl_28d"] * 7).fillna(0).round(1).tolist(),
            "acwr": sub["acwr_calc"].fillna(1.0).round(2).tolist(),
            "soreness": sub["soreness"].fillna(3.0).round(1).tolist(),
            "fatigue": sub["fatigue"].fillna(3.0).round(1).tolist(),
            "readiness": sub["readiness"].fillna(7.0).round(1).tolist(),
            "injuries": sub["injury_reported"].fillna(0).astype(int).tolist()
        }
        
    # 2. Benchmarks
    comp_df = pd.read_csv("results/metrics/model_comparison.csv")
    benchmarks = comp_df.to_dict(orient="records")
    
    # 3. Statistical tests
    stat_df = pd.read_csv("results/metrics/statistical_tests.csv")
    stat_records = stat_df.head(10).to_dict(orient="records")
    
    # Write to data.js
    js_content = f"""// Auto-generated web assets from AthleteLoad Python Research Pipeline
const SOCCERMON_TIMELINES = {json.dumps(timelines, indent=2)};
const MODEL_BENCHMARKS = {json.dumps(benchmarks, indent=2)};
const STATISTICAL_TESTS = {json.dumps(stat_records, indent=2)};
"""
    with open("data.js", "w") as f:
        f.write(js_content)
        
    print("Exported data.js with real SoccerMon timelines and metrics.")

if __name__ == "__main__":
    export_web_data()
