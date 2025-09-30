# 🌦️ WeatherWidget – Masaüstü Hava Durumu Widget’ı

WeatherWidget, geçmiş 10 yıllık meteorolojik veriyi analiz ederek güncel hava tahminlerini **tutarlılık yüzdesi** ile birlikte sunan modern bir masaüstü widget uygulamasıdır.  
Bu proje, geliştiricilerin ekip çalışması deneyimi kazanması ve teknik tecrübelerini artırması amacıyla hayata geçirilmiştir.

---

## 🎯 Projenin Amacı

- Ekip projesi deneyimi kazanmak
- Veri işleme kütüphaneleri ile geçmiş yıllara ait ve gerçek bir hava durumu analiz sistemi kurmak
- Python ve PyQt5 teknolojilerini kullanarak masaüstü geliştirme becerilerini artırmak
- Şık, modern ve işlevsel bir masaüstü widget geliştirmek

---

## 🛠️ Teknik Altyapı

- **Dil & Framework:** Python 3.11, PyQt5
- **Veri İşleme:** Pandas, NumPy, Scikit-learn
- **Arayüz:** PyQt5 tabanlı modern UI, Temalar
- **Dağıtım:** `build.bat` ile `.exe` çıktısı üretimi

---

## 🚀 Özellikler

- 📊 **Geçmişe Dayalı Analiz:** Güncel hava durumunu geçmiş 10 yılın verileriyle kıyaslar
- 🌧️ **Tutarlılık Yüzdesi:** “Bugün yağmurlu (%88 tutarlılık)” gibi destekleyici etiketler üretir
- 🖥️ **Modern Arayüz:** Minimalist ve kullanıcı dostu tasarım
- 🎨 **Tema Desteği:** Dark ve Light mode seçenekleri
- 🔄 **Esnek Kullanım:** Widget farklı boyutlarda olabilir veya görev çubuğuna alınabilir
- 📷 **Görsel Destek:** Ekran görüntüleri ve gif örnekleri ile kullanım önizlemesi

---

## 📥 Kurulum ve Kullanım

### 1. Kaynak Koddan Çalıştırma

```bash
git clone https://github.com/kullanici/weatherwidget.git
cd weatherwidget
pip install -r requirements.txt
python main.py
```

---

## 1. Geliştirme Ortamında Çalıştırma

```bash
pip install -r requirements.txt
python src/app.py
```

---

## 2. EXE Üzerinden Kullanım

- `build.bat` dosyasını çalıştırarak `.exe` çıktısını alın\
- Üretilen `.exe` dosyasını çift tıklayarak uygulamayı çalıştırın

---

### 1️⃣ Model Hariç Gömme (Tavsiye Edilen)

Bu yöntemde exe dosyasına **tüm kütüphaneler + QSS temaları + ikonlar**
gömülür,\
ancak `weather_prediction_model.joblib` ayrı tutulur.\
Böylece modeli gerektiğinde kolayca güncelleyebilirsiniz.

#### Adımlar:

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole src/app.py ^
  --name WeatherWidget ^
  --add-data "src/frontend/assets/styles_dark.qss;assets" ^
  --add-data "src/frontend/assets/styles_light.qss;assets" ^
  --add-data "src/frontend/assets/figma;figma" ^
  --icon=src/frontend/assets/app.ico
```

#### Kullanım:

- Oluşan `dist/WeatherWidget.exe` dosyasını çalıştırın.\
- `weather_prediction_model.joblib` dosyasını exe ile aynı klasöre
  koyun.\
- Eğer model bulunamazsa, uygulama aynı klasörde bir `error.txt`
  oluşturur ve\
  içinde `model.joblib bulunamadı` uyarısı yer alır.

---

### 2️⃣ Model Dahil Gömme

Bu yöntemde model de exe içine gömülür.\
Tek dosya ile dağıtım yapılabilir ancak modeli güncellemek için exe'yi
yeniden üretmek gerekir.

#### Adımlar:

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole src/app.py ^
  --name WeatherWidget ^
  --add-data "src/frontend/views/weather_prediction_model.joblib;." ^
  --add-data "src/frontend/assets/styles_dark.qss;assets" ^
  --add-data "src/frontend/assets/styles_light.qss;assets" ^
  --add-data "src/frontend/assets/figma;figma" ^
  --icon=src/frontend/assets/app.ico
```

