import warnings
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from google.colab import files
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputRegressor

warnings.filterwarnings("ignore")


plt.style.use("seaborn-v0_8-darkgrid")
sns.set_palette("husl")

print("✅ Kütüphaneler başarıyla yüklendi!")


print("📁 Lütfen CSV dosyanızı seçin...")
uploaded = files.upload()

# Yüklenen dosyanın adını al
filename = list(uploaded.keys())[0]
print(f"✅ '{"karabuk_hourly_2020_2025.csv"}' dosyası başarıyla yüklendi!")


df = pd.read_csv("karabuk_hourly_2020_2025.csv")


print("📊 Verinin ilk 5 satırı:")
print(df.head())
print("\n📈 Veri boyutu:", df.shape)
print("\n📋 Sütun bilgileri:")
print(df.info())
print("\n📊 İstatistiksel özet:")
print(df.describe())


df.rename(columns={"date": "datetime"}, inplace=True)
df["datetime"] = pd.to_datetime(df["datetime"])
df = df.set_index("datetime")


df["year"] = df.index.year
df["month"] = df.index.month
df["day"] = df.index.day
df["hour"] = df.index.hour
df["day_of_week"] = df.index.dayofweek  # 0=Pazartesi, 6=Pazar
df["day_of_year"] = df.index.dayofyear
df["quarter"] = df.index.quarter
df["is_weekend"] = (df.index.dayofweek >= 5).astype(int)


# Eğer datetime sütunu yoksa index’ten alıp sütun yap
df = df.reset_index()  # index’i sütun yapar, adı 'date' olacak
df.rename(columns={"date": "datetime"}, inplace=True)

# Şimdi tarih özelliklerini çıkarabilirsin
df["year"] = df["datetime"].dt.year
df["month"] = df["datetime"].dt.month
df["day"] = df["datetime"].dt.day
df["hour"] = df["datetime"].dt.hour
df["day_of_week"] = df["datetime"].dt.dayofweek
df["day_of_year"] = df["datetime"].dt.dayofyear
df["quarter"] = df["datetime"].dt.quarter
df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

# Mevsim ve trigonometrik özellikler
df["season"] = df["month"].apply(get_season)
df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)

# Artık 'datetime' sütunu var
print(
    df[
        [
            "datetime",
            "year",
            "month",
            "day",
            "hour",
            "day_of_week",
            "day_of_year",
            "season",
            "is_weekend",
        ]
    ].head()
)


print("🔍 Eksik veri kontrolü:")
print(df.isnull().sum())


if df.isnull().sum().sum() > 0:
    print("\n⚠️ Eksik veriler bulundu. Temizleniyor...")
    # Sayısal değerler için interpolasyon kullan
    df["temperature_2m"] = df["temperature_2m"].interpolate(method="linear")
    df["precipitation"] = df["precipitation"].interpolate(method="linear")
    # Kalan eksikleri sil
    df = df.dropna()
    print("✅ Eksik veriler temizlendi!")
else:
    print("✅ Eksik veri yok!")

print(f"\n📊 Temizlenmiş veri boyutu: {df.shape}")


feature_columns = [
    "month",
    "day",
    "hour",
    "day_of_week",
    "day_of_year",
    "quarter",
    "is_weekend",
    "season",
    "month_sin",
    "month_cos",
    "hour_sin",
    "hour_cos",
]


target_columns = ["temperature_2m", "precipitation"]


X = df[feature_columns]
y = df[target_columns]

print("📊 Özellik matrisi (X) boyutu:", X.shape)
print("🎯 Hedef matrisi (y) boyutu:", y.shape)
print("\n📋 Özellikler:", feature_columns)
print("🎯 Hedefler:", target_columns)


X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, shuffle=True
)

print("📊 Eğitim seti boyutu:")
print(f"   X_train: {X_train.shape}")
print(f"   y_train: {y_train.shape}")
print("\n📊 Test seti boyutu:")
print(f"   X_test: {X_test.shape}")
print(f"   y_test: {y_test.shape}")


print("🤖 Model oluşturuluyor ve eğitiliyor...")

# RandomForestRegressor'ı MultiOutputRegressor ile sar
base_model = RandomForestRegressor(
    n_estimators=100,
    max_depth=20,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1,  # Tüm CPU çekirdeklerini kullan
)

# Çoklu çıktı için model
model = MultiOutputRegressor(base_model)

# Modeli eğit
model.fit(X_train, y_train)

print("✅ Model başarıyla eğitildi!")


feature_importance_temp = model.estimators_[0].feature_importances_
feature_importance_precip = model.estimators_[1].feature_importances_

