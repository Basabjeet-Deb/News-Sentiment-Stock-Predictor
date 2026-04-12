"""
Next-day stock direction forecaster trained on the daily news panel.

Uses strict time-based splits (no leakage) and produces:
- probability_up (P(direction_fwd==1))
- confidence (|p-0.5|*2)
- recommendation buckets
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    import joblib  # type: ignore
except Exception:  # pragma: no cover
    joblib = None


@dataclass
class ForecasterArtifacts:
    model_path: str
    meta_path: str


class DailyPanelForecaster:
    """
    Trains a classifier on `data/daily_panel.csv` and predicts next-day UP probabilities.
    """

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.artifacts = ForecasterArtifacts(
            model_path=os.path.join(self.data_dir, "forecaster_model.pkl"),
            meta_path=os.path.join(self.data_dir, "forecaster_meta.json"),
        )

    @staticmethod
    def _feature_columns(df: pd.DataFrame) -> List[str]:
        candidates = [
            "news_count",
            "sent_mean",
            "sent_std",
            "sent_min",
            "sent_max",
            "relevance_mean",
            "high_impact_count",
            "macro_count",
            "sent_mean_roll3",
            "news_count_roll3",
            "sent_mean_roll7",
            "news_count_roll7",
        ]
        return [c for c in candidates if c in df.columns]

    @staticmethod
    def _time_split(df: pd.DataFrame, test_days: int = 14) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split by date: last `test_days` unique dates are test, rest are train.
        """
        dates = sorted(df["date_dt"].dropna().dt.date.unique().tolist())
        if len(dates) <= max(10, test_days + 1):
            # Not enough history; do a small tail split
            cut = int(len(df) * 0.8)
            return df.iloc[:cut].copy(), df.iloc[cut:].copy()
        test_set = set(dates[-test_days:])
        train = df[~df["date_dt"].dt.date.isin(test_set)].copy()
        test = df[df["date_dt"].dt.date.isin(test_set)].copy()
        return train, test

    def train(self, panel_csv: str) -> Dict:
        if joblib is None:
            raise RuntimeError("joblib is required to save/load the forecaster model. Install 'joblib'.")

        df = pd.read_csv(panel_csv)
        if df.empty:
            raise ValueError("daily_panel.csv is empty")

        df["date_dt"] = pd.to_datetime(df["date"], errors="coerce")
        df = df[df["date_dt"].notna()].copy()

        # Target
        if "direction_fwd" not in df.columns:
            raise ValueError("daily_panel.csv missing direction_fwd labels")
        df["direction_fwd"] = pd.to_numeric(df["direction_fwd"], errors="coerce")
        df = df[df["direction_fwd"].isin([0, 1])].copy()

        feats = self._feature_columns(df)
        if len(feats) < 5:
            raise ValueError(f"Not enough feature columns in panel. Found: {feats}")

        X = df[feats].fillna(0.0)
        y = df["direction_fwd"].astype(int)

        train_df, test_df = self._time_split(df, test_days=14)
        X_train = train_df[feats].fillna(0.0)
        y_train = train_df["direction_fwd"].astype(int)
        X_test = test_df[feats].fillna(0.0)
        y_test = test_df["direction_fwd"].astype(int)

        # Prefer LightGBM if available, else fallback to sklearn
        model = None
        model_name = ""
        try:
            import lightgbm as lgb  # type: ignore

            model = lgb.LGBMClassifier(
                n_estimators=400,
                learning_rate=0.05,
                num_leaves=31,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
            )
            model_name = "LightGBM"
        except Exception:
            from sklearn.ensemble import RandomForestClassifier

            model = RandomForestClassifier(
                n_estimators=300,
                max_depth=10,
                min_samples_split=10,
                class_weight="balanced",
                random_state=42,
                n_jobs=-1,
            )
            model_name = "RandomForest"

        model.fit(X_train, y_train)

        # Metrics
        from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

        proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else model.predict(X_test)
        pred = (proba >= 0.5).astype(int)
        acc = float(accuracy_score(y_test, pred)) if len(y_test) else 0.0
        f1 = float(f1_score(y_test, pred, zero_division=0)) if len(y_test) else 0.0
        try:
            auc = float(roc_auc_score(y_test, proba)) if len(np.unique(y_test)) > 1 else 0.5
        except Exception:
            auc = 0.5

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

        joblib.dump({"model": model, "features": feats}, self.artifacts.model_path)
        with open(self.artifacts.meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        return meta

    def load(self):
        if joblib is None:
            raise RuntimeError("joblib is required to save/load the forecaster model. Install 'joblib'.")
        if not os.path.exists(self.artifacts.model_path):
            raise FileNotFoundError("Forecaster model not trained yet")
        bundle = joblib.load(self.artifacts.model_path)
        return bundle["model"], bundle["features"]

    @staticmethod
    def prob_to_recommendation(p_up: float) -> str:
        """
        Map probability to recommendation.

        These buckets are intentionally *moderately* conservative so we don't end up with
        98% HOLDs when the model is only mildly confident (common in noisy news-driven data).
        """
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
        df = pd.read_csv(panel_csv)
        df["date_dt"] = pd.to_datetime(df["date"], errors="coerce")
        df = df[df["date_dt"].notna()].copy()
        if df.empty:
            return pd.DataFrame()

        latest_date = df["date_dt"].max()
        latest = df[df["date_dt"] == latest_date].copy()
        if latest.empty:
            return pd.DataFrame()

        X = latest[feats].fillna(0.0)
        p_up = model.predict_proba(X)[:, 1] if hasattr(model, "predict_proba") else model.predict(X)
        latest["ml_probability_up"] = p_up.astype(float)
        latest["ml_confidence"] = (np.abs(latest["ml_probability_up"] - 0.5) * 2).clip(0, 1)

        # Recommendation strategy:
        # Use *rank-based* buckets to avoid tie issues when many probabilities are identical.
        # This guarantees stable coverage: top/bottom 5% are STRONG, next 5% are regular.
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

        # A score in [-1, 1] for sorting
        latest["ml_score"] = (latest["ml_probability_up"] - 0.5) * 2

        return latest[["ticker", "date", "ml_probability_up", "ml_confidence", "ml_recommendation", "ml_score"]]