#### Kullanım:

- `dist/WeatherWidget.exe` dosyasını doğrudan çalıştırın.\
- Model exe içine gömülü olduğundan ayrıca kopyalamanız gerekmez.

---

## 3. Notlar

- Windows için `--add-data` parametresinde ayraç `;` kullanılmalıdır.\
- Linux/Mac için `:` kullanılmalıdır.\
- `app.ico` uygulama ikonunuzdur, yoksa çıkarabilirsiniz.

---

## 3️⃣ Ek Notlar

- Stil dosyaları (`styles_dark.qss`, `styles_light.qss`) ve `assets/` klasörü de `--add-data` parametresi ile gömülmelidir.
- Eğer tray ikonu veya görseller kullanılacaksa, ilgili yollar da eklenmelidir. Örnek:

```bash
--add-data "src/frontend/assets;frontend/assets"
```

---

## Özet

- **Versiyon 1 (Model Hariç):** Daha esnek, güncelleme kolay.
- **Versiyon 2 (Model Dahil):** Tek dosya, ama model güncellemesi için tekrar derleme gerek.

---

## 📸 Ekran Görüntüleri

### Açık Tema

### Koyu Tema

---

## 📁 Katkıda Bulunma

Projeye katkıda bulunmak isteyenlerin profesyonel süreçleri takip etmesi beklenir:

1. Fork → Branch açma → Geliştirme yapma
2. Pull request açma → Code review süreci
3. Issue açma ve tartışma kurallarına uyma

---

## 📂 Proje Yapısı

```
weatherinsight/
│
├── docs/                # Dokümantasyon ve diyagramlar
│   └── screenshots/     # README için ekran görüntüleri
│
├── src/                 # Kaynak kod
│   ├── backend/         # Veri işleme, modeller, analiz
│   │   └── .gitkeep     # Yer tutucu (dosyalar eklendiğinde silin)
│   │
│   ├── frontend/        # PyQt5 arayüzü, temalar ve varlıklar
│   │   ├── themes/      # Koyu & Açık temalar
│   │   │   └── .gitkeep
│   │   └── assets/      # İkonlar, görseller
│   │       └── .gitkeep
│   │
│   └── main.py          # Giriş noktası
│
├── tests/               # Birim testleri
│   └── .gitkeep
│
├── build/               # Derlenmiş çalıştırılabilir dosyalar (otomatik üretilir)
│   └── .gitkeep
│
├── requirements.txt     # Python bağımlılıkları
├── build.bat            # exe oluşturma scripti
├── README.md
└── LICENSE
```

---

## 📁 Depo Yapısı Hakkında Notlar

- Bazı dizinlerde `placeholder.txt` dosyası bulunabilir.
- Bu dosyalar yalnızca klasör yapısının Git tarafından takip edilmesini sağlamak için eklenmiştir.
- Gerçek içerik eklendikten sonra bu dosyaların silinmesi gerekir.

---

Projeye katkıda bulunmak isteyenlerin profesyonel süreçleri takip etmesi beklenir:

1. Fork → Branch açma → Geliştirme yapma
2. Pull request açma → Code review süreci
3. Issue açma ve tartışma kurallarına uyma

---

## 👨‍💻 Geliştirici Ekibi

- **Mert Taban** – Data Analysis
- **Umut Eren Demir** – UI/UX Design
- **Berat Tezer** – Backend & Team Lead

---

## 📄 Lisans

Bu proje **özel kullanım lisansı** altındadır.  
Kaynak kodun veya derlenmiş sürümlerin kullanımı, çoğaltılması ve dağıtılması yalnızca **geliştirici ekibin yazılı izni** ile mümkündür.

Tüm hakları saklıdır © 2025

---
