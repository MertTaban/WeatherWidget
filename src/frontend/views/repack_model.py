import os
import pickle
import sys
from pathlib import Path

import joblib

SRC = Path("src\\frontend\\views\\weather_prediction_model.pkl")  # mevcut pkl
DST = Path("src\\frontend\\views\\weather_prediction_model.joblib")

if not SRC.exists():
    print("Kaynak pkl bulunamadı:", SRC.resolve())
    sys.exit(1)

# Eski ortamda aç
with open(SRC, "rb") as f:
    model = pickle.load(f)

# Joblib'e yaz
joblib.dump(model, DST)
print("Yazıldı:", DST.resolve())