print("\n📊 Özellik Önemlilikleri (Sıcaklık için):")
for feat, imp in sorted(
    zip(feature_columns, feature_importance_temp), key=lambda x: x[1], reverse=True
):
    print(f"   {feat}: {imp:.4f}")


y_pred = model.predict(X_test)

# Her hedef için ayrı metrikler hesapla
mse_temp = mean_squared_error(y_test["temperature_2m"], y_pred[:, 0])
mse_precip = mean_squared_error(y_test["precipitation"], y_pred[:, 1])
mae_temp = mean_absolute_error(y_test["temperature_2m"], y_pred[:, 0])
mae_precip = mean_absolute_error(y_test["precipitation"], y_pred[:, 1])
r2_temp = r2_score(y_test["temperature_2m"], y_pred[:, 0])
r2_precip = r2_score(y_test["precipitation"], y_pred[:, 1])

print("📊 Model Performansı:")
print("\n🌡️ Sıcaklık Tahmin Metrikleri:")
print(f"   MSE: {mse_temp:.4f}")
print(f"   RMSE: {np.sqrt(mse_temp):.4f}")
print(f"   MAE: {mae_temp:.4f}")
print(f"   R² Skoru: {r2_temp:.4f}")

print("\n💧 Yağış Tahmin Metrikleri:")
print(f"   MSE: {mse_precip:.4f}")
print(f"   RMSE: {np.sqrt(mse_precip):.4f}")
print(f"   MAE: {mae_precip:.4f}")
print(f"   R² Skoru: {r2_precip:.4f}")


fig, axes = plt.subplots(2, 2, figsize=(15, 12))

# 1. Sıcaklık: Gerçek vs Tahmin (Scatter)
axes[0, 0].scatter(y_test["temperature_2m"], y_pred[:, 0], alpha=0.5, s=10, c="blue")
axes[0, 0].plot(
    [y_test["temperature_2m"].min(), y_test["temperature_2m"].max()],
    [y_test["temperature_2m"].min(), y_test["temperature_2m"].max()],
    "r--",
    lw=2,
)
axes[0, 0].set_xlabel("Gerçek Sıcaklık (°C)", fontsize=12)
axes[0, 0].set_ylabel("Tahmin Edilen Sıcaklık (°C)", fontsize=12)
axes[0, 0].set_title("Sıcaklık: Gerçek vs Tahmin", fontsize=14, fontweight="bold")
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].text(
    0.05,
    0.95,
    f"R² = {r2_temp:.3f}\nRMSE = {np.sqrt(mse_temp):.2f}°C",
    transform=axes[0, 0].transAxes,
    fontsize=11,
    verticalalignment="top",
    bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
)

# 2. Yağış: Gerçek vs Tahmin (Scatter)
axes[0, 1].scatter(y_test["precipitation"], y_pred[:, 1], alpha=0.5, s=10, c="green")
axes[0, 1].plot(
    [y_test["precipitation"].min(), y_test["precipitation"].max()],
    [y_test["precipitation"].min(), y_test["precipitation"].max()],
    "r--",
    lw=2,
)
axes[0, 1].set_xlabel("Gerçek Yağış (mm)", fontsize=12)
axes[0, 1].set_ylabel("Tahmin Edilen Yağış (mm)", fontsize=12)
axes[0, 1].set_title("Yağış: Gerçek vs Tahmin", fontsize=14, fontweight="bold")
axes[0, 1].grid(True, alpha=0.3)
axes[0, 1].text(
    0.05,
    0.95,
    f"R² = {r2_precip:.3f}\nRMSE = {np.sqrt(mse_precip):.2f}mm",
    transform=axes[0, 1].transAxes,
    fontsize=11,
    verticalalignment="top",
    bbox=dict(boxstyle="round", facecolor="lightblue", alpha=0.5),
)

# 3. Sıcaklık: Zaman serisi karşılaştırması (ilk 200 örnek)
sample_size = min(200, len(y_test))
indices = range(sample_size)
axes[1, 0].plot(
    indices,
    y_test["temperature_2m"].iloc[:sample_size].values,
    label="Gerçek",
    alpha=0.7,
    linewidth=1.5,
)
axes[1, 0].plot(
    indices, y_pred[:sample_size, 0], label="Tahmin", alpha=0.7, linewidth=1.5
)
axes[1, 0].set_xlabel("Örnek İndeksi", fontsize=12)
axes[1, 0].set_ylabel("Sıcaklık (°C)", fontsize=12)
axes[1, 0].set_title(
    "Sıcaklık Zaman Serisi Karşılaştırması", fontsize=14, fontweight="bold"
)
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

