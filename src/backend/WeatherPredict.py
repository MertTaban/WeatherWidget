import pickle
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List


class WeatherPredictor:
    """
    Hava durumu tahmin sınıfı - pickle dosyasından model yükler ve tahminler yapar
    """

    def __init__(self, model_path: str = "weather_prediction_model.pkl"):
        """
        Model dosyasını yükle

        Args:
            model_path (str): Pickle model dosyasının yolu
        """
        self.model = None
        self.model_path = model_path
        print(f"🔍 Model yükleniyor: {model_path}")
        self.load_model(model_path)

    def load_model(self, model_path: str):
        """
        Pickle dosyasından modeli yükle - Birden fazla yöntem dener

        Args:
            model_path (str): Model dosyasının yolu
        """
        print(f"📂 Model dosyası kontrol ediliyor: {model_path}")

        try:
            # Dosya varlığını kontrol et
            import os
            if not os.path.exists(model_path):
                print(f"❌ Hata: Model dosyası bulunamadı: {model_path}")
                print(f"📍 Mevcut klasör: {os.getcwd()}")
                print(f"📁 Klasördeki dosyalar: {os.listdir('.')}")
                return

            print(f"✅ Model dosyası bulundu: {model_path}")

            # Yöntem 1: Standart pickle ile dene
            print("🔄 Yöntem 1: Standart pickle ile yükleniyor...")
            try:
                with open(model_path, 'rb') as file:
                    self.model = pickle.load(file)
                    print(f"✅ Model başarıyla yüklendi (standart pickle): {model_path}")
                    return
            except Exception as e:
                print(f"❌ Standart pickle hatası: {str(e)}")

            # Yöntem 2: Latin-1 encoding ile dene
            print("🔄 Yöntem 2: Latin-1 encoding ile yükleniyor...")
            try:
                with open(model_path, 'rb') as file:
                    self.model = pickle.load(file, encoding='latin-1')
                    print(f"✅ Model başarıyla yüklendi (latin-1): {model_path}")
                    return
            except Exception as e:
                print(f"❌ Latin-1 encoding hatası: {str(e)}")

            # Yöntem 3: Joblib ile dene
            print("🔄 Yöntem 3: Joblib ile yükleniyor...")
            try:
                import joblib
                self.model = joblib.load(model_path)
                print(f"✅ Model başarıyla yüklendi (joblib): {model_path}")
                return
            except ImportError:
                print("⚠️ Joblib kütüphanesi bulunamadı. Kurulum: pip install joblib")
            except Exception as e:
                print(f"❌ Joblib hatası: {str(e)}")

            # Yöntem 4: Bytes mode ile farklı encodings
            print("🔄 Yöntem 4: Farklı encoding yöntemleri deneniyor...")
            encodings_to_try = ['utf-8', 'ascii', 'cp1252']

            for encoding in encodings_to_try:
                try:
                    with open(model_path, 'rb') as file:
                        self.model = pickle.load(file, encoding=encoding)
                        print(f"✅ Model başarıyla yüklendi ({encoding}): {model_path}")
                        return
                except Exception as e:
                    print(f"❌ {encoding} encoding hatası: {str(e)}")

            # Son çare: Model dosyasının içeriğini kontrol et
            print("🔍 Model dosyası içeriği kontrol ediliyor...")
            try:
                with open(model_path, 'rb') as file:
                    first_bytes = file.read(50)
                    print(f"📄 Dosya başlangıcı (ilk 50 byte): {first_bytes}")
            except Exception as e:
                print(f"❌ Dosya okuma hatası: {str(e)}")

        except Exception as e:
            print(f"❌ Beklenmeyen hata: {str(e)}")

        # Hiçbir yöntem çalışmadıysa
        print("\n💡 Çözüm Önerileri:")
        print("1. Model dosyasının bozuk olmadığından emin olun")
        print("2. Modeli farklı bir Python sürümü ile kaydettiyseniz, aynı sürümü kullanın")
        print("3. 'pip install joblib' komutu ile joblib kütüphanesini kurun")
        print("4. Modeli yeniden eğitip kaydedin")
        print("5. Model dosyasını farklı bir formatta (joblib ile) kaydetmeyi deneyin")

    def create_features(self, dates: List[datetime]) -> pd.DataFrame:
        """
        Modelin beklediği tüm özellikleri hesapla

        Args:
            dates (List[datetime]): Tarih listesi

        Returns:
            pd.DataFrame: Modelin beklediği özellikler
        """
        import numpy as np

        features = []

        for date in dates:
            # Temel tarih bilgileri
            month = date.month
            day = date.day
            hour = date.hour  # Default 0 (gece yarısı)
            day_of_week = date.weekday()  # 0=Pazartesi, 6=Pazar
            day_of_year = date.timetuple().tm_yday

            # Çeyrek hesapla
            quarter = (month - 1) // 3 + 1

            # Hafta sonu kontrolü
            is_weekend = 1 if day_of_week >= 5 else 0

            # Mevsim hesapla (1=Kış, 2=İlkbahar, 3=Yaz, 4=Sonbahar)
            if month in [12, 1, 2]:
                season = 1  # Kış
            elif month in [3, 4, 5]:
                season = 2  # İlkbahar
            elif month in [6, 7, 8]:
                season = 3  # Yaz
            else:
                season = 4  # Sonbahar

            # Trigonometrik özellikler (döngüsel zamanları yakalamak için)
            month_sin = np.sin(2 * np.pi * month / 12)
            month_cos = np.cos(2 * np.pi * month / 12)
            hour_sin = np.sin(2 * np.pi * hour / 24)
            hour_cos = np.cos(2 * np.pi * hour / 24)

            features.append({
                'month': month,
                'day': day,
                'hour': hour,
                'day_of_week': day_of_week,
                'day_of_year': day_of_year,
                'quarter': quarter,
                'is_weekend': is_weekend,
                'season': season,
                'month_sin': month_sin,
                'month_cos': month_cos,
                'hour_sin': hour_sin,
                'hour_cos': hour_cos
            })

        return pd.DataFrame(features)

    def predict(self, dates: List[datetime]) -> pd.DataFrame:
        """
        Verilen tarihler için hava durumu tahmini yap

        Args:
            dates (List[datetime]): Tahmin yapılacak tarih listesi

        Returns:
            pd.DataFrame: Tarih ve tahmin sütunları içeren DataFrame
        """
        if self.model is None:
            print("❌ Hata: Model yüklenmedi!")
            return pd.DataFrame()

        try:
            # Modelin beklediği özellikleri hesapla
            features_df = self.create_features(dates)

            print(f"🔍 Hesaplanan özellikler: {list(features_df.columns)}")

            # Model ile tahmin yap
            predictions = self.model.predict(features_df)

            # Tahminler multi-output olabilir, düzelt
            if predictions.ndim > 1:
                # Eğer birden fazla çıktı varsa, ilkini al veya ortalama al
                if predictions.shape[1] == 1:
                    predictions = predictions.flatten()
                else:
                    # Çok çıktılı model - her çıktı için ayrı sütun oluştur
                    result_df = pd.DataFrame({
                        'date': [date.strftime('%Y-%m-%d') for date in dates]
                    })

                    for i in range(predictions.shape[1]):
                        result_df[f'prediction_{i + 1}'] = predictions[:, i]

                    return result_df

            # Sonuçları DataFrame olarak döndür
            result_df = pd.DataFrame({
                'date': [date.strftime('%Y-%m-%d') for date in dates],
                'prediction': predictions
            })

            return result_df

        except Exception as e:
            print(f"❌ Tahmin hatası: {str(e)}")
            print("💡 Özellik hesaplama veya model tahmini başarısız")
            return pd.DataFrame()

    def get_next_week_dates(self) -> List[datetime]:
        """
        Bugünden itibaren önümüzdeki 7 gün için tarih listesi üret
        """
        today = datetime.now().date()
        dates = []

        for i in range(7):
            future_date = today + timedelta(days=i)
            dates.append(datetime.combine(future_date, datetime.min.time()))

        return dates

    def parse_custom_dates(self, date_strings: List[str]) -> List[datetime]:
        """
        String formatındaki tarihleri datetime objelerine çevir
        """
        parsed_dates = []

        for date_str in date_strings:
            try:
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                parsed_dates.append(parsed_date)
            except ValueError:
                print(f"❌ Geçersiz tarih formatı: {date_str} (YYYY-MM-DD formatında olmalı)")

        return parsed_dates

    def print_predictions_table(self, predictions_df: pd.DataFrame, title: str):
        """
        Tahminleri tablo halinde yazdır
        """
        if predictions_df.empty:
            print(f"❌ {title} için tahmin sonucu bulunamadı!")
            return

        print(f"\n{'=' * 70}")
        print(f"{title:^70}")
        print(f"{'=' * 70}")

        # Multi-output model kontrolü
        prediction_columns = [col for col in predictions_df.columns if col.startswith('prediction')]

        if len(prediction_columns) > 1:
            # Çoklu çıktı için başlık
            header = f"{'Tarih':<12}"
            for i, col in enumerate(prediction_columns):
                header += f" | {'Tahmin ' + str(i + 1):<15}"
            print(header)
            print(f"{'-' * 70}")

            for _, row in predictions_df.iterrows():
                line = f"{row['date']:<12}"
                for col in prediction_columns:
                    line += f" | {row[col]:<15.4f}"
                print(line)

        elif 'prediction' in predictions_df.columns:
            # Tek çıktı için başlık
            print(f"{'Tarih':<12} | {'Tahmin':<35}")
            print(f"{'-' * 70}")

            for _, row in predictions_df.iterrows():
                print(f"{row['date']:<12} | {row['prediction']:<35.4f}")
        else:
            print("❌ Tahmin sütunu bulunamadı!")
            print(f"Mevcut sütunlar: {list(predictions_df.columns)}")
            return

        print(f"{'=' * 70}\n")

    def test_model_info(self):
        """
        Model hakkında bilgi ver ve test et
        """
        if self.model is None:
            print("❌ Model yüklenmedi, test yapılamıyor!")
            return

        print("\n🔍 Model Bilgileri:")
        print(f"Model tipi: {type(self.model)}")

        # Model özelliklerini kontrol et
        if hasattr(self.model, 'feature_names_in_'):
            expected_features = list(self.model.feature_names_in_)
            print(f"Beklenen özellikler ({len(expected_features)}): {expected_features}")

        if hasattr(self.model, 'n_features_in_'):
            print(f"Özellik sayısı: {self.model.n_features_in_}")

        # Test tahmini yap
        try:
            print("\n🧪 Test tahmini yapılıyor...")
            test_date = datetime(2024, 10, 1)  # Test tarihi
            test_features = self.create_features([test_date])

            print(f"Oluşturulan özellikler: {list(test_features.columns)}")
            print(f"Test verileri:\n{test_features}")

            test_prediction = self.model.predict(test_features)
            print(f"✅ Test tahmini başarılı!")
            print(f"Tahmin sonucu: {test_prediction}")
            print(f"Tahmin şekli: {test_prediction.shape}")

        except Exception as e:
            print(f"❌ Test tahmin hatası: {str(e)}")
            print("💡 Özellik hesaplama veya eşleştirme sorunu olabilir")


