import pandas as pd
import numpy as np
from typing import List, Tuple

def compute_rolling_workload_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate sports-science training load metrics per athlete.
    
    Includes:
    - Multi-window rolling load sums and means (3d, 7d, 14d, 28d)
    - Acute Training Load (ATL, 7d rolling sum)
    - Chronic Training Load (CTL, 28d rolling daily average)
    - Acute:Chronic Workload Ratio (ACWR) with stability epsilon
    - Workload Monotony and Strain
    """
    df = df.sort_values(["player_id", "date"]).reset_index(drop=True)
    grouped = df.groupby("player_id")["daily_load"]
    
    # Rolling load sums
    df["load_3d_sum"] = grouped.transform(lambda s: s.rolling(3, min_periods=1).sum())
    df["load_7d_sum"] = grouped.transform(lambda s: s.rolling(7, min_periods=1).sum())
    df["load_14d_sum"] = grouped.transform(lambda s: s.rolling(14, min_periods=1).sum())
    df["load_28d_sum"] = grouped.transform(lambda s: s.rolling(28, min_periods=1).sum())
    
    # Rolling load daily averages
    df["load_3d_avg"] = grouped.transform(lambda s: s.rolling(3, min_periods=1).mean())
    df["load_7d_avg"] = grouped.transform(lambda s: s.rolling(7, min_periods=1).mean())
    df["load_14d_avg"] = grouped.transform(lambda s: s.rolling(14, min_periods=1).mean())
    df["load_28d_avg"] = grouped.transform(lambda s: s.rolling(28, min_periods=1).mean())
    
    # Acute Training Load (ATL_7d sum) & Chronic Training Load (CTL_28d daily mean)
    df["atl_7d"] = df["load_7d_sum"]
    df["ctl_28d"] = df["load_28d_avg"]
    
    # Uncoupled Acute:Chronic Workload Ratio
    # ACWR = (7-day daily mean load) / (28-day daily mean load + epsilon)
    eps = 1e-4
    df["acwr_calc"] = (df["load_7d_avg"]) / (df["ctl_28d"] + eps)
    
    # Monotony & Strain (Foster et al., 1998)
    def calc_monotony(s: pd.Series) -> pd.Series:
        r_mean = s.rolling(7, min_periods=3).mean()
        r_std = s.rolling(7, min_periods=3).std().fillna(0)
        return r_mean / (r_std + eps)
        
    df["monotony_calc"] = grouped.transform(calc_monotony)
    df["strain_calc"] = df["load_7d_sum"] * df["monotony_calc"]
    
    return df


def compute_rolling_wellness_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate multi-window rolling averages and trajectories for self-reported wellness.
    """
    df = df.sort_values(["player_id", "date"]).reset_index(drop=True)
    wellness_cols = [
        "fatigue", "soreness", "mood", "readiness",
        "sleep_duration", "sleep_quality", "stress"
    ]
    
    for col in wellness_cols:
        grouped = df.groupby("player_id")[col]
        # Impute missing values with forward fill per athlete up to 7 days, then athlete median
        filled = grouped.transform(lambda s: s.ffill(limit=7))
        
        df[f"{col}_3d_avg"] = df.groupby("player_id")[col].transform(
            lambda s: s.rolling(3, min_periods=1).mean()
        )
        df[f"{col}_7d_avg"] = df.groupby("player_id")[col].transform(
            lambda s: s.rolling(7, min_periods=1).mean()
        )
        df[f"{col}_14d_avg"] = df.groupby("player_id")[col].transform(
            lambda s: s.rolling(14, min_periods=1).mean()
        )
        df[f"{col}_28d_avg"] = df.groupby("player_id")[col].transform(
            lambda s: s.rolling(28, min_periods=1).mean()
        )
        
    return df


def compute_athlete_relative_zscores(df: pd.DataFrame, window: int = 28) -> pd.DataFrame:
    """
    Compute athlete-relative rolling baseline z-scores for load and wellness.
    
    Z = (Value_t - RollingMean_28d) / (RollingStd_28d + epsilon)
    """
    df = df.sort_values(["player_id", "date"]).reset_index(drop=True)
    target_cols = [
        "daily_load", "fatigue", "soreness", "sleep_duration",
        "sleep_quality", "stress", "readiness", "mood"
    ]
    eps = 1e-4
    
    for col in target_cols:
        grouped = df.groupby("player_id")[col]
        r_mean = grouped.transform(lambda s: s.rolling(window, min_periods=5).mean())
        r_std = grouped.transform(lambda s: s.rolling(window, min_periods=5).std().fillna(0))
        
        df[f"{col}_zscore"] = (df[col] - r_mean) / (r_std + eps)
        # Fallback to standard athlete baseline z-score if rolling period is sparse
        ath_mean = grouped.transform("mean")
        ath_std = grouped.transform("std").fillna(0)
        fallback_z = (df[col] - ath_mean) / (ath_std + eps)
        df[f"{col}_zscore"] = df[f"{col}_zscore"].fillna(fallback_z).fillna(0.0)
        
    return df


