import os
import random
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def set_seed(seed: int = 42) -> None:
    """Set random seed across libraries for reproducible runs."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def ensure_directories() -> None:
    """Ensure all required project output directories exist."""
    directories = [
        'data/raw',
        'data/processed',
        'results/figures',
        'results/metrics',
        'notebooks'
    ]
    for d in directories:
        os.makedirs(d, exist_ok=True)

def setup_plotting_style() -> None:
    """Configure modern, publication-quality plotting styles for figures."""
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    plt.rcParams.update({
        'figure.autolayout': True,
        'figure.dpi': 150,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica', 'sans-serif'],
        'font.family': 'sans-serif',
        'axes.labelsize': 11,
        'axes.labelweight': 'bold',
        'axes.titlesize': 13,
        'axes.titleweight': 'bold',
        'axes.titlepad': 12,
        'axes.edgecolor': '#cccccc',
        'axes.linewidth': 0.8,
        'grid.color': '#e6e6e6',
        'grid.linestyle': '--',
        'grid.alpha': 0.7,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'legend.frameon': True,
        'legend.edgecolor': '#dddddd',
    })

# Curated sports-science color palette
PALETTE = {
    'primary': '#1f77b4',     # Navy / Blue
    'secondary': '#ff7f0e',   # Warm Amber / Orange
    'accent': '#2ca02c',      # Pitch Green
    'danger': '#d62728',      # Injury Red
    'warning': '#e377c2',     # Magenta / Alert
    'neutral_dark': '#2c3e50',
    'neutral_light': '#ecf0f1',
    'injury': '#d9383a',      # High risk / Injury
    'healthy': '#2b8cbe',     # Healthy baseline
    'logistic': '#7f7f7f',
    'rf': '#2ca02c',
    'xgboost': '#ff7f0e',
    'lightgbm': '#1f77b4'
}