# 4. Yağış: Zaman serisi karşılaştırması (ilk 200 örnek)
axes[1, 1].plot(
    indices,
    y_test["precipitation"].iloc[:sample_size].values,
    label="Gerçek",
    alpha=0.7,
    linewidth=1.5,
)
axes[1, 1].plot(
    indices, y_pred[:sample_size, 1], label="Tahmin", alpha=0.7, linewidth=1.5
)
axes[1, 1].set_xlabel("Örnek İndeksi", fontsize=12)
axes[1, 1].set_ylabel("Yağış (mm)", fontsize=12)
axes[1, 1].set_title(
    "Yağış Zaman Serisi Karşılaştırması", fontsize=14, fontweight="bold"
)
axes[1, 1].legend()
axes[1, 1].grid(True, alpha=0.3)

plt.suptitle(
    "Hava Durumu Tahmin Modeli Performansı", fontsize=16, fontweight="bold", y=1.02
)
plt.tight_layout()
plt.show()

# ============================================
# Hücre 12: Hata dağılımı analizi
# ============================================
# Hata hesaplama
temp_errors = y_test["temperature_2m"].values - y_pred[:, 0]
precip_errors = y_test["precipitation"].values - y_pred[:, 1]

# Grafik
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Sıcaklık hata dağılımı
axes[0].hist(temp_errors, bins=50, edgecolor="black", alpha=0.7, color="coral")
axes[0].axvline(x=0, color="red", linestyle="--", linewidth=2)
axes[0].set_xlabel("Hata (°C)", fontsize=12)
axes[0].set_ylabel("Frekans", fontsize=12)
axes[0].set_title("Sıcaklık Tahmin Hatası Dağılımı", fontsize=14, fontweight="bold")
axes[0].grid(True, alpha=0.3)
axes[0].text(
    0.05,
    0.95,
    f"Ortalama Hata: {np.mean(temp_errors):.3f}°C\n"
    f"Std Sapma: {np.std(temp_errors):.3f}°C",
    transform=axes[0].transAxes,
    fontsize=11,
    verticalalignment="top",
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
)

# Yağış hata dağılımı
axes[1].hist(precip_errors, bins=50, edgecolor="black", alpha=0.7, color="skyblue")
axes[1].axvline(x=0, color="red", linestyle="--", linewidth=2)
axes[1].set_xlabel("Hata (mm)", fontsize=12)
axes[1].set_ylabel("Frekans", fontsize=12)
axes[1].set_title("Yağış Tahmin Hatası Dağılımı", fontsize=14, fontweight="bold")
axes[1].grid(True, alpha=0.3)
axes[1].text(
    0.05,
    0.95,
    f"Ortalama Hata: {np.mean(precip_errors):.3f}mm\n"
    f"Std Sapma: {np.std(precip_errors):.3f}mm",
    transform=axes[1].transAxes,
    fontsize=11,
    verticalalignment="top",
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
)

plt.tight_layout()
plt.show()


