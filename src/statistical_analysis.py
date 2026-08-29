import os
import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.stats.multitest import multipletests
from typing import List, Dict, Any

def compute_cliffs_delta(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Compute Cliff's Delta effect size for non-parametric comparisons.
    
    Delta = (#(x1 > x2) - #(x1 < x2)) / (n1 * n2)
    Ranges from -1.0 to +1.0.
    """
    g1 = np.asarray(group1)
    g2 = np.asarray(group2)
    g1 = g1[~np.isnan(g1)]
    g2 = g2[~np.isnan(g2)]
    
    n1, n2 = len(g1), len(g2)
    if n1 == 0 or n2 == 0:
        return 0.0
        
    # Efficient Mann-Whitney U based conversion
    u_stat, _ = stats.mannwhitneyu(g1, g2, alternative='two-sided')
    delta = (2 * u_stat) / (n1 * n2) - 1.0
    return float(delta)

def compute_cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """Compute Cohen's d standardized mean difference."""
    g1 = np.asarray(group1)
    g2 = np.asarray(group2)
    g1 = g1[~np.isnan(g1)]
    g2 = g2[~np.isnan(g2)]
    
    n1, n2 = len(g1), len(g2)
    if n1 < 2 or n2 < 2:
        return 0.0
        
    m1, m2 = np.mean(g1), np.mean(g2)
    s1, s2 = np.var(g1, ddof=1), np.var(g2, ddof=1)
    pooled_std = np.sqrt(((n1 - 1) * s1 + (n2 - 1) * s2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return float((m1 - m2) / pooled_std)

def run_pre_injury_comparisons(
    df: pd.DataFrame,
    variables: List[str],
    target_col: str = "injury_next_7_days"
) -> pd.DataFrame:
    """
    Perform statistical tests comparing pre-injury athlete-days vs normal healthy periods.
    
    Parameters
    ----------
    df : pd.DataFrame
        Dataset containing features and injury label.
    variables : List[str]
        List of numerical variables to compare.
    target_col : str
        Target column separating pre-injury (1) vs healthy (0).
        
    Returns
    -------
    pd.DataFrame
        Statistical summary table with medians, IQRs, test statistics, and effect sizes.
    """
    records = []
    
    injury_mask = df[target_col] == 1
    healthy_mask = df[target_col] == 0
    
    for var in variables:
        if var not in df.columns:
            continue
            
        inj_vals = df.loc[injury_mask, var].dropna().values
        hlth_vals = df.loc[healthy_mask, var].dropna().values
        
        if len(inj_vals) < 5 or len(hlth_vals) < 5:
            continue
            
        u_stat, p_val = stats.mannwhitneyu(inj_vals, hlth_vals, alternative="two-sided")
        cliffs_d = compute_cliffs_delta(inj_vals, hlth_vals)
        cohens_d = compute_cohens_d(inj_vals, hlth_vals)
        
        # Categorize Cliff's delta magnitude
        abs_cd = abs(cliffs_d)
        if abs_cd < 0.147:
            magnitude = "Negligible"
        elif abs_cd < 0.33:
            magnitude = "Small"
        elif abs_cd < 0.474:
            magnitude = "Medium"
        else:
            magnitude = "Large"
            
        records.append({
            "variable": var,
            "injury_median": float(np.median(inj_vals)),
            "injury_iqr": float(np.percentile(inj_vals, 75) - np.percentile(inj_vals, 25)),
            "injury_mean": float(np.mean(inj_vals)),
            "injury_std": float(np.std(inj_vals)),
            "healthy_median": float(np.median(hlth_vals)),
            "healthy_iqr": float(np.percentile(hlth_vals, 75) - np.percentile(hlth_vals, 25)),
            "healthy_mean": float(np.mean(hlth_vals)),
            "healthy_std": float(np.std(hlth_vals)),
            "mann_whitney_u": float(u_stat),
            "p_value": float(p_val),
            "cliffs_delta": float(cliffs_d),
            "effect_magnitude": magnitude,
            "cohens_d": float(cohens_d)
        })
        
    res_df = pd.DataFrame(records)
    
    # Benjamini-Hochberg FDR correction
    if len(res_df) > 0:
        _, p_adj, _, _ = multipletests(res_df["p_value"], method="fdr_bh")
        res_df["p_value_fdr"] = p_adj
        res_df["significant_fdr"] = res_df["p_value_fdr"] < 0.05
        
    return res_df.sort_values("p_value").reset_index(drop=True)

if __name__ == "__main__":
    import os
    os.makedirs("results/metrics", exist_ok=True)
    
    feat_path = "data/processed/player_daily_features.csv"
    if not os.path.exists(feat_path):
        from src.data_processing import load_and_preprocess_soccermon
        from src.features import build_feature_pipeline
        df = load_and_preprocess_soccermon()
        df = build_feature_pipeline(df)
    else:
        df = pd.read_csv(feat_path)
        
    key_vars = [
        "daily_load", "load_7d_sum", "load_28d_sum", "atl", "ctl28", "acwr",
        "fatigue", "soreness", "sleep_duration", "sleep_quality", "stress",
        "mood", "readiness", "daily_load_zscore", "fatigue_zscore", "soreness_zscore",
        "load_change_7d", "recovery_deficit_index", "workload_soreness_interaction"
    ]
    
    stats_df = run_pre_injury_comparisons(df, key_vars)
    out_csv = "results/metrics/statistical_tests.csv"
    stats_df.to_csv(out_csv, index=False)
    print(f"Statistical comparisons computed and saved to {out_csv}.")
    print("\nTop significant factors (pre-injury vs healthy):")
    print(stats_df[["variable", "injury_median", "healthy_median", "p_value_fdr", "cliffs_delta", "effect_magnitude"]].head(10))
