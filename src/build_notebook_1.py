import os
import nbformat as nbf

def create_notebook_1_eda():
    nb = nbf.v4.new_notebook()
    nb.metadata["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3"
    }
    
    cells = []
    
    cells.append(nbf.v4.new_markdown_cell(
        "# AthleteLoad: 01. Exploratory Data Analysis\n\n"
        "This notebook explores longitudinal athlete monitoring data from the SoccerMon dataset. "
        "We analyze subjective training load, daily wellness questionnaires, and injury report distributions across two elite women's football teams over two seasons (2020 and 2021)."
    ))
    
    cells.append(nbf.v4.new_code_cell(
        "import os\n"
        "import json\n"
        "import pandas as pd\n"
        "import numpy as np\n"
        "import matplotlib.pyplot as plt\n"
        "import seaborn as sns\n\n"
        "from src.utils import setup_plotting_style, PALETTE\n"
        "setup_plotting_style()\n\n"
        "# Load feature-enriched dataset\n"
        "df = pd.read_csv('../data/processed/player_daily_features.csv')\n"
        "df['date'] = pd.to_datetime(df['date'])\n"
        "print(f'Dataset Shape: {df.shape[0]:,} player-days across {df[\"player_id\"].nunique()} athletes.')\n"
        "print(f'Date Range: {df[\"date\"].min().date()} to {df[\"date\"].max().date()}')\n"
        "print(f'Total Reported Injury Days: {df[\"injury_reported\"].sum()}')\n"
        "print(f'Total 7-Day Pre-Injury Windows: {df[\"injury_next_7_days\"].sum()} ({df[\"injury_next_7_days\"].mean():.2%})')"
    ))
    
    cells.append(nbf.v4.new_markdown_cell(
        "## 1. Injury Report Distribution\n\n"
        "We analyze the anatomical locations and severity breakdown of player-reported injuries."
    ))
    
    cells.append(nbf.v4.new_code_cell(
        "inj_raw = pd.read_csv('../data/raw/subjective/injury/injury.csv')\n"
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
    ))
    
    cells.append(nbf.v4.new_markdown_cell(
        "## 2. Longitudinal Athlete Training Load Trajectories\n\n"
        "Examining daily workload, Acute Training Load (ATL, 7d), Chronic Training Load (CTL, 28d), and the Acute:Chronic Workload Ratio (ACWR) for a representative athlete."
    ))
    
    cells.append(nbf.v4.new_code_cell(
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
    ))
    
    cells.append(nbf.v4.new_markdown_cell(
        "## 3. Wellness & Workload Correlation Heatmap"
    ))
    
    cells.append(nbf.v4.new_code_cell(
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
    ))
    
    cells.append(nbf.v4.new_markdown_cell(
        "## 4. Pre-Injury vs Baseline Workload & Wellness Comparisons"
    ))
    
    cells.append(nbf.v4.new_code_cell(
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
    ))
    
    nb.cells = cells
    with open("notebooks/01_eda.ipynb", "w") as f:
        nbf.write(nb, f)
    print("Created notebooks/01_eda.ipynb")

if __name__ == "__main__":
    create_notebook_1_eda()
