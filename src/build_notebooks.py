import os
import nbformat as nbf

def build_all_notebooks():
    os.makedirs("notebooks", exist_ok=True)
    
    # Common preamble for robust path handling
    preamble = (
        "import os\n"
        "import sys\n"
        "# Ensure parent directory is in python path\n"
        "if os.path.abspath('..') not in sys.path:\n"
        "    sys.path.insert(0, os.path.abspath('..'))\n\n"
        "def get_path(rel_path):\n"
        "    if os.path.exists(rel_path):\n"
        "        return rel_path\n"
        "    elif os.path.exists(os.path.join('..', rel_path)):\n"
        "        return os.path.join('..', rel_path)\n"
        "    return rel_path\n"
    )
    
    # -------------------------------------------------------------------
    # NOTEBOOK 1: EDA
    # -------------------------------------------------------------------
    nb1 = nbf.v4.new_notebook()
    nb1.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb1.cells = [
        nbf.v4.new_markdown_cell(
            "# AthleteLoad: 01. Exploratory Data Analysis\n\n"
            "This notebook explores longitudinal athlete monitoring data from the SoccerMon dataset. "
            "We analyze subjective training load, daily wellness questionnaires, and injury report distributions across two elite women's football teams over two seasons (2020 and 2021)."
        ),
        nbf.v4.new_code_cell(
            preamble + "\n"
            "import json\n"
            "import pandas as pd\n"
            "import numpy as np\n"
            "import matplotlib.pyplot as plt\n"
            "import seaborn as sns\n\n"
            "from src.utils import setup_plotting_style, PALETTE\n"
            "setup_plotting_style()\n\n"
            "df = pd.read_csv(get_path('data/processed/player_daily_features.csv'))\n"
            "df['date'] = pd.to_datetime(df['date'])\n"
            "print(f'Dataset Shape: {df.shape[0]:,} player-days across {df[\"player_id\"].nunique()} athletes.')\n"
            "print(f'Date Range: {df[\"date\"].min().date()} to {df[\"date\"].max().date()}')\n"
            "print(f'Total Reported Injury Days: {df[\"injury_reported\"].sum()}')\n"
            "print(f'Total 7-Day Pre-Injury Windows: {df[\"injury_next_7_days\"].sum()} ({df[\"injury_next_7_days\"].mean():.2%})')"
        ),
        nbf.v4.new_markdown_cell("## 1. Reported Injuries by Anatomical Location & Severity"),
        nbf.v4.new_code_cell(
            "inj_raw = pd.read_csv(get_path('data/raw/subjective/injury/injury.csv'))\n"
            "locations_list = []\n"
            "for s in inj_raw['type']:\n"
            "    try:\n"
            "        d = json.loads(s)\n"
            "        for loc, sev in d.items():\n"
            "            locations_list.append({'location': loc.replace('_', ' ').title(), 'severity': sev.capitalize()})\n"
            "    except Exception:\n"
            "        pass\n"
            "inj_loc_df = pd.DataFrame(locations_list)\n\n"
            "fig, axes = plt.subplots(1, 2, figsize=(13, 5))\n"
            "loc_counts = inj_loc_df['location'].value_counts().head(8)\n"
            "sns.barplot(x=loc_counts.values, y=loc_counts.index, ax=axes[0], palette='Blues_r', hue=loc_counts.index, legend=False)\n"
            "axes[0].set_title('Reported Injuries by Anatomical Location', fontsize=12, fontweight='bold')\n"
            "axes[0].set_xlabel('Number of Reports', fontweight='bold')\n"
            "axes[0].set_ylabel('Anatomical Location', fontweight='bold')\n\n"
            "sev_df = inj_loc_df.groupby(['location', 'severity']).size().unstack(fill_value=0)\n"
            "sev_df['total'] = sev_df.sum(axis=1)\n"
            "sev_top = sev_df.sort_values('total', ascending=False).head(8).drop(columns=['total'])\n"
            "sev_top.plot(kind='barh', stacked=True, ax=axes[1], color=[PALETTE['healthy'], PALETTE['danger']], edgecolor='black', linewidth=0.5)\n"
            "axes[1].set_title('Injury Severity Proportion by Location', fontsize=12, fontweight='bold')\n"
            "axes[1].set_xlabel('Number of Reports', fontweight='bold')\n"
            "axes[1].set_ylabel('')\n"
            "plt.tight_layout()\n"
            "plt.show()"
        ),
        nbf.v4.new_markdown_cell("## 2. Longitudinal Athlete Training Load Trajectories"),
        nbf.v4.new_code_cell(
            "sample_pid = 'TeamA-5cd7a61b-88b2-46d2-94f8-5a0d4f682d93'\n"
            "p_df = df[df['player_id'] == sample_pid].sort_values('date').copy()\n\n"
            "fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), sharex=True, gridspec_kw={'height_ratios': [2.2, 1.2]})\n"
            "ax1.bar(p_df['date'], p_df['daily_load'], color='#bdc3c7', alpha=0.5, label='Daily Load (sRPE)', width=1.0)\n"
            "ax1.plot(p_df['date'], p_df['atl_7d'], color=PALETTE['primary'], linewidth=2.0, label='ATL (7-day Acute Load)')\n"
            "ax1.plot(p_df['date'], p_df['ctl_28d'] * 7, color=PALETTE['accent'], linewidth=2.0, label='CTL (28-day Chronic Load x 7)')\n\n"
            "inj_dates = p_df[p_df['injury_reported'] == 1]['date']\n"
            "for idt in inj_dates:\n"
            "    ax1.axvline(idt, color=PALETTE['danger'], linestyle='--', linewidth=1.5, alpha=0.8)\n"
            "if len(inj_dates) > 0:\n"
            "    ax1.plot([], [], color=PALETTE['danger'], linestyle='--', label='Reported Injury Event')\n\n"
            "ax1.set_title(f'Longitudinal Workload Trajectory and Injury Events (Athlete: {sample_pid[:12]})', fontsize=12, fontweight='bold')\n"
            "ax1.set_ylabel('Workload (sRPE Units)', fontweight='bold')\n"
            "ax1.legend(loc='upper right', frameon=True)\n\n"
            "ax2.plot(p_df['date'], p_df['acwr_calc'], color=PALETTE['secondary'], linewidth=1.8, label='Calculated ACWR (7:28)')\n"
            "ax2.axhspan(0.8, 1.3, color='#2ecc71', alpha=0.2, label=\"Optimal 'Sweet Spot' (0.8 - 1.3)\")\n"
            "ax2.axhline(1.5, color=PALETTE['danger'], linestyle=':', linewidth=1.5, label='High Risk Threshold (> 1.5)')\n"
            "ax2.set_ylim(0, 3.0)\n"
            "ax2.set_ylabel('ACWR', fontweight='bold')\n"
            "ax2.set_xlabel('Date', fontweight='bold')\n"
            "ax2.legend(loc='upper right', frameon=True)\n"
            "plt.tight_layout()\n"
            "plt.show()"
        ),
        nbf.v4.new_markdown_cell("## 3. Wellness & Workload Correlation Heatmap"),
        nbf.v4.new_code_cell(
            "corr_cols = ['fatigue', 'soreness', 'mood', 'readiness', 'sleep_duration', 'sleep_quality', 'stress', 'atl', 'acwr']\n"
            "corr_labels = ['Fatigue', 'Soreness', 'Mood', 'Readiness', 'Sleep Dur', 'Sleep Qual', 'Stress', 'ATL', 'ACWR']\n"
            "corr_mat = df[corr_cols].corr()\n\n"
            "fig, ax = plt.subplots(figsize=(9, 7))\n"
            "mask = np.triu(np.ones_like(corr_mat, dtype=bool))\n"
            "sns.heatmap(\n"
            "    corr_mat, mask=mask, annot=True, fmt='.2f', cmap='vlag', vmin=-1, vmax=1,\n"
            "    square=True, linewidths=0.5, cbar_kws={'shrink': 0.8, 'label': 'Pearson Correlation'},\n"
            "    xticklabels=corr_labels, yticklabels=corr_labels, ax=ax\n"
            ")\n"
            "ax.set_title('Correlation Matrix of Athlete Wellness and Workload Metrics', fontsize=12, fontweight='bold')\n"
            "plt.tight_layout()\n"
            "plt.show()"
        ),
        nbf.v4.new_markdown_cell("## 4. Pre-Injury vs Baseline Workload & Wellness Comparisons"),
        nbf.v4.new_code_cell(
            "fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))\n"
            "metrics_to_plot = [\n"
            "    ('atl', 'Acute Training Load (ATL)', 'sRPE units'),\n"
            "    ('acwr', 'Acute:Chronic Ratio (ACWR)', 'Ratio'),\n"
            "    ('load_7d_sum', '7-Day Load Sum', 'sRPE units')\n"
            "]\n"
            "for i, (col, title, unit) in enumerate(metrics_to_plot):\n"
            "    valid = df[[col, 'injury_next_7_days']].dropna().copy()\n"
            "    valid['Status'] = valid['injury_next_7_days'].map({0: 'Healthy Baseline', 1: 'Pre-Injury (7d)'})\n"
            "    sns.boxplot(x='Status', y=col, data=valid, ax=axes[i], palette=[PALETTE['healthy'], PALETTE['danger']], showfliers=False, width=0.45, hue='Status', legend=False)\n"
            "    axes[i].set_title(title, fontweight='bold', fontsize=11)\n"
            "    axes[i].set_ylabel(unit, fontweight='bold')\n"
            "    axes[i].set_xlabel('')\n"
            "plt.tight_layout()\n"
            "plt.show()"
        )
    ]
    with open("notebooks/01_eda.ipynb", "w") as f:
        nbf.write(nb1, f)

    # -------------------------------------------------------------------
    # NOTEBOOK 2: Baseline Modeling
    # -------------------------------------------------------------------
    nb2 = nbf.v4.new_notebook()
    nb2.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb2.cells = [
        nbf.v4.new_markdown_cell(
            "# AthleteLoad: 02. Interpretable Baseline Modeling\n\n"
            "This notebook establishes an interpretable linear baseline using Logistic Regression with balanced class weights on a strictly chronological train/validation/test split."
        ),
        nbf.v4.new_code_cell(
            preamble + "\n"
            "import pandas as pd\n"
            "import numpy as np\n"
            "import matplotlib.pyplot as plt\n"
            "import seaborn as sns\n"
            "from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, average_precision_score\n\n"
            "from src.utils import setup_plotting_style, PALETTE\n"
            "from src.train import run_full_training_pipeline\n"
            "from src.evaluate import evaluate_binary_model, find_optimal_threshold\n"
            "setup_plotting_style()\n\n"
            "artifacts = run_full_training_pipeline(data_path=get_path('data/processed/player_daily_features.csv'), seed=42)\n"
            "lr_model = artifacts['models']['Logistic Regression']\n"
            "feature_cols = artifacts['feature_cols']\n"
            "X_val_scaled = artifacts['X_val_scaled']\n"
            "y_val = artifacts['y_val']\n"
            "X_test_scaled = artifacts['X_test_scaled']\n"
            "y_test = artifacts['y_test']\n"
            "print('Logistic Regression Model Loaded.')"
        ),
        nbf.v4.new_markdown_cell("## 1. Standardized Coefficients"),
        nbf.v4.new_code_cell(
            "coefs = lr_model.coef_[0]\n"
            "coef_df = pd.DataFrame({\n"
            "    'feature': feature_cols,\n"
            "    'coefficient': coefs,\n"
            "    'abs_coef': np.abs(coefs)\n"
            "}).sort_values('abs_coef', ascending=False)\n\n"
            "print('Top 10 Influential Features in Logistic Baseline:')\n"
            "display(coef_df.head(10))\n\n"
            "plt.figure(figsize=(10, 6))\n"
            "top_coefs = pd.concat([coef_df[coef_df['coefficient'] > 0].head(7), coef_df[coef_df['coefficient'] < 0].head(7)]).sort_values('coefficient')\n"
            "colors = [PALETTE['healthy'] if c < 0 else PALETTE['danger'] for c in top_coefs['coefficient']]\n"
            "sns.barplot(x='coefficient', y='feature', data=top_coefs, palette=colors, hue='feature', legend=False)\n"
            "plt.title('Logistic Regression Standardized Coefficients (Top Risk vs Protective Factors)', fontsize=12, fontweight='bold')\n"
            "plt.xlabel('Standardized Coefficient (Log Odds)', fontweight='bold')\n"
            "plt.ylabel('Feature', fontweight='bold')\n"
            "plt.axvline(0, color='black', linestyle='--', linewidth=0.8)\n"
            "plt.tight_layout()\n"
            "plt.show()"
        ),
        nbf.v4.new_markdown_cell("## 2. Evaluation on Test Partition"),
        nbf.v4.new_code_cell(
            "val_probs = lr_model.predict_proba(X_val_scaled)[:, 1]\n"
            "best_thresh, _ = find_optimal_threshold(y_val, val_probs)\n"
            "print(f'Optimal Validation Threshold: {best_thresh:.3f}')\n\n"
            "val_res = evaluate_binary_model(lr_model, X_val_scaled, y_val, threshold=best_thresh)\n"
            "test_res = evaluate_binary_model(lr_model, X_test_scaled, y_test, threshold=best_thresh)\n\n"
            "print(f'Validation: PR-AUC = {val_res[\"pr_auc\"]:.4f} | ROC-AUC = {val_res[\"roc_auc\"]:.4f} | Recall = {val_res[\"recall\"]:.3f} | Prec = {val_res[\"precision\"]:.3f} | F1 = {val_res[\"f1\"]:.3f}')\n"
            "print(f'Test:       PR-AUC = {test_res[\"pr_auc\"]:.4f} | ROC-AUC = {test_res[\"roc_auc\"]:.4f} | Recall = {test_res[\"recall\"]:.3f} | Prec = {test_res[\"precision\"]:.3f} | F1 = {test_res[\"f1\"]:.3f}')\n\n"
            "cm = np.array(test_res['confusion_matrix'])\n"
            "plt.figure(figsize=(5, 4))\n"
            "sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False, xticklabels=['Pred Healthy', 'Pred Injury (7d)'], yticklabels=['Actual Healthy', 'Actual Injury (7d)'])\n"
            "plt.title('Test Set Confusion Matrix (Logistic Regression)', fontweight='bold')\n"
            "plt.show()"
        )
    ]
    with open("notebooks/02_baseline.ipynb", "w") as f:
        nbf.write(nb2, f)

    # -------------------------------------------------------------------
    # NOTEBOOK 3: Model Evaluation
    # -------------------------------------------------------------------
    nb3 = nbf.v4.new_notebook()
    nb3.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb3.cells = [
        nbf.v4.new_markdown_cell(
            "# AthleteLoad: 03. Model Evaluation & Benchmark Comparison\n\n"
            "This notebook compares Logistic Regression, Random Forest, XGBoost, and LightGBM across temporal validation and test partitions. "
            "We also evaluate the secondary objective: next-day athlete readiness score prediction."
        ),
        nbf.v4.new_code_cell(
            preamble + "\n"
            "import pandas as pd\n"
            "import numpy as np\n"
            "import matplotlib.pyplot as plt\n"
            "import seaborn as sns\n"
            "from sklearn.metrics import roc_curve, precision_recall_curve, auc, average_precision_score\n\n"
            "from src.utils import setup_plotting_style, PALETTE\n"
            "from src.train import run_full_training_pipeline\n"
            "from src.evaluate import run_model_comparison\n"
            "setup_plotting_style()\n\n"
            "artifacts = run_full_training_pipeline(data_path=get_path('data/processed/player_daily_features.csv'), seed=42)\n"
            "comp_df = run_model_comparison(artifacts)\n"
            "display(comp_df)"
        ),
        nbf.v4.new_markdown_cell("## 1. Test Set ROC & Precision-Recall Curves"),
        nbf.v4.new_code_cell(
            "models = artifacts['models']\n"
            "X_test = artifacts['X_test']\n"
            "X_test_scaled = artifacts['X_test_scaled']\n"
            "y_test = artifacts['y_test']\n\n"
            "fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))\n\n"
            "for name, model in models.items():\n"
            "    X = X_test_scaled if 'Logistic' in name else X_test\n"
            "    probs = model.predict_proba(X)[:, 1]\n"
            "    fpr, tpr, _ = roc_curve(y_test, probs)\n"
            "    roc_val = auc(fpr, tpr)\n"
            "    axes[0].plot(fpr, tpr, linewidth=2.0, label=f'{name} ({roc_val:.3f})')\n"
            "axes[0].plot([0, 1], [0, 1], 'k--', alpha=0.5, label='Random Guess')\n"
            "axes[0].set_title('Test Set ROC Curves', fontsize=12, fontweight='bold')\n"
            "axes[0].set_xlabel('False Positive Rate', fontweight='bold')\n"
            "axes[0].set_ylabel('True Positive Rate (Recall)', fontweight='bold')\n"
            "axes[0].legend(loc='lower right', frameon=True)\n\n"
            "prevalence = np.mean(y_test)\n"
            "for name, model in models.items():\n"
            "    X = X_test_scaled if 'Logistic' in name else X_test\n"
            "    probs = model.predict_proba(X)[:, 1]\n"
            "    prec, rec, _ = precision_recall_curve(y_test, probs)\n"
            "    ap = average_precision_score(y_test, probs)\n"
            "    axes[1].plot(rec, prec, linewidth=2.0, label=f'{name} (PR-AUC={ap:.4f})')\n"
            "axes[1].axhline(prevalence, color='k', linestyle='--', alpha=0.5, label=f'Prevalence ({prevalence:.2%})')\n"
            "axes[1].set_title('Test Set Precision-Recall Curves', fontsize=12, fontweight='bold')\n"
            "axes[1].set_xlabel('Recall (Sensitivity)', fontweight='bold')\n"
            "axes[1].set_ylabel('Precision (PPV)', fontweight='bold')\n"
            "axes[1].legend(loc='upper right', frameon=True)\n\n"
            "plt.tight_layout()\n"
            "plt.show()"
        ),
        nbf.v4.new_markdown_cell("## 2. Secondary Task: Next-Day Readiness Prediction"),
        nbf.v4.new_code_cell(
            "r_model = artifacts['readiness_models']['XGBoost Regressor']\n"
            "val_df = artifacts['val_df']\n"
            "feature_cols = artifacts['feature_cols']\n"
            "imputer = artifacts['imputer']\n"
            "X_val = imputer.transform(val_df[feature_cols].values)\n"
            "y_val_r = val_df['readiness_next_day'].values\n\n"
            "val_mask = ~np.isnan(y_val_r)\n"
            "y_true_v = y_val_r[val_mask]\n"
            "y_pred_v = r_model.predict(X_val[val_mask])\n\n"
            "plt.figure(figsize=(7, 6))\n"
            "sns.regplot(x=y_true_v, y=y_pred_v, scatter_kws={'alpha': 0.25, 'color': PALETTE['primary']}, line_kws={'color': PALETTE['danger'], 'linewidth': 2.0})\n"
            "plt.plot([1, 10], [1, 10], 'k--', alpha=0.6, label='Ideal 1:1 Reference')\n"
            "plt.title('Next-Day Athlete Readiness Prediction (XGBoost Regressor)', fontsize=12, fontweight='bold')\n"
            "plt.xlabel('Actual Next-Day Readiness (1-10)', fontweight='bold')\n"
            "plt.ylabel('Predicted Readiness Score', fontweight='bold')\n"
            "plt.legend(loc='upper left', frameon=True)\n"
            "plt.tight_layout()\n"
            "plt.show()"
        )
    ]
    with open("notebooks/03_model_evaluation.ipynb", "w") as f:
        nbf.write(nb3, f)

    # -------------------------------------------------------------------
    # NOTEBOOK 4: Explainability
    # -------------------------------------------------------------------
    nb4 = nbf.v4.new_notebook()
    nb4.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb4.cells = [
        nbf.v4.new_markdown_cell(
            "# AthleteLoad: 04. Model Explainability & SHAP Analysis\n\n"
            "This notebook uses TreeSHAP to interpret the decisions of our XGBoost model. "
            "We examine global feature importances, feature impact beeswarm plots, and local waterfall explanations for individual athlete-days."
        ),
        nbf.v4.new_code_cell(
            preamble + "\n"
            "import pandas as pd\n"
            "import numpy as np\n"
            "import matplotlib.pyplot as plt\n"
            "import seaborn as sns\n"
            "import shap\n\n"
            "from src.utils import setup_plotting_style, PALETTE\n"
            "from src.train import run_full_training_pipeline\n"
            "setup_plotting_style()\n\n"
            "artifacts = run_full_training_pipeline(data_path=get_path('data/processed/player_daily_features.csv'), seed=42)\n"
            "xgb_model = artifacts['models']['XGBoost']\n"
            "feature_names = artifacts['feature_cols']\n"
            "X_test = artifacts['X_test']\n"
            "y_test = artifacts['y_test']\n\n"
            "explainer = shap.TreeExplainer(xgb_model)\n"
            "shap_values = explainer(X_test)\n"
            "shap_values.feature_names = feature_names\n"
            "print('TreeSHAP values computed successfully on test partition.')"
        ),
        nbf.v4.new_markdown_cell("## 1. Global TreeSHAP Summary (Beeswarm Plot)"),
        nbf.v4.new_code_cell(
            "plt.figure(figsize=(10, 8))\n"
            "shap.summary_plot(shap_values, X_test, feature_names=feature_names, max_display=15, show=False)\n"
            "plt.title('Global TreeSHAP Summary Plot (Top 15 Workload & Wellness Drivers)', fontsize=12, fontweight='bold', pad=15)\n"
            "plt.tight_layout()\n"
            "plt.show()"
        ),
        nbf.v4.new_markdown_cell("## 2. Mean Absolute SHAP Importance Ranking"),
        nbf.v4.new_code_cell(
            "mean_abs_shap = np.mean(np.abs(shap_values.values), axis=0)\n"
            "top_indices = np.argsort(mean_abs_shap)[::-1][:15]\n"
            "top_features = [feature_names[i] for i in top_indices]\n"
            "top_values = mean_abs_shap[top_indices]\n\n"
            "plt.figure(figsize=(9, 6))\n"
            "sns.barplot(x=top_values, y=top_features, palette='mako', hue=top_features, legend=False)\n"
            "plt.title('Global Feature Importance Ranking (Mean |SHAP Value|)', fontsize=12, fontweight='bold')\n"
            "plt.xlabel('Mean Absolute SHAP Value', fontweight='bold')\n"
            "plt.ylabel('Feature', fontweight='bold')\n"
            "plt.tight_layout()\n"
            "plt.show()"
        ),
        nbf.v4.new_markdown_cell("## 3. Individual Athlete-Day Case Studies (Waterfall Explanations)"),
        nbf.v4.new_code_cell(
            "test_probs = xgb_model.predict_proba(X_test)[:, 1]\n"
            "high_risk_idx = np.argmax(test_probs)\n"
            "low_risk_idx = np.argmin(test_probs)\n\n"
            "print(f'High-Risk Athlete-Day: Index {high_risk_idx} | Predicted Probability: {test_probs[high_risk_idx]:.1%}')\n"
            "print(f'Low-Risk Athlete-Day:  Index {low_risk_idx} | Predicted Probability: {test_probs[low_risk_idx]:.1%}')\n\n"
            "plt.figure(figsize=(9, 6))\n"
            "shap.plots.waterfall(shap_values[high_risk_idx], max_display=10, show=False)\n"
            "plt.title(f'Case Study: Elevated-Risk Athlete-Day (Risk = {test_probs[high_risk_idx]:.1%})', fontsize=11, fontweight='bold', pad=15)\n"
            "plt.tight_layout()\n"
            "plt.show()\n\n"
            "plt.figure(figsize=(9, 6))\n"
            "shap.plots.waterfall(shap_values[low_risk_idx], max_display=10, show=False)\n"
            "plt.title(f'Case Study: Low-Risk Athlete-Day (Risk = {test_probs[low_risk_idx]:.1%})', fontsize=11, fontweight='bold', pad=15)\n"
            "plt.tight_layout()\n"
            "plt.show()"
        )
    ]
    with open("notebooks/04_explainability.ipynb", "w") as f:
        nbf.write(nb4, f)
    print("All 4 notebooks written successfully.")

if __name__ == "__main__":
    build_all_notebooks()