def compute_workload_change_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate acute workload spikes and wellness delta changes.
    """
    df = df.sort_values(["player_id", "date"]).reset_index(drop=True)
    
    # 1-day, 3-day, 7-day load deltas
    df["load_change_1d"] = df.groupby("player_id")["daily_load"].diff(1).fillna(0.0)
    df["load_change_3d"] = df["load_3d_avg"] - df["load_7d_avg"]
    
    # Acute 7-day change vs previous 7-day window
    prev_7d_load = df.groupby("player_id")["load_7d_sum"].shift(7)
    df["load_change_7d"] = (df["load_7d_sum"] - prev_7d_load).fillna(0.0)
    
    # Wellness deltas (current day vs 7-day average)
    df["fatigue_delta_7d"] = df["fatigue"] - df["fatigue_7d_avg"]
    df["soreness_delta_7d"] = df["soreness"] - df["soreness_7d_avg"]
    df["sleep_quality_delta_7d"] = df["sleep_quality"] - df["sleep_quality_7d_avg"]
    df["readiness_delta_7d"] = df["readiness"] - df["readiness_7d_avg"]
    df["stress_delta_7d"] = df["stress"] - df["stress_7d_avg"]
    
    # Sports science compound indices
    # Recovery Deficit: high fatigue + soreness + stress vs sleep quality + readiness
    df["recovery_deficit_index"] = (
        (df["fatigue"].fillna(3) + df["soreness"].fillna(3) + df["stress"].fillna(3)) -
        (df["sleep_quality"].fillna(6) + df["readiness"].fillna(6))
    )
    
    # Workload-Soreness Interaction
    df["workload_soreness_interaction"] = df["acwr"].fillna(1.0) * df["soreness"].fillna(3.0)
    
    return df


def build_feature_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Execute full feature engineering pipeline.
    
    Parameters
    ----------
    df : pd.DataFrame
        Processed longitudinal player-day dataframe.
        
    Returns
    -------
    pd.DataFrame
        Enriched dataframe with all engineered features.
    """
    print("Computing rolling workload features...")
    df = compute_rolling_workload_features(df)
    
    print("Computing rolling wellness trajectories...")
    df = compute_rolling_wellness_features(df)
    
    print("Computing athlete-relative baseline z-scores...")
    df = compute_athlete_relative_zscores(df, window=28)
    
    print("Computing workload change deltas and interaction indices...")
    df = compute_workload_change_features(df)
    
    return df


def get_feature_columns() -> List[str]:
    """Return canonical list of feature column names for machine learning models."""
    return [
        # Baseline raw signals
        "daily_load", "weekly_load", "atl", "ctl28", "acwr", "monotony", "strain",
        "session_duration", "session_rpe", "session_count",
        "fatigue", "soreness", "mood", "readiness", "sleep_duration", "sleep_quality", "stress",
        
        # Multi-window rolling workload features
        "load_3d_sum", "load_7d_sum", "load_14d_sum", "load_28d_sum",
        "load_3d_avg", "load_7d_avg", "load_14d_avg", "load_28d_avg",
        "acwr_calc", "monotony_calc", "strain_calc",
        
        # Multi-window rolling wellness features
        "fatigue_3d_avg", "fatigue_7d_avg", "fatigue_14d_avg", "fatigue_28d_avg",
        "soreness_3d_avg", "soreness_7d_avg", "soreness_14d_avg", "soreness_28d_avg",
        "sleep_duration_3d_avg", "sleep_duration_7d_avg",
        "sleep_quality_3d_avg", "sleep_quality_7d_avg",
        "stress_3d_avg", "stress_7d_avg",
        "readiness_3d_avg", "readiness_7d_avg",
        
        # Athlete-relative rolling z-scores
        "daily_load_zscore", "fatigue_zscore", "soreness_zscore",
        "sleep_duration_zscore", "sleep_quality_zscore", "stress_zscore",
        "readiness_zscore", "mood_zscore",
        
        # Rate of change deltas & interactions
        "load_change_1d", "load_change_3d", "load_change_7d",
        "fatigue_delta_7d", "soreness_delta_7d", "sleep_quality_delta_7d",
        "readiness_delta_7d", "stress_delta_7d",
        "recovery_deficit_index", "workload_soreness_interaction"
    ]


if __name__ == "__main__":
    import os
    input_path = "data/processed/player_daily.csv"
    if not os.path.exists(input_path):
        from src.data_processing import load_and_preprocess_soccermon
        load_and_preprocess_soccermon()
        
    df = pd.read_csv(input_path)
    df["date"] = pd.to_datetime(df["date"])
    df_feat = build_feature_pipeline(df)
    
    features = get_feature_columns()
    print(f"Engineered {len(features)} sports-science features.")
    print("Feature columns sample:", features[:10])
    
    output_path = "data/processed/player_daily_features.csv"
    df_feat.to_csv(output_path, index=False)
    print(f"Saved feature-enriched dataset to {output_path}.")
