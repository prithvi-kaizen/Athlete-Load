import pytest
import pandas as pd
import numpy as np
from src.data_processing import generate_causal_targets

def test_causal_target_generation_no_leakage():
    # Construct synthetic timeline for a single player
    dates = pd.date_range("2021-01-01", periods=15, freq="D")
    df = pd.DataFrame({
        "player_id": ["P01"] * 15,
        "date": dates,
        "injury_reported": [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0], # Injury on day index 7 (Jan 8)
        "readiness": [7, 6, 8, 5, 6, 7, 4, 3, 5, 6, 7, 8, 7, 6, 5]
    })
    
    df_targeted = generate_causal_targets(df)
    
    # Verify injury_next_7_days is 1 strictly for days t in [Jan 1 to Jan 7] (indices 0 to 6)
    # Because for index 0 (Jan 1), window [Jan 2..Jan 8] contains the injury on Jan 8.
    # For index 6 (Jan 7), window [Jan 8..Jan 14] contains the injury on Jan 8.
    # For index 7 (Jan 8, day of injury itself), forward window is [Jan 9..Jan 15] which has NO injury -> MUST BE 0!
    expected_injury_7d = [1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0]
    np.testing.assert_array_equal(df_targeted["injury_next_7_days"].values, expected_injury_7d)
    
    # Verify readiness_next_day is strictly shifted by -1 (next day)
    expected_readiness_next_day = [6, 8, 5, 6, 7, 4, 3, 5, 6, 7, 8, 7, 6, 5, np.nan]
    np.testing.assert_array_equal(
        df_targeted["readiness_next_day"].iloc[:-1].values,
        expected_readiness_next_day[:-1]
    )
    assert np.isnan(df_targeted["readiness_next_day"].iloc[-1])

def test_multi_player_independence_in_targets():
    dates = pd.date_range("2021-01-01", periods=5, freq="D")
    df = pd.DataFrame({
        "player_id": ["P01"] * 5 + ["P02"] * 5,
        "date": list(dates) + list(dates),
        "injury_reported": [0, 0, 1, 0, 0] + [0, 0, 0, 0, 0],
        "readiness": [7, 8, 6, 5, 6] + [8, 8, 8, 7, 7]
    })
    
    df_targeted = generate_causal_targets(df)
    
    p1 = df_targeted[df_targeted["player_id"] == "P01"]
    p2 = df_targeted[df_targeted["player_id"] == "P02"]
    
    # P01 has injury on day 2 (Jan 3) -> days 0 and 1 have injury_next_7_days=1
    assert p1["injury_next_7_days"].iloc[0] == 1
    assert p1["injury_next_7_days"].iloc[1] == 1
    assert p1["injury_next_7_days"].iloc[2] == 0
    
    # P02 has 0 injuries throughout -> all injury_next_7_days must be 0
    assert (p2["injury_next_7_days"] == 0).all()
