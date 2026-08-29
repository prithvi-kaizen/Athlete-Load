import os
import json
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any, List
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from xgboost import XGBClassifier, XGBRegressor
from lightgbm import LGBMClassifier, LGBMRegressor

from src.features import get_feature_columns, build_feature_pipeline
from src.utils import set_seed

def temporal_train_val_test_split(
    df: pd.DataFrame,
    train_frac: float = 0.70,
    val_frac: float = 0.15,
    date_col: str = "date"
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Partition dataframe chronologically into Train, Validation, and Test sets.
    
    Guarantees:
        max(Train Date) < min(Val Date) and max(Val Date) < min(Test Date)
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    unique_dates = np.sort(df[date_col].unique())
    n_dates = len(unique_dates)
    
    train_end_idx = int(n_dates * train_frac)
    val_end_idx = int(n_dates * (train_frac + val_frac))
    
    train_dates = unique_dates[:train_end_idx]
    val_dates = unique_dates[train_end_idx:val_end_idx]
    test_dates = unique_dates[val_end_idx:]
    
    train_df = df[df[date_col].isin(train_dates)].reset_index(drop=True)
    val_df = df[df[date_col].isin(val_dates)].reset_index(drop=True)
    test_df = df[df[date_col].isin(test_dates)].reset_index(drop=True)
    
    print(f"Chronological Split Summary:")
    print(f"  Train: {train_df[date_col].min().date()} to {train_df[date_col].max().date()} ({len(train_df):,} rows)")
    print(f"  Val:   {val_df[date_col].min().date()} to {val_df[date_col].max().date()} ({len(val_df):,} rows)")
    print(f"  Test:  {test_df[date_col].min().date()} to {test_df[date_col].max().date()} ({len(test_df):,} rows)")
    
    return train_df, val_df, test_df


def fit_preprocessors(
    train_df: pd.DataFrame,
    feature_cols: List[str]
) -> Tuple[SimpleImputer, StandardScaler]:
    """Fit imputer and standard scaler strictly on training partition."""
    imputer = SimpleImputer(strategy="median")
    X_train_raw = train_df[feature_cols].values
    X_train_imp = imputer.fit_transform(X_train_raw)
    
    scaler = StandardScaler()
    scaler.fit(X_train_imp)
    
    return imputer, scaler


def train_injury_models(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_train_scaled: np.ndarray,
    scale_pos_weight: float,
    seed: int = 42
) -> Dict[str, Any]:
    """Train benchmark injury risk classification models."""
    set_seed(seed)
    
    models = {}
    
    # 1. Logistic Regression Baseline
    print("Training Logistic Regression...")
    lr = LogisticRegression(
        C=0.1,
        class_weight="balanced",
        max_iter=1000,
        random_state=seed,
        solver="lbfgs"
    )
    lr.fit(X_train_scaled, y_train)
    models["Logistic Regression"] = lr
    
    # 2. Random Forest Classifier
    print("Training Random Forest...")
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=5,
        min_samples_split=10,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=seed,
        n_jobs=-1
    )
    rf.fit(X_train, y_train)
    models["Random Forest"] = rf
    
    # 3. XGBoost Classifier
    print("Training XGBoost...")
    xgb = XGBClassifier(
        n_estimators=200,
        max_depth=3,
        learning_rate=0.03,
        scale_pos_weight=scale_pos_weight,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        random_state=seed,
        n_jobs=-1,
        eval_metric="logloss"
    )
    xgb.fit(X_train, y_train)
    models["XGBoost"] = xgb
    
    # 4. LightGBM Classifier
    print("Training LightGBM...")
    lgb = LGBMClassifier(
        n_estimators=200,
        max_depth=3,
        learning_rate=0.03,
        scale_pos_weight=scale_pos_weight,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_samples=10,
        random_state=seed,
        n_jobs=-1,
        verbose=-1
    )
    lgb.fit(X_train, y_train)
    models["LightGBM"] = lgb
    
    return models


def train_readiness_regressors(
    X_train: np.ndarray,
    y_train_readiness: np.ndarray,
    X_train_scaled: np.ndarray,
    seed: int = 42
) -> Dict[str, Any]:
    """Train next-day readiness score regression models."""
    set_seed(seed)
    
    # Drop NaNs from readiness targets
    valid_mask = ~np.isnan(y_train_readiness)
    X_tr = X_train[valid_mask]
    X_tr_sc = X_train_scaled[valid_mask]
    y_tr = y_train_readiness[valid_mask]
    
    models = {}
    
    # 1. Ridge Baseline
    ridge = Ridge(alpha=1.0, random_state=seed)
    ridge.fit(X_tr_sc, y_tr)
    models["Ridge Regression"] = ridge
    
    # 2. XGBoost Regressor
    xgb_reg = XGBRegressor(
        n_estimators=150,
        max_depth=3,
        learning_rate=0.03,
        subsample=0.8,
        random_state=seed,
        n_jobs=-1
    )
    xgb_reg.fit(X_tr, y_tr)
    models["XGBoost Regressor"] = xgb_reg
    
    return models


def run_full_training_pipeline(
    data_path: str = "data/processed/player_daily_features.csv",
    seed: int = 42
) -> Dict[str, Any]:
    """Execute end-to-end model training workflow."""
    if not os.path.exists(data_path):
        from src.data_processing import load_and_preprocess_soccermon
        from src.features import build_feature_pipeline
        df = load_and_preprocess_soccermon()
        df = build_feature_pipeline(df)
        df.to_csv(data_path, index=False)
    else:
        df = pd.read_csv(data_path)
        df["date"] = pd.to_datetime(df["date"])
        
    feature_cols = get_feature_columns()
    train_df, val_df, test_df = temporal_train_val_test_split(df)
    
    imputer, scaler = fit_preprocessors(train_df, feature_cols)
    
    # Transform partitions
    X_train = imputer.transform(train_df[feature_cols].values)
    X_train_scaled = scaler.transform(X_train)
    y_train = train_df["injury_next_7_days"].values
    
    X_val = imputer.transform(val_df[feature_cols].values)
    X_val_scaled = scaler.transform(X_val)
    y_val = val_df["injury_next_7_days"].values
    
    X_test = imputer.transform(test_df[feature_cols].values)
    X_test_scaled = scaler.transform(X_test)
    y_test = test_df["injury_next_7_days"].values
    
    # Positive class weighting for imbalanced injury label
    n_pos = np.sum(y_train == 1)
    n_neg = np.sum(y_train == 0)
    scale_pos_weight = float(n_neg / max(n_pos, 1))
    print(f"\nTraining Class Balance: {n_pos:,} Positives, {n_neg:,} Negatives (Ratio: {scale_pos_weight:.1f}:1)")
    
    # Train injury classification models
    models = train_injury_models(X_train, y_train, X_train_scaled, scale_pos_weight, seed=seed)
    
    # Train secondary readiness regression models
    readiness_models = train_readiness_regressors(
        X_train,
        train_df["readiness_next_day"].values,
        X_train_scaled,
        seed=seed
    )
    
    return {
        "models": models,
        "readiness_models": readiness_models,
        "feature_cols": feature_cols,
        "imputer": imputer,
        "scaler": scaler,
        "train_df": train_df,
        "val_df": val_df,
        "test_df": test_df,
        "X_train": X_train,
        "X_train_scaled": X_train_scaled,
        "y_train": y_train,
        "X_val": X_val,
        "X_val_scaled": X_val_scaled,
        "y_val": y_val,
        "X_test": X_test,
        "X_test_scaled": X_test_scaled,
        "y_test": y_test
    }


if __name__ == "__main__":
    run_full_training_pipeline()
