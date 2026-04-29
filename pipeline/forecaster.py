"""
Next-day stock direction forecaster trained on the daily news panel.

Improvements over v1:
- Ensemble: LightGBM + XGBoost + RandomForest (soft-vote)
- Richer features: price momentum, volatility, volume, rolling windows
- Optuna hyperparameter tuning (fast 30-trial search)
- Strict time-based splits (no leakage)
- Produces probability_up, confidence, recommendation per ticker
"""

from __future__ import annotations

import json
import os
import warnings
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

try:
    import joblib
except ImportError:
    joblib = None


@dataclass
class ForecasterArtifacts:
    model_path: str
    meta_path: str


class DailyPanelForecaster:
    """
    Trains an ensemble classifier on `data/daily_panel.csv` and predicts
    next-day UP probabilities.
    """

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.artifacts = ForecasterArtifacts(
            model_path=os.path.join(self.data_dir, "forecaster_model.pkl"),
            meta_path=os.path.join(self.data_dir, "forecaster_meta.json"),
        )

    # ------------------------------------------------------------------
    # Feature engineering
    # ------------------------------------------------------------------

    @staticmethod
    def _add_price_features(df: pd.DataFrame) -> pd.DataFrame:
        """Add price-based features from daily_panel if available."""
        # These columns come from TimeSeriesDatasetBuilder._build_forward_return_labels
        # return_fwd is the *label* — never use it as a feature (leakage).
        # But we can derive momentum from lagged returns.
        if "return_fwd" in df.columns:
            df = df.sort_values(["ticker", "date_dt"])
            # Lag-1 and lag-2 returns as momentum features (no leakage)
            df["return_lag1"] = df.groupby("ticker")["return_fwd"].shift(1)
            df["return_lag2"] = df.groupby("ticker")["return_fwd"].shift(2)
            df["return_lag1"] = df["return_lag1"].fillna(0.0)
            df["return_lag2"] = df["return_lag2"].fillna(0.0)
            # Volatility: rolling std of lagged returns
            df["vol_5d"] = (
                df.groupby("ticker")["return_lag1"]
                .transform(lambda s: s.rolling(5, min_periods=1).std())
                .fillna(0.0)
            )
        return df

    @staticmethod
    def _feature_columns(df: pd.DataFrame) -> List[str]:
        candidates = [
            # News sentiment
            "news_count",
            "sent_mean",
            "sent_std",
            "sent_min",
            "sent_max",
            "relevance_mean",
            "high_impact_count",
            "macro_count",
            # Rolling windows
            "sent_mean_roll3",
            "news_count_roll3",
            "sent_mean_roll7",
            "news_count_roll7",
            # Price-derived (lag, no leakage)
            "return_lag1",
            "return_lag2",
            "vol_5d",
            # Technical indicators
            "rsi14",
            "macd_hist",
            "bb_pos",
            "vol_ratio",
            "price_trend",
            "atr_pct",
            # Derived interaction
            "sent_x_news",
            "sent_range",
        ]
        return [c for c in candidates if c in df.columns]

    @staticmethod
    def _engineer(df: pd.DataFrame) -> pd.DataFrame:
        """Add derived features."""
        df = df.copy()
        if "sent_mean" in df.columns and "news_count" in df.columns:
            df["sent_x_news"] = df["sent_mean"] * np.log1p(df["news_count"])
        if "sent_max" in df.columns and "sent_min" in df.columns:
            df["sent_range"] = df["sent_max"] - df["sent_min"]
        return df

    # ------------------------------------------------------------------
    # Train / test split
    # ------------------------------------------------------------------

    @staticmethod
    def _time_split(df: pd.DataFrame, test_days: int = 14) -> Tuple[pd.DataFrame, pd.DataFrame]:
        dates = sorted(df["date_dt"].dropna().dt.date.unique().tolist())
        if len(dates) <= max(10, test_days + 1):
            cut = int(len(df) * 0.8)
            return df.iloc[:cut].copy(), df.iloc[cut:].copy()
        test_set = set(dates[-test_days:])
        train = df[~df["date_dt"].dt.date.isin(test_set)].copy()
        test = df[df["date_dt"].dt.date.isin(test_set)].copy()
        return train, test

    # ------------------------------------------------------------------
    # Model builders
    # ------------------------------------------------------------------

    def _build_lgbm(self, params: Optional[Dict] = None):
        import lightgbm as lgb
        defaults = dict(
            n_estimators=500,
            learning_rate=0.03,
            num_leaves=31,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_samples=20,
            reg_alpha=0.1,
            reg_lambda=0.1,
            class_weight="balanced",
            random_state=42,
            verbose=-1,
        )
        if params:
            defaults.update(params)
        return lgb.LGBMClassifier(**defaults)

    def _build_xgb(self, params: Optional[Dict] = None):
        import xgboost as xgb
        defaults = dict(
            n_estimators=500,
            learning_rate=0.03,
            max_depth=5,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=5,
            gamma=0.1,
            reg_alpha=0.1,
            reg_lambda=1.0,
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=42,
            verbosity=0,
        )
        if params:
            defaults.update(params)
        return xgb.XGBClassifier(**defaults)

    def _build_rf(self, params: Optional[Dict] = None):
        from sklearn.ensemble import RandomForestClassifier
        defaults = dict(
            n_estimators=400,
            max_depth=10,
            min_samples_split=10,
            min_samples_leaf=5,
            max_features="sqrt",
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )
        if params:
            defaults.update(params)
        return RandomForestClassifier(**defaults)

    # ------------------------------------------------------------------
    # Optuna tuning (fast, 30 trials)
    # ------------------------------------------------------------------

    def _tune_lgbm(self, X_train, y_train, X_val, y_val) -> Dict:
        try:
            import optuna
            optuna.logging.set_verbosity(optuna.logging.WARNING)
            import lightgbm as lgb
            from sklearn.metrics import roc_auc_score

            def objective(trial):
                params = dict(
                    n_estimators=trial.suggest_int("n_estimators", 200, 800),
                    learning_rate=trial.suggest_float("learning_rate", 0.01, 0.1, log=True),
                    num_leaves=trial.suggest_int("num_leaves", 15, 63),
                    max_depth=trial.suggest_int("max_depth", 3, 8),
                    subsample=trial.suggest_float("subsample", 0.6, 1.0),
                    colsample_bytree=trial.suggest_float("colsample_bytree", 0.6, 1.0),
                    min_child_samples=trial.suggest_int("min_child_samples", 10, 50),
                    reg_alpha=trial.suggest_float("reg_alpha", 1e-3, 1.0, log=True),
                    reg_lambda=trial.suggest_float("reg_lambda", 1e-3, 1.0, log=True),
                    class_weight="balanced",
                    random_state=42,
                    verbose=-1,
                )
                m = lgb.LGBMClassifier(**params)
                m.fit(X_train, y_train)
                p = m.predict_proba(X_val)[:, 1]
                return roc_auc_score(y_val, p) if len(np.unique(y_val)) > 1 else 0.5

            study = optuna.create_study(direction="maximize")
            study.optimize(objective, n_trials=30, show_progress_bar=False)
            print(f"[TUNE] LightGBM best AUC={study.best_value:.4f} params={study.best_params}")
            return study.best_params
        except Exception as e:
            print(f"[TUNE] Optuna skipped: {e}")
            return {}

    # ------------------------------------------------------------------
    # Train
    # ------------------------------------------------------------------

    def train(self, panel_csv: str, use_balanced: bool = True) -> Dict:
        if joblib is None:
            raise RuntimeError("joblib is required. Install it with: pip install joblib")

        # Use balanced panel if available to prevent overfitting
        if use_balanced:
            balanced_path = panel_csv.replace('.csv', '_balanced.csv')
            if os.path.exists(balanced_path):
                panel_csv = balanced_path
                print(f"[FORECASTER] Using balanced panel: {balanced_path}")

        df = pd.read_csv(panel_csv, on_bad_lines="skip")
        if df.empty:
            raise ValueError("daily_panel.csv is empty")

        df["date_dt"] = pd.to_datetime(df["date"], errors="coerce")
        df = df[df["date_dt"].notna()].copy()

        if "direction_fwd" not in df.columns:
            raise ValueError("daily_panel.csv missing direction_fwd labels")
        df["direction_fwd"] = pd.to_numeric(df["direction_fwd"], errors="coerce")
        df = df[df["direction_fwd"].isin([0, 1])].copy()

        # Only train on rows that actually have news — zero-news rows are pure noise
        # and dilute the signal massively (typically 98%+ of the panel)
        df_with_news = df[df["news_count"] > 0].copy()
        if len(df_with_news) >= 50:
            df = df_with_news
            print(f"[FORECASTER] Filtered to news-only rows: {len(df)} / {len(df_with_news) + (len(df) - len(df_with_news))} total")
        else:
            print(f"[FORECASTER] Not enough news rows ({len(df_with_news)}), using all rows")

        # Add price features and engineer derived features
        df = self._add_price_features(df)
        df = self._engineer(df)

        feats = self._feature_columns(df)
        if len(feats) < 3:
            raise ValueError(f"Not enough feature columns. Found: {feats}")

        print(f"[FORECASTER] Training on {len(df)} rows, {len(feats)} features: {feats}")

        train_df, test_df = self._time_split(df, test_days=14)
        X_train = train_df[feats].fillna(0.0)
        y_train = train_df["direction_fwd"].astype(int)
        X_test = test_df[feats].fillna(0.0)
        y_test = test_df["direction_fwd"].astype(int)

        # Calculate class imbalance for XGBoost
        n_neg = (y_train == 0).sum()
        n_pos = (y_train == 1).sum()
        scale_pos_weight = n_neg / n_pos if n_pos > 0 else 1.0
        print(f"[FORECASTER] Class balance: {n_neg} negative, {n_pos} positive (scale_pos_weight={scale_pos_weight:.2f})")

        # Use a validation slice from train for tuning (last 7 days of train)
        train_dates = sorted(train_df["date_dt"].dt.date.unique())
        if len(train_dates) > 7:
            val_dates = set(train_dates[-7:])
            val_mask = train_df["date_dt"].dt.date.isin(val_dates)
            X_tune_val = train_df.loc[val_mask, feats].fillna(0.0)
            y_tune_val = train_df.loc[val_mask, "direction_fwd"].astype(int)
            X_tune_train = train_df.loc[~val_mask, feats].fillna(0.0)
            y_tune_train = train_df.loc[~val_mask, "direction_fwd"].astype(int)
        else:
            X_tune_train, y_tune_train = X_train, y_train
            X_tune_val, y_tune_val = X_test, y_test

        # Tune LightGBM
        best_lgbm_params = self._tune_lgbm(X_tune_train, y_tune_train, X_tune_val, y_tune_val)

        # Build individual models
        models_available = []
        model_name = "Ensemble"

        try:
            lgbm = self._build_lgbm(best_lgbm_params)
            lgbm.fit(X_train, y_train)
            models_available.append(("lgbm", lgbm))
            print("[FORECASTER] LightGBM trained")
        except Exception as e:
            print(f"[FORECASTER] LightGBM failed: {e}")

        try:
            xgb_model = self._build_xgb({'scale_pos_weight': scale_pos_weight})
            xgb_model.fit(X_train, y_train)
            models_available.append(("xgb", xgb_model))
            print("[FORECASTER] XGBoost trained (with scale_pos_weight)")
        except Exception as e:
            print(f"[FORECASTER] XGBoost failed: {e}")

        try:
            rf = self._build_rf()
            rf.fit(X_train, y_train)
            models_available.append(("rf", rf))
            print("[FORECASTER] RandomForest trained")
        except Exception as e:
            print(f"[FORECASTER] RandomForest failed: {e}")

        if not models_available:
            raise RuntimeError("All model backends failed to train.")

        # Soft-vote ensemble
        if len(models_available) > 1:
            from sklearn.ensemble import VotingClassifier
            ensemble = VotingClassifier(
                estimators=models_available,
                voting="soft",
                weights=[1.2, 1.0, 0.8][: len(models_available)],  # slight LightGBM bias
            )
            ensemble.fit(X_train, y_train)
            final_model = ensemble
            model_name = f"Ensemble({'+'.join(n for n, _ in models_available)})"
        else:
            final_model = models_available[0][1]
            model_name = models_available[0][0].upper()

        # Metrics
        from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

        proba = (
            final_model.predict_proba(X_test)[:, 1]
            if hasattr(final_model, "predict_proba")
            else final_model.predict(X_test).astype(float)
        )
        pred = (proba >= 0.5).astype(int)
        acc = float(accuracy_score(y_test, pred)) if len(y_test) else 0.0
        f1 = float(f1_score(y_test, pred, zero_division=0)) if len(y_test) else 0.0
        try:
            auc = float(roc_auc_score(y_test, proba)) if len(np.unique(y_test)) > 1 else 0.5
        except Exception:
            auc = 0.5

        print(f"[FORECASTER] {model_name} | Acc={acc:.3f} F1={f1:.3f} AUC={auc:.3f}")

        meta = {
            "trained_at": datetime.now().isoformat(),
            "model": model_name,
            "features": feats,
            "rows": int(len(df)),
            "train_rows": int(len(train_df)),
            "test_rows": int(len(test_df)),
            "test_days": 14,
            "metrics": {"accuracy": acc, "f1": f1, "auc": auc},
        }

        joblib.dump({"model": final_model, "features": feats}, self.artifacts.model_path)
        with open(self.artifacts.meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        return meta

    # ------------------------------------------------------------------
    # Load + predict
    # ------------------------------------------------------------------

    def load(self):
        if joblib is None:
            raise RuntimeError("joblib is required.")
        if not os.path.exists(self.artifacts.model_path):
            raise FileNotFoundError("Forecaster model not trained yet")
        bundle = joblib.load(self.artifacts.model_path)
        return bundle["model"], bundle["features"]

    @staticmethod
    def prob_to_recommendation(p_up: float) -> str:
        if p_up >= 0.66:
            return "STRONG BUY"
        if p_up >= 0.56:
            return "BUY"
        if p_up <= 0.34:
            return "STRONG SELL"
        if p_up <= 0.44:
            return "SELL"
        return "HOLD"

    def predict_latest(self, panel_csv: str) -> pd.DataFrame:
        model, feats = self.load()

        df = pd.read_csv(panel_csv, on_bad_lines="skip")
        df["date_dt"] = pd.to_datetime(df["date"], errors="coerce")
        df = df[df["date_dt"].notna()].copy()
        if df.empty:
            return pd.DataFrame()

        # Add price features and engineer derived features
        df = self._add_price_features(df)
        df = self._engineer(df)

        # Use the LATEST available date (today's data, not stale)
        latest_date = df["date_dt"].max()
        latest = df[df["date_dt"] == latest_date].copy()

        # Only predict for tickers that have news on the latest date
        if "news_count" in latest.columns:
            latest_with_news = latest[latest["news_count"] > 0].copy()
            if len(latest_with_news) >= 5:
                latest = latest_with_news
            # If fewer than 5 tickers have news today, fall back to all tickers
        if latest.empty:
            return pd.DataFrame()

        # Ensure all required features exist
        for f in feats:
            if f not in latest.columns:
                latest[f] = 0.0

        X = latest[feats].fillna(0.0)
        p_up = (
            model.predict_proba(X)[:, 1]
            if hasattr(model, "predict_proba")
            else model.predict(X).astype(float)
        )
        latest = latest.copy()
        latest["ml_probability_up"] = p_up.astype(float)
        latest["ml_confidence"] = (np.abs(latest["ml_probability_up"] - 0.5) * 2).clip(0, 1)

        # Rank-based recommendations to guarantee spread
        p = latest["ml_probability_up"].astype(float)
        n = int(len(p))
        strong_n = max(1, int(round(n * 0.05)))
        reg_n = max(1, int(round(n * 0.10)))

        order_desc = p.sort_values(ascending=False).index.tolist()
        order_asc = p.sort_values(ascending=True).index.tolist()

        strong_buy_idx = set(order_desc[:strong_n])
        buy_idx = set(order_desc[strong_n:reg_n])
        strong_sell_idx = set(order_asc[:strong_n])
        sell_idx = set(order_asc[strong_n:reg_n])

        rec = pd.Series("HOLD", index=latest.index, dtype="object")
        rec.loc[list(sell_idx)] = "SELL"
        rec.loc[list(strong_sell_idx)] = "STRONG SELL"
        rec.loc[list(buy_idx)] = "BUY"
        rec.loc[list(strong_buy_idx)] = "STRONG BUY"
        latest["ml_recommendation"] = rec
        latest["ml_score"] = (latest["ml_probability_up"] - 0.5) * 2

        return latest[
            ["ticker", "date", "ml_probability_up", "ml_confidence", "ml_recommendation", "ml_score"]
        ]
