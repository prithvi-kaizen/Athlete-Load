import pytest
import pandas as pd
import numpy as np
from src.features import (
    compute_rolling_workload_features,
    compute_rolling_wellness_features,
    compute_athlete_relative_zscores,
    compute_workload_change_features,
    get_feature_columns,
    build_feature_pipeline
)

@pytest.fixture
def sample_player_timeline():
    dates = pd.date_range("2021-01-01", periods=30, freq="D")
    df = pd.DataFrame({
        "player_id": ["P01"] * 30,
        "date": dates,
        "daily_load": [100.0, 200.0, 150.0, 300.0, 0.0, 400.0, 250.0] * 4 + [200.0, 300.0],
        "weekly_load": [1400.0] * 30,
        "atl": [1400.0] * 30,
        "ctl28": [200.0] * 30,
        "ctl42": [200.0] * 30,
        "acwr": [1.0] * 30,
        "monotony": [1.2] * 30,
        "strain": [1680.0] * 30,
        "session_duration": [60.0] * 30,
        "session_rpe": [5.0] * 30,
        "session_count": [1] * 30,
        "session_srpe": [300.0] * 30,
        "fatigue": [4.0] * 30,
        "soreness": [3.0] * 30,
        "mood": [7.0] * 30,
        "readiness": [7.0] * 30,
        "sleep_duration": [8.0] * 30,
        "sleep_quality": [7.0] * 30,
        "stress": [3.0] * 30,
        "injury_reported": [0] * 30,
        "has_major_injury": [0] * 30,
        "injury_count": [0] * 30,
        "injury_locations": ["none"] * 30,
        "team": ["TeamA"] * 30,
        "injury_next_7_days": [0] * 30,
        "readiness_next_day": [7.0] * 30,
        "low_readiness_next_day": [0.0] * 30
    })
    return df

def test_rolling_workload_metrics(sample_player_timeline):
    df_feat = compute_rolling_workload_features(sample_player_timeline)
    
    # 7-day load sum at day index 6 (Jan 7) should equal sum of first 7 loads
    expected_7d_sum = sum(sample_player_timeline["daily_load"].iloc[:7])
    assert np.isclose(df_feat["load_7d_sum"].iloc[6], expected_7d_sum)
    assert np.isclose(df_feat["atl_7d"].iloc[6], expected_7d_sum)
    
    # ACWR should be positive and finite
    assert (df_feat["acwr_calc"] >= 0).all()
    assert not df_feat["acwr_calc"].isna().any()

def test_athlete_relative_zscores(sample_player_timeline):
    # Introduce sudden spike at day index 25
    sample_player_timeline.loc[25, "daily_load"] = 1200.0
    df_feat = compute_athlete_relative_zscores(sample_player_timeline, window=28)
    
    # Load z-score on spike day should be clearly positive (> 2.0)
    assert df_feat["daily_load_zscore"].iloc[25] > 2.0
    assert not df_feat["daily_load_zscore"].isna().any()

def test_full_pipeline_output_columns(sample_player_timeline):
    df_all = build_feature_pipeline(sample_player_timeline)
    feature_cols = get_feature_columns()
    
    for col in feature_cols:
        assert col in df_all.columns, f"Missing feature column: {col}"
    assert len(feature_cols) >= 50