def predict_weather(target_date, target_hour, model, df):
    """
    Belirtilen tarih ve saat için hava durumu tahmini yapar.
    Geçmiş yılların aynı tarih ve saatlerindeki verilerden yararlanır.

    Parametreler:
    - target_date: 'YYYY-MM-DD' formatında tarih string'i
    - target_hour: Saat (0-23 arası)
    - model: Eğitilmiş model
    - df: Orijinal DataFrame

    Döndürür:
    - Tahmin edilen sıcaklık ve yağış değerleri
    """

    # Tarih parse et
    target_dt = pd.to_datetime(target_date)

    # Özellikler oluştur
    features = {
        "month": target_dt.month,
        "day": target_dt.day,
        "hour": target_hour,
        "day_of_week": target_dt.dayofweek,
        "day_of_year": target_dt.dayofyear,
        "quarter": target_dt.quarter,
        "is_weekend": 1 if target_dt.dayofweek >= 5 else 0,
        "season": get_season(target_dt.month),
        "month_sin": np.sin(2 * np.pi * target_dt.month / 12),
        "month_cos": np.cos(2 * np.pi * target_dt.month / 12),
        "hour_sin": np.sin(2 * np.pi * target_hour / 24),
        "hour_cos": np.cos(2 * np.pi * target_hour / 24),
    }

    # DataFrame'e çevir
    X_pred = pd.DataFrame([features], columns=feature_columns)

    # Tahmin yap
    prediction = model.predict(X_pred)

    # Geçmiş verileri analiz et (aynı ay-gün-saat kombinasyonu)
    historical = df[
        (df["month"] == target_dt.month)
        & (df["day"] == target_dt.day)
        & (df["hour"] == target_hour)
    ]

    if len(historical) > 0:
        hist_temp_mean = historical["temperature_2m"].mean()
        hist_temp_std = historical["temperature_2m"].std()
        hist_precip_mean = historical["precipitation"].mean()
        hist_precip_std = historical["precipitation"].std()
    else:
        # Eğer tam eşleşme yoksa, aynı ay ve saati kullan
        historical = df[(df["month"] == target_dt.month) & (df["hour"] == target_hour)]
        if len(historical) > 0:
            hist_temp_mean = historical["temperature_2m"].mean()
            hist_temp_std = historical["temperature_2m"].std()
            hist_precip_mean = historical["precipitation"].mean()
            hist_precip_std = historical["precipitation"].std()
        else:
            hist_temp_mean = None
            hist_temp_std = None
            hist_precip_mean = None
            hist_precip_std = None

    # Sonuçları yazdır
    print(f"\n🌤️ HAVA DURUMU TAHMİNİ")
    print(f"📅 Tarih: {target_date}")
    print(f"⏰ Saat: {target_hour:02d}:00")
    print("-" * 50)

    print(f"\n🤖 MODEL TAHMİNİ:")
    print(f"🌡️ Sıcaklık: {prediction[0, 0]:.1f}°C")
    print(f"💧 Yağış: {prediction[0, 1]:.2f} mm")

    if hist_temp_mean is not None:
        print(f"\n📊 GEÇMİŞ VERİ ANALİZİ (aynı tarih/saat):")
        print(f"🌡️ Ortalama Sıcaklık: {hist_temp_mean:.1f}°C (±{hist_temp_std:.1f})")
        print(f"💧 Ortalama Yağış: {hist_precip_mean:.2f} mm (±{hist_precip_std:.2f})")
        print(f"📈 Geçmiş veri sayısı: {len(historical)} kayıt")

    # Hava durumu yorumu
    print(f"\n💬 YORUM:")
    if prediction[0, 0] < 0:
        temp_comment = "Çok soğuk"
    elif prediction[0, 0] < 10:
        temp_comment = "Soğuk"
    elif prediction[0, 0] < 20:
        temp_comment = "Ilık"
    elif prediction[0, 0] < 30:
        temp_comment = "Sıcak"
    else:
        temp_comment = "Çok sıcak"

    if prediction[0, 1] < 0.1:
        rain_comment = "yağışsız"
    elif prediction[0, 1] < 2:
        rain_comment = "hafif yağışlı"
    elif prediction[0, 1] < 10:
        rain_comment = "yağışlı"
    else:
        rain_comment = "şiddetli yağışlı"

    print(f"   {temp_comment} ve {rain_comment} bir hava bekleniyor.")

    return prediction[0, 0], prediction[0, 1]


# Test fonksiyonu
print("✅ Tahmin fonksiyonu hazır!")
print("\n📌 Kullanım örneği:")
print("   temp, rain = predict_weather('2025-09-25', 12, model, df)")


print("=" * 60)
print("🔮 ÖRNEK TAHMİNLER")
print("=" * 60)

# Yarın için tahmin
tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
predict_weather(tomorrow, 12, model, df)

print("\n" + "=" * 60)


three_days = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
predict_weather(three_days, 8, model, df)

print("\n" + "=" * 60)


one_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
predict_weather(one_week, 18, model, df)


# Hücre 15: Kullanıcı girdisi ile tahmin
# ============================================
def interactive_prediction():
    """
    Kullanıcıdan tarih ve saat alarak tahmin yapar.
    """
    print("🌤️ İNTERAKTİF HAVA DURUMU TAHMİNİ")
    print("-" * 40)

    while True:
        try:
            # Tarih al
            date_input = input(
                "\n📅 Tarih girin (YYYY-MM-DD formatında) veya çıkmak için 'q': "
            )
            if date_input.lower() == "q":
                print("👋 Güle güle!")
                break

            # Tarih formatını kontrol et
            try:
                pd.to_datetime(date_input)
            except:
                print("❌ Hatalı tarih formatı! YYYY-MM-DD şeklinde girin.")
                continue

            # Saat al
            hour_input = input("⏰ Saat girin (0-23 arası): ")
            hour = int(hour_input)

            if hour < 0 or hour > 23:
                print("❌ Saat 0-23 arasında olmalıdır!")
                continue

            # Tahmin yap
            predict_weather(date_input, hour, model, df)

        except ValueError:
            print("❌ Geçersiz giriş! Lütfen sayı girin.")
        except Exception as e:
            print(f"❌ Hata oluştu: {str(e)}")


z  # Fonksiyonu çalıştır
interactive_prediction()


# Hücre 16: Model kaydetme
# ============================================
import joblib

# Modeli kaydet
model_filename = "weather_prediction_model.pkl"
joblib.dump(model, model_filename)
print(f"✅ Model '{model_filename}' olarak kaydedildi!")

# İndirme linki oluştur
files.download(model_filename)
print("📥 Model dosyası indirildi!")
