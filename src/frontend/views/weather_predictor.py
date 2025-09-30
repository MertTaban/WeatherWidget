# src/frontend/views/weather_predictor.py

import os
import pickle
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd


def _find_model_path(given: Optional[str]) -> Optional[str]:
    """Model dosyasını bulmak için çeşitli yolları dene"""
    if given:
        p = Path(given)
        if p.is_file():
            return str(p.resolve())

    env = os.environ.get("WEATHER_MODEL_PATH")
    if env and Path(env).is_file():
        return str(Path(env).resolve())

    here = Path(__file__).parent
    root = here.parents[3] if len(here.parents) >= 4 else here

    candidates = [
        here / "weather_prediction_model.joblib",
        here / "weather_prediction_model.pkl",
        here / "models" / "weather_prediction_model.joblib",
        here.parent / "weather_prediction_model.joblib",
        root / "weather_prediction_model.joblib",
        Path.cwd() / "weather_prediction_model.joblib",
    ]
    for c in candidates:
        if c.is_file():
            return str(c.resolve())

    return None


class WeatherPredictor:
    """Hava durumu tahmin sınıfı - joblib/pickle modelini yükler ve tahmin yapar"""

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.model_path = _find_model_path(model_path)

        if not self.model_path:
            print("[predictor] ERROR: model file not found")
            return

        print(f"[predictor] loading model: {self.model_path}")
        ext = Path(self.model_path).suffix.lower()

        try:
            if ext == ".joblib":
                import joblib

                self.model = joblib.load(self.model_path)
            elif ext == ".skops":
                from skops.io import load

                self.model = load(self.model_path)
            else:
                with open(self.model_path, "rb") as f:
                    self.model = pickle.load(f)
        except Exception as e:
            print("[predictor] load failed:", e)
            self.model = None

    def create_features(self, dates: List[pd.Timestamp]) -> pd.DataFrame:
        features = []
        for date in dates:
            month = date.month
            day = date.day
            hour = date.hour
            day_of_week = date.weekday()
            day_of_year = date.timetuple().tm_yday
            quarter = (month - 1) // 3 + 1
            is_weekend = 1 if day_of_week >= 5 else 0

            if month in [12, 1, 2]:
                season = 1
            elif month in [3, 4, 5]:
                season = 2
            elif month in [6, 7, 8]:
                season = 3
            else:
                season = 4

            features.append(
                {
                    "month": month,
                    "day": day,
                    "hour": hour,
                    "day_of_week": day_of_week,
                    "day_of_year": day_of_year,
                    "quarter": quarter,
                    "is_weekend": is_weekend,
                    "season": season,
                    "month_sin": np.sin(2 * np.pi * month / 12),
                    "month_cos": np.cos(2 * np.pi * month / 12),
                    "hour_sin": np.sin(2 * np.pi * hour / 24),
                    "hour_cos": np.cos(2 * np.pi * hour / 24),
                }
            )
        return pd.DataFrame(features)

    def predict(self, dates: List[pd.Timestamp]) -> pd.DataFrame:
        if self.model is None:
            print("[predictor] ERROR: model not loaded")
            return pd.DataFrame()

        try:
            features_df = self.create_features(dates)
            predictions = self.model.predict(features_df)

            if predictions.ndim > 1:
                df = pd.DataFrame({"date": [d.strftime("%Y-%m-%d") for d in dates]})
                for i in range(predictions.shape[1]):
                    df[f"prediction_{i+1}"] = predictions[:, i]
                return df

            return pd.DataFrame(
                {
                    "date": [d.strftime("%Y-%m-%d") for d in dates],
                    "prediction": predictions,
                }
            )

        except Exception as e:
            print("[predictor] predict failed:", e)
            return pd.DataFrame()
