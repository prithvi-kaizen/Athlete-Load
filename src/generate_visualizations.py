import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_curve, precision_recall_curve, auc, average_precision_score
from sklearn.calibration import calibration_curve
import shap

from src.utils import setup_plotting_style, PALETTE, set_seed
from src.train import run_full_training_pipeline
from src.features import get_feature_columns

def generate_all_figures():
    setup_plotting_style()
    set_seed(42)
    os.makedirs("results/figures", exist_ok=True)
    os.makedirs("results/metrics", exist_ok=True)
    
    # Load dataset
    df_feat_path = "data/processed/player_daily_features.csv"
    if not os.path.exists(df_feat_path):
        from src.data_processing import load_and_preprocess_soccermon
        from src.features import build_feature_pipeline
        df = load_and_preprocess_soccermon()
        df = build_feature_pipeline(df)
        df.to_csv(df_feat_path, index=False)
    else:
        df = pd.read_csv(df_feat_path)
        df["date"] = pd.to_datetime(df["date"])
        
    print("Generating Figure 1: Injury Distribution...")
    # ==========================================
    # FIGURE 1: Injury Distribution
    # ==========================================
    inj_raw_path = "data/raw/subjective/injury/injury.csv"
    if os.path.exists(inj_raw_path):
        inj_raw = pd.read_csv(inj_raw_path)
        locations_list = []
        for s in inj_raw["type"]:
            try:
                d = json.loads(s)
                for loc, sev in d.items():
                    locations_list.append({"location": loc.replace("_", " ").title(), "severity": sev.capitalize()})
            except Exception:
                pass
        inj_loc_df = pd.DataFrame(locations_list)
        
        fig, axes = plt.subplots(1, 2, figsize=(13, 5))
        
        # 1A: Overall location frequency
        loc_counts = inj_loc_df["location"].value_counts().head(8)
        sns.barplot(
            x=loc_counts.values,
            y=loc_counts.index,
            ax=axes[0],
            palette="Blues_r"
        )
        axes[0].set_title("Reported Injuries by Anatomical Location", fontsize=12, fontweight="bold")
        axes[0].set_xlabel("Number of Reports", fontweight="bold")
        axes[0].set_ylabel("Anatomical Location", fontweight="bold")
        for i, v in enumerate(loc_counts.values):
            axes[0].text(v + 1, i, str(v), va="center", fontweight="bold", color="#333333")
            
        # 1B: Severity breakdown
        sev_df = inj_loc_df.groupby(["location", "severity"]).size().unstack(fill_value=0)
        sev_df["total"] = sev_df.sum(axis=1)
        sev_top = sev_df.sort_values("total", ascending=False).head(8).drop(columns=["total"])
        sev_top.plot(
            kind="barh",
            stacked=True,
            ax=axes[1],
            color=[PALETTE["healthy"], PALETTE["danger"]],
            edgecolor="black",
            linewidth=0.5
        )
        axes[1].set_title("Injury Severity Proportion by Location", fontsize=12, fontweight="bold")
        axes[1].set_xlabel("Number of Reports", fontweight="bold")
        axes[1].set_ylabel("")
        axes[1].legend(title="Severity", frameon=True)
        
        plt.tight_layout()
        plt.savefig("results/figures/fig1_injury_distribution.png")
        plt.close()

    print("Generating Figure 2: Training Load Timeline...")
    # ==========================================
    # FIGURE 2: Training Load Timeline
    # ==========================================
    # Select an athlete with high compliance and reported injuries
    sample_pid = "TeamA-5cd7a61b-88b2-46d2-94f8-5a0d4f682d93"
    p_df = df[df["player_id"] == sample_pid].sort_values("date").copy()
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), sharex=True, gridspec_kw={"height_ratios": [2.2, 1.2]})
    
    # 2A: Workloads and injury events
    ax1.bar(p_df["date"], p_df["daily_load"], color="#bdc3c7", alpha=0.5, label="Daily Load (sRPE)", width=1.0)
    ax1.plot(p_df["date"], p_df["atl_7d"], color=PALETTE["primary"], linewidth=2.0, label="ATL (7-day Acute Load)")
    ax1.plot(p_df["date"], p_df["ctl_28d"] * 7, color=PALETTE["accent"], linewidth=2.0, label="CTL (28-day Chronic Load x 7)")
    
    # Highlight injury dates
    inj_dates = p_df[p_df["injury_reported"] == 1]["date"]
    for idt in inj_dates:
        ax1.axvline(idt, color=PALETTE["danger"], linestyle="--", linewidth=1.5, alpha=0.8)
    if len(inj_dates) > 0:
        ax1.plot([], [], color=PALETTE["danger"], linestyle="--", label="Reported Injury Event")
        
    ax1.set_title(f"Longitudinal Workload Trajectory and Injury Events (Athlete: {sample_pid[:12]})", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Workload (sRPE Units)", fontweight="bold")
    ax1.legend(loc="upper right", frameon=True)
    
    # 2B: ACWR with sweet spot band
    ax2.plot(p_df["date"], p_df["acwr_calc"], color=PALETTE["secondary"], linewidth=1.8, label="Calculated ACWR (7:28)")
    ax2.axhspan(0.8, 1.3, color="#2ecc71", alpha=0.2, label="Optimal 'Sweet Spot' (0.8 - 1.3)")
    ax2.axhline(1.5, color=PALETTE["danger"], linestyle=":", linewidth=1.5, label="High Risk Threshold (> 1.5)")
    ax2.set_ylim(0, 3.0)
    ax2.set_ylabel("ACWR", fontweight="bold")
    ax2.set_xlabel("Date", fontweight="bold")
    ax2.legend(loc="upper right", frameon=True)
    
    plt.tight_layout()
    plt.savefig("results/figures/fig2_training_load_timeline.png")
    plt.close()

    print("Generating Figure 3: Wellness Correlation Matrix...")
    # ==========================================
    # FIGURE 3: Wellness Correlation Matrix
    # ==========================================
    corr_cols = ["fatigue", "soreness", "mood", "readiness", "sleep_duration", "sleep_quality", "stress", "atl", "acwr"]
    corr_labels = ["Fatigue", "Soreness", "Mood", "Readiness", "Sleep Dur", "Sleep Qual", "Stress", "ATL", "ACWR"]
    corr_mat = df[corr_cols].corr()
    
    fig, ax = plt.subplots(figsize=(9, 7))
    mask = np.triu(np.ones_like(corr_mat, dtype=bool))
    sns.heatmap(
        corr_mat,
        mask=mask,
        annot=True,
        fmt=".2f",
        cmap="vlag",
        vmin=-1,
        vmax=1,
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.8, "label": "Pearson Correlation Coefficient"},
        xticklabels=corr_labels,
        yticklabels=corr_labels,
        ax=ax
    )
    ax.set_title("Correlation Matrix of Athlete Wellness and Workload Metrics", fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig("results/figures/fig3_wellness_correlation.png")
    plt.close()

    print("Generating Figure 4: Workload Before Injury...")
    # ==========================================
    # FIGURE 4: Workload Before Injury vs Healthy
    # ==========================================
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    metrics_to_plot = [
        ("atl", "Acute Training Load (ATL)", "sRPE units"),
        ("acwr", "Acute:Chronic Ratio (ACWR)", "Ratio"),
        ("load_7d_sum", "7-Day Load Sum", "sRPE units")
    ]
    
    for i, (col, title, unit) in enumerate(metrics_to_plot):
        valid = df[[col, "injury_next_7_days"]].dropna()
        valid["Status"] = valid["injury_next_7_days"].map({0: "Healthy Baseline", 1: "Pre-Injury (7d)"})
        
        sns.boxplot(
            x="Status",
            y=col,
            data=valid,
            ax=axes[i],
            palette=[PALETTE["healthy"], PALETTE["danger"]],
            showfliers=False,
            width=0.45
        )
        axes[i].set_title(title, fontweight="bold", fontsize=11)
        axes[i].set_ylabel(unit, fontweight="bold")
        axes[i].set_xlabel("")
        
    plt.tight_layout()
    plt.savefig("results/figures/fig4_workload_pre_injury.png")
    plt.close()

    print("Generating Figure 5: Soreness & Fatigue Trajectory Before Injury...")
    # ==========================================
    # FIGURE 5: Trajectory Leading Up to Reported Injury
    # ==========================================
    # For all injury events, compute mean wellness trajectory for days -14 to +3
    inj_events = df[df["injury_reported"] == 1][["player_id", "date"]].values
    trajectories = []
    
    for pid, idate in inj_events:
        sub = df[df["player_id"] == pid].sort_values("date")
        idx_match = sub[sub["date"] == idate].index
        if len(idx_match) == 0:
            continue
        curr_idx = idx_match[0]
        for offset in range(-14, 4):
            tgt_date = pd.to_datetime(idate) + pd.Timedelta(days=offset)
            match_row = sub[sub["date"] == tgt_date]
            if len(match_row) > 0:
                row = match_row.iloc[0]
                trajectories.append({
                    "offset_days": offset,
                    "soreness": row["soreness"],
                    "fatigue": row["fatigue"],
                    "readiness": row["readiness"],
                    "daily_load": row["daily_load"]
                })
                
    traj_df = pd.DataFrame(trajectories)
    traj_avg = traj_df.groupby("offset_days").mean().reset_index()
    
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(traj_avg["offset_days"], traj_avg["soreness"], marker="o", color=PALETTE["danger"], linewidth=2.2, label="Muscle Soreness (1-10)")
    ax1.plot(traj_avg["offset_days"], traj_avg["fatigue"], marker="s", color=PALETTE["secondary"], linewidth=2.0, label="Fatigue (1-10)")
    ax1.plot(traj_avg["offset_days"], traj_avg["readiness"], marker="^", color=PALETTE["accent"], linewidth=2.0, label="Readiness (1-10)")
    
    ax1.axvline(0, color="black", linestyle="--", linewidth=1.5, label="Injury Report Day (Day 0)")
    ax1.set_title("Athlete Wellness Trajectories Surrounding Reported Injury Events", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Days Relative to Injury Report (Day 0)", fontweight="bold")
    ax1.set_ylabel("Subjective Score (1-10 Scale)", fontweight="bold")
    ax1.legend(loc="best", frameon=True)
    ax1.set_xticks(range(-14, 4, 2))
    
    plt.tight_layout()
    plt.savefig("results/figures/fig5_soreness_fatigue_trajectory.png")
    plt.close()

    print("Generating Figure 6: Sleep Distributions Before Injury...")
    # ==========================================
    # FIGURE 6: Sleep Distributions
    # ==========================================
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    sleep_df = df[["sleep_duration", "sleep_quality", "injury_next_7_days"]].dropna()
    sleep_df["Status"] = sleep_df["injury_next_7_days"].map({0: "Healthy Baseline", 1: "Pre-Injury (7d)"})
    
    sns.kdeplot(
        data=sleep_df,
        x="sleep_duration",
        hue="Status",
        common_norm=False,
        fill=True,
        alpha=0.3,
        palette=[PALETTE["healthy"], PALETTE["danger"]],
        ax=axes[0]
    )
    axes[0].set_title("Sleep Duration Distribution (Hours)", fontweight="bold", fontsize=11)
    axes[0].set_xlabel("Sleep Duration (Hours)", fontweight="bold")
    axes[0].set_ylabel("Density", fontweight="bold")
    
    sns.boxplot(
        data=sleep_df,
        x="Status",
        y="sleep_quality",
        palette=[PALETTE["healthy"], PALETTE["danger"]],
        width=0.4,
        ax=axes[1]
    )
    axes[1].set_title("Sleep Quality Distribution (1-10 Scale)", fontweight="bold", fontsize=11)
    axes[1].set_ylabel("Sleep Quality Rating", fontweight="bold")
    axes[1].set_xlabel("")
    
    plt.tight_layout()
    plt.savefig("results/figures/fig6_sleep_pre_injury.png")
    plt.close()

    # ==========================================
    # TRAIN MODELS & EVALUATE
    # ==========================================
    print("Training ML models and evaluating curves...")
    pipeline_artifacts = run_full_training_pipeline(seed=42)
    models = pipeline_artifacts["models"]
    X_test = pipeline_artifacts["X_test"]
    X_test_scaled = pipeline_artifacts["X_test_scaled"]
    y_test = pipeline_artifacts["y_test"]
    
    # 7. ROC Curves
    fig, ax = plt.subplots(figsize=(8, 6))
    for name, model in models.items():
        is_linear = "Logistic" in name
        X = X_test_scaled if is_linear else X_test
        probs = model.predict_proba(X)[:, 1]
        fpr, tpr, _ = roc_curve(y_test, probs)
        roc_val = auc(fpr, tpr)
        ax.plot(fpr, tpr, linewidth=2.0, label=f"{name} (AUC = {roc_val:.3f})")
        
    ax.plot([0, 1], [0, 1], "k--", alpha=0.5, label="Random Guess (AUC = 0.500)")
    ax.set_title("Receiver Operating Characteristic (ROC) - Test Set", fontsize=12, fontweight="bold")
    ax.set_xlabel("False Positive Rate (1 - Specificity)", fontweight="bold")
    ax.set_ylabel("True Positive Rate (Sensitivity / Recall)", fontweight="bold")
    ax.legend(loc="lower right", frameon=True)
    plt.tight_layout()
    plt.savefig("results/figures/fig7_model_roc_curves.png")
    plt.close()

    # 8. Precision-Recall Curves
    fig, ax = plt.subplots(figsize=(8, 6))
    prevalence = np.mean(y_test)
    for name, model in models.items():
        is_linear = "Logistic" in name
        X = X_test_scaled if is_linear else X_test
        probs = model.predict_proba(X)[:, 1]
        prec, rec, _ = precision_recall_curve(y_test, probs)
        ap = average_precision_score(y_test, probs)
        ax.plot(rec, prec, linewidth=2.0, label=f"{name} (PR-AUC = {ap:.4f})")
        
    ax.axhline(prevalence, color="k", linestyle="--", alpha=0.5, label=f"Baseline Prevalence ({prevalence:.3%})")
    ax.set_title("Precision-Recall Curves - Test Set (Imbalanced Setting)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Recall (Sensitivity)", fontweight="bold")
    ax.set_ylabel("Precision (Positive Predictive Value)", fontweight="bold")
    ax.legend(loc="upper right", frameon=True)
    plt.tight_layout()
    plt.savefig("results/figures/fig8_model_pr_curves.png")
    plt.close()

    # 9. Calibration Curves
    fig, ax = plt.subplots(figsize=(8, 6))
    for name, model in models.items():
        is_linear = "Logistic" in name
        X = X_test_scaled if is_linear else X_test
        probs = model.predict_proba(X)[:, 1]
        prob_true, prob_pred = calibration_curve(y_test, probs, n_bins=10, strategy="quantile")
        ax.plot(prob_pred, prob_true, marker="o", linewidth=1.8, label=name)
        
    ax.plot([0, 1], [0, 1], "k--", alpha=0.5, label="Perfect Calibration")
    ax.set_title("Reliability Diagram / Calibration Curves - Test Set", fontsize=12, fontweight="bold")
    ax.set_xlabel("Mean Predicted Probability", fontweight="bold")
    ax.set_ylabel("Observed Empirical Frequency", fontweight="bold")
    ax.legend(loc="upper left", frameon=True)
    plt.tight_layout()
    plt.savefig("results/figures/fig9_calibration_curves.png")
    plt.close()

    # 10. Readiness Regression Plot
    print("Generating Figure 10: Readiness Prediction Scatter...")
    r_model = pipeline_artifacts["readiness_models"]["XGBoost Regressor"]
    val_df = pipeline_artifacts["val_df"]
    feature_cols = pipeline_artifacts["feature_cols"]
    imputer = pipeline_artifacts["imputer"]
    X_val = imputer.transform(val_df[feature_cols].values)
    y_val_r = val_df["readiness_next_day"].values
    
    val_mask = ~np.isnan(y_val_r)
    y_true_v = y_val_r[val_mask]
    y_pred_v = r_model.predict(X_val[val_mask])
    
    fig, ax = plt.subplots(figsize=(7, 6))
    sns.regplot(x=y_true_v, y=y_pred_v, scatter_kws={"alpha": 0.25, "color": PALETTE["primary"]}, line_kws={"color": PALETTE["danger"], "linewidth": 2.0}, ax=ax)
    ax.plot([1, 10], [1, 10], "k--", alpha=0.6, label="Ideal 1:1 Reference Line")
    ax.set_title("Secondary Task: Next-Day Athlete Readiness Prediction", fontsize=12, fontweight="bold")
    ax.set_xlabel("Actual Next-Day Readiness (1-10)", fontweight="bold")
    ax.set_ylabel("Predicted Readiness Score", fontweight="bold")
    ax.legend(loc="upper left", frameon=True)
    plt.tight_layout()
    plt.savefig("results/figures/fig10_readiness_prediction.png")
    plt.close()

    # ==========================================
    # SHAP EXPLAINABILITY
    # ==========================================
    print("Computing SHAP explanations with TreeExplainer...")
    xgb_model = models["XGBoost"]
    feature_names = pipeline_artifacts["feature_cols"]
    
    explainer = shap.TreeExplainer(xgb_model)
    shap_values = explainer(X_test)
    shap_values.feature_names = feature_names
    
    # 11. SHAP Summary Beeswarm
    fig, ax = plt.subplots(figsize=(10, 8))
    shap.summary_plot(shap_values, X_test, feature_names=feature_names, max_display=15, show=False)
    plt.title("Global TreeSHAP Summary Plot (Top 15 Workload & Wellness Drivers)", fontsize=12, fontweight="bold", pad=15)
    plt.tight_layout()
    plt.savefig("results/figures/fig11_shap_summary.png")
    plt.close()

    # 12. SHAP Bar Plot (Mean |SHAP|)
    fig, ax = plt.subplots(figsize=(9, 6))
    mean_abs_shap = np.mean(np.abs(shap_values.values), axis=0)
    top_indices = np.argsort(mean_abs_shap)[::-1][:15]
    top_features = [feature_names[i] for i in top_indices]
    top_values = mean_abs_shap[top_indices]
    
    sns.barplot(x=top_values, y=top_features, palette="mako", ax=ax)
    ax.set_title("Global Feature Importance (Mean |SHAP Value|)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Mean Absolute SHAP Value", fontweight="bold")
    ax.set_ylabel("Feature", fontweight="bold")
    plt.tight_layout()
    plt.savefig("results/figures/fig12_shap_importance_bar.png")
    plt.close()

    # 13 & 14. Individual Waterfall Plots
    test_probs = xgb_model.predict_proba(X_test)[:, 1]
    high_risk_idx = np.argmax(test_probs)
    low_risk_idx = np.argmin(test_probs)
    
    # High risk waterfall
    fig, ax = plt.subplots(figsize=(9, 6))
    shap.plots.waterfall(shap_values[high_risk_idx], max_display=10, show=False)
    plt.title(f"Individual Case Study: Elevated-Risk Athlete-Day (Predicted Risk: {test_probs[high_risk_idx]:.1%})", fontsize=11, fontweight="bold", pad=15)
    plt.tight_layout()
    plt.savefig("results/figures/fig13_shap_waterfall_high_risk.png")
    plt.close()

    # Low risk waterfall
    fig, ax = plt.subplots(figsize=(9, 6))
    shap.plots.waterfall(shap_values[low_risk_idx], max_display=10, show=False)
    plt.title(f"Individual Case Study: Low-Risk Athlete-Day (Predicted Risk: {test_probs[low_risk_idx]:.1%})", fontsize=11, fontweight="bold", pad=15)
    plt.tight_layout()
    plt.savefig("results/figures/fig14_shap_waterfall_low_risk.png")
    plt.close()

    print("All figures successfully generated in results/figures/.")

if __name__ == "__main__":
    generate_all_figures()