def main():
    """
    Ana fonksiyon - Hava durumu tahmin uygulamasını çalıştır
    """
    print("🌤️  Hava Durumu Tahmin Uygulaması")
    print("=" * 50)

    # Tahmin sınıfını başlat
    predictor = WeatherPredictor("weather_prediction_model.pkl")

    if predictor.model is None:
        print("\n🛠️  Model Yükleme Sorun Giderme Tamamlandı")
        print("❌ Model hiçbir yöntemle yüklenemedi!")
        print("Program sonlandırılıyor...")
        return

    # Model bilgilerini göster
    predictor.test_model_info()

    # 1. Önümüzdeki 1 hafta için tahmin
    print("\n📅 Önümüzdeki 7 gün için tahmin hesaplanıyor...")
    next_week_dates = predictor.get_next_week_dates()
    weekly_predictions = predictor.predict(next_week_dates)

    # 2. Özel tarihler için tahmin
    custom_date_strings = [
        "2024-12-25",  # Noel
        "2024-12-31",  # Yılbaşı
        "2025-01-01",  # Yeni yıl
        "2025-02-14",  # Sevgililer günü
        "2025-03-15"  # Örnek tarih
    ]

    print(f"\n📋 Özel tarihler için tahmin hesaplanıyor...")
    print(f"Tarihler: {', '.join(custom_date_strings)}")

    custom_dates = predictor.parse_custom_dates(custom_date_strings)
    custom_predictions = predictor.predict(custom_dates)

    # 3. Sonuçları tablo halinde yazdır
    predictor.print_predictions_table(
        weekly_predictions,
        "ÖNÜMÜZDEKI 7 GÜN TAHMİNLERİ"
    )

    predictor.print_predictions_table(
        custom_predictions,
        "ÖZEL TARİHLER İÇİN TAHMİNLER"
    )

    # 4. Özet bilgi
    if not weekly_predictions.empty or not custom_predictions.empty:
        print("📊 Özet:")
        print(f"- Haftalık tahmin sayısı: {len(weekly_predictions)}")
        print(f"- Özel tarih tahmin sayısı: {len(custom_predictions)}")
        print(f"- Toplam tahmin sayısı: {len(weekly_predictions) + len(custom_predictions)}")

        # Model çıktı bilgisi
        if not weekly_predictions.empty:
            prediction_cols = [col for col in weekly_predictions.columns if col.startswith('prediction')]
            if len(prediction_cols) > 1:
                print(f"- Model çıktı sayısı: {len(prediction_cols)} (çoklu hedef tahmini)")
                print("  💡 Bu muhtemelen sıcaklık, nem, basınç gibi farklı hava parametreleri")
            else:
                print("- Model çıktı sayısı: 1 (tek hedef tahmini)")

        print("\n✅ Tahmin işlemleri tamamlandı!")
    else:
        print("❌ Hiçbir tahmin yapılamadı!")


if __name__ == "__main__":
    main()


# DEBUG VERSİYONU - Sorun giderme için
def debug_model_file(model_path: str = "weather_prediction_model.pkl"):
    """
    Model dosyasını debug etmek için özel fonksiyon
    """
    import os

    print("🐛 DEBUG MODU")
    print("=" * 40)

    print(f"📂 Çalışma dizini: {os.getcwd()}")
    print(f"📁 Dizindeki tüm dosyalar:")
    for file in os.listdir('.'):
        print(f"  - {file}")

    if os.path.exists(model_path):
        file_size = os.path.getsize(model_path)
        print(f"✅ Model dosyası bulundu: {model_path}")
        print(f"📏 Dosya boyutu: {file_size} bytes")

        # İlk birkaç byte'ı oku
        try:
            with open(model_path, 'rb') as f:
                first_100_bytes = f.read(100)
                print(f"📄 İlk 100 byte: {first_100_bytes}")
        except Exception as e:
            print(f"❌ Dosya okuma hatası: {e}")
    else:
        print(f"❌ Model dosyası bulunamadı: {model_path}")

# Debug fonksiyonunu çalıştırmak için:
# debug_model_file("weather_prediction_model.pkl")