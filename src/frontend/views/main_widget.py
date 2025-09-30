from __future__ import annotations

import asyncio
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PySide6.QtCore import QEvent, QPoint, QSettings, Qt
from PySide6.QtGui import QAction, QColor, QIcon, QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from backend.weather_service import (
    describe_weather,
    fetch_current_weather,
    fetch_weather_bundle,
)


def _base_dir() -> Path:
    # PyInstaller ile çalışıyorsa, geçici unpack klasörü (MEIPASS)
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    # Geliştirme ortamı: main_widget.py -> ../assets
    return Path(__file__).resolve().parent.parent


def resource_path(*parts: str) -> Path:
    return _base_dir().joinpath(*parts)


# ---- Assets dizinlerini burada topla ----
ASSETS_DIR = resource_path("assets")
FIGMA_DIR = resource_path("assets", "figma")  # figma assets klasörü assets altında


# ✅ Doğru import: dosya adı weather_predictor.py olmalı
from .weather_predictor import WeatherPredictor

# -------- Assets & city DB --------
ASSETS_DIR = (Path(__file__).resolve().parent.parent / "assets").resolve()
FIGMA_DIR = ASSETS_DIR / "figma"


def load_city_db() -> Dict[str, Dict[str, Tuple[float, float]]]:
    path = ASSETS_DIR / "cities.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        fixed = {
            country: {
                city: (float(lat), float(lon)) for city, (lat, lon) in cities.items()
            }
            for country, cities in data.items()
        }
        return fixed
    except Exception as e:
        print("[WARN] cities.json okunamadı:", e)
        return {"Türkiye": {"Karabük": (41.2040, 32.6260)}}


CITY_DB: Dict[str, Dict[str, Tuple[float, float]]] = load_city_db()


def pick_icon_path(code: Optional[int], is_day: int) -> Path:
    if code is None:
        return FIGMA_DIR / "cloudy.png"
    if code in (95, 96, 99):
        return FIGMA_DIR / "stormy.png"
    if 71 <= code <= 77 or code in (85, 86):
        return FIGMA_DIR / "snow.png"
    if code in (80, 81, 82) or 61 <= code <= 67 or 51 <= code <= 57:
        return FIGMA_DIR / "rainy.png"
    if code in (45, 48, 3):
        return FIGMA_DIR / "cloudy.png"
    if code in (1, 2):
        return FIGMA_DIR / ("partlycloudy.png" if is_day else "night.png")
    if code == 0:
        return FIGMA_DIR / ("sunny.png" if is_day else "night.png")
    return FIGMA_DIR / "cloudy.png"


# Türkçe kısa gün adları (Mon=0)
TR_WD = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]


# -------- LocationDialog (temalı kart) --------
class LocationDialog(QDialog):
    def __init__(self, parent=None, current_country="Türkiye", current_city="Karabük"):
        super().__init__(parent)
        self.setWindowTitle("Konum Seç")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.panel = QFrame(self)
        self.panel.setObjectName("card")
        outer.addWidget(self.panel)

        root = QVBoxLayout(self.panel)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        shadow = QGraphicsDropShadowEffect(self.panel)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 6)
        shadow.setColor(Qt.black)
        self.panel.setGraphicsEffect(shadow)

        self.country = QComboBox(self.panel)
        self.city = QComboBox(self.panel)

        self.country.addItems(list(CITY_DB.keys()))
        if current_country in CITY_DB:
            self.country.setCurrentText(current_country)

        def load_cities(cn: str):
            self.city.clear()
            self.city.addItems(list(CITY_DB.get(cn, {}).keys()))
            if current_city in CITY_DB.get(cn, {}):
                self.city.setCurrentText(current_city)

        load_cities(self.country.currentText())
        self.country.currentTextChanged.connect(load_cities)

        root.addWidget(QLabel("Ülke:", self.panel))
        root.addWidget(self.country)
        root.addWidget(QLabel("Şehir:", self.panel))
        root.addWidget(self.city)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self.panel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.adjustSize()
        if parent:
            geo = parent.frameGeometry()
            self.move(geo.center() - self.rect().center())

    def selected(self) -> Tuple[str, str]:
        return self.country.currentText(), self.city.currentText()


# -------- MainWidget --------
class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._drag_pos = QPoint()
        self._drag_active = False
        self._fetch_lock = asyncio.Lock()
        self._last_bundle: Optional[Dict[str, Any]] = None

        self.settings = QSettings("YourOrg", "WeatherWidget")
        self._cache_key = "last_bundle_json"

        # ✨ MODEL: yükle (model dosyası bu dosyayla aynı klasörde veya otomatik bulunur)
        self.predictor: Optional[WeatherPredictor] = None
        try:
            # WeatherPredictor içi otomatik yol buluyor; None geçilebilir
            tmp = WeatherPredictor(None)
            if getattr(tmp, "model", None) is not None:
                self.predictor = tmp
            else:
                print("[consistency] Model yüklenemedi (model=None).")
        except Exception as e:
            print("[consistency] model init failed:", e)
            self.predictor = None

        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnBottomHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.card = QFrame(self)
        self.card.setObjectName("card")
        outer.addWidget(self.card)

        self.root = QVBoxLayout(self.card)
        self.root.setContentsMargins(10, 10, 10, 10)  # kompakt
        self.root.setSpacing(6)

        # Header
        header = QFrame(self.card)
        header.setObjectName("header")
        h = QHBoxLayout(header)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(6)

        country = self.settings.value("geo_country", "Türkiye")
        city = self.settings.value("geo_city", "Karabük")
        self.location_label = QLabel(f"{city}, {country}", header)
        self.location_label.setObjectName("locationLabel")
        h.addWidget(self.location_label)
        h.addStretch(1)

        self.settings_btn = QPushButton("", header)
        self.settings_btn.setObjectName("settingsBtn")
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.setFixedSize(24, 24)
        gear = ASSETS_DIR / "gear.svg"
        if gear.exists():
            self.settings_btn.setIcon(QIcon(str(gear)))
        else:
            self.settings_btn.setText("⚙")
        self.settings_btn.clicked.connect(self.open_settings_menu)
        h.addWidget(self.settings_btn)

        self.root.addWidget(header)
        header.installEventFilter(self)

        # ---- Dinamik içerik alanı ----
        self.content_frame = QFrame(self.card)
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(4)  # sıkı
        self.root.addWidget(self.content_frame)

        # Consistency (sabit)
        self.consistency_row = QFrame(self.card)
        c = QHBoxLayout(self.consistency_row)
        c.setContentsMargins(0, 0, 0, 0)
        c.setSpacing(6)
        ai_png = ASSETS_DIR / "ai.png"
        self.consistency_icon = QLabel(self.consistency_row)

        tip = "Modelimizin hava durumu tahminine yönelik hesapladığı tutarlılık puanı"
        self.consistency_icon.setToolTip(tip)

        if ai_png.exists():
            pix = QPixmap(str(ai_png)).scaled(
                14, 14, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.consistency_icon.setPixmap(pix)
        else:
            self.consistency_icon.setText("🤖")
        self.consistency_label = QLabel("—", self.consistency_row)  # başlangıçta boş
        self.consistency_label.setObjectName("consistency")
        c.addWidget(self.consistency_icon)
        c.addWidget(self.consistency_label)
        c.addStretch(1)
        self.root.addWidget(self.consistency_row)

        # Init
        self.apply_size(self.settings.value("size", "small"))
        self.apply_theme(self.settings.value("theme", "dark"))

        if pt := self.settings.value("pos"):
            try:
                x, y = map(int, str(pt).split(","))  # type: ignore
                self.move(x, y)
            except Exception:
                pass

        self._lat, self._lon = self.resolve_coords(country, city)

    # ----- Drag -----
    def eventFilter(self, obj, event):
        if obj.objectName() == "header":
            et = event.type()
            if et == QEvent.Type.MouseButtonPress and isinstance(event, QMouseEvent):
                if event.button() == Qt.LeftButton:
                    self._drag_active = True
                    self._drag_pos = (
                        event.globalPosition().toPoint()
                        - self.frameGeometry().topLeft()
                    )
                    return True
            elif (
                et == QEvent.Type.MouseMove
                and self._drag_active
                and isinstance(event, QMouseEvent)
            ):
                self.move(event.globalPosition().toPoint() - self._drag_pos)
                return True
            elif et == QEvent.Type.MouseButtonRelease and isinstance(
                event, QMouseEvent
            ):
                self._drag_active = False
                return True
        return super().eventFilter(obj, event)

    # ----- Menu -----
    def open_settings_menu(self):
        menu = QMenu(self)
        menu.setProperty("smallMenu", (self.card.property("sizeVariant") == "small"))

        size_menu = menu.addMenu("Boyut")
        for key, text in [("small", "Küçük"), ("medium", "Orta"), ("large", "Büyük")]:
            act = QAction(text, self, checkable=True)
            act.setChecked(self.settings.value("size", "small") == key)
            act.triggered.connect(lambda _, k=key: self.apply_size(k))
            size_menu.addAction(act)

        pos_menu = menu.addMenu("Ekran Konumu")
        for key, text in [
            ("tl", "Sol-Üst"),
            ("tr", "Sağ-Üst"),
            ("bl", "Sol-Alt"),
            ("br", "Sağ-Alt"),
        ]:
            act = QAction(text, self)
            act.triggered.connect(lambda _, k=key: self.snap_to(k))
            pos_menu.addAction(act)
        save_pos = QAction("Şimdiki konumu kaydet", self)
        save_pos.triggered.connect(self.save_current_pos)
        pos_menu.addAction(save_pos)

        theme_menu = menu.addMenu("Tema")
        for key, text in [("dark", "Modern Karanlık"), ("light", "Modern Aydınlık")]:
            act = QAction(text, self, checkable=True)
            act.setChecked(self.settings.value("theme", "dark") == key)
            act.triggered.connect(lambda _, k=key: self.apply_theme(k))
            theme_menu.addAction(act)

        menu.addSeparator()
        geo_act = QAction("Konumu Değiştir (Ülke/Şehir)…", self)
        geo_act.triggered.connect(self.change_geo_location)
        menu.addAction(geo_act)

        refresh_act = QAction("Şimdi güncelle", self)
        refresh_act.triggered.connect(lambda: asyncio.create_task(self._safe_update()))
        menu.addAction(refresh_act)

        menu.exec(self.settings_btn.mapToGlobal(self.settings_btn.rect().bottomRight()))

    async def _safe_update(self):
        try:
            await self.update_weather_once()
        except Exception as e:
            print("[refresh] error:", e)

    # ----- Helpers -----
    def _icon_px_for_variant(self) -> int:
        v = self.card.property("sizeVariant") or "small"
        return 18 if v == "small" else (20 if v == "medium" else 22)

    def apply_size(self, key: str):
        # small daha dar; medium 5 gün; large kompakt saatlik
        if key == "small":
            w, h, variant = 180, 160, "small"
            spacing = 4
        elif key == "medium":
            w, h, variant = 180, 260, "medium"
            spacing = 5
        else:
            w, h, variant = 360, 180, "large"
            spacing = 4
        self.setFixedSize(w, h)
        self.card.setProperty("sizeVariant", variant)
        self.content_layout.setSpacing(spacing)
        for wgt in [self.card, self]:
            wgt.style().unpolish(wgt)
            wgt.style().polish(wgt)
        self.settings.setValue("size", key)
        self.render_content()  # tam temiz çiz

    def apply_theme(self, key: str):
        self.settings.setValue("theme", key)
        app = QApplication.instance()
        if hasattr(app, "load_styles"):
            app.load_styles(key)
        # Karanlıkta ikonlara "glow", aydınlıkta kaldır
        self._apply_glow_for_dark(is_dark=(key == "dark"))
        for w in [self.card, self]:
            w.style().unpolish(w)
            w.style().polish(w)

    def _apply_glow_for_dark(self, is_dark: bool):
        widgets = [self.settings_btn, self.consistency_icon]
        if is_dark:
            for w in widgets:
                eff = QGraphicsDropShadowEffect(self)
                eff.setBlurRadius(16)
                eff.setOffset(0)
                eff.setColor(QColor(255, 255, 255, 180))
                w.setGraphicsEffect(eff)
        else:
            for w in widgets:
                w.setGraphicsEffect(None)

    def snap_to(self, corner: str):
        screen = QApplication.primaryScreen().availableGeometry()
        m = 10
        if corner == "tl":
            x, y = m, m
        elif corner == "tr":
            x, y = screen.width() - self.width() - m, m
        elif corner == "bl":
            x, y = m, screen.height() - self.height() - m
        else:
            x, y = (
                screen.width() - self.width() - m,
                screen.height() - self.height() - m,
            )
        self.move(x, y)
        self.save_current_pos()

    def save_current_pos(self):
        self.settings.setValue("pos", f"{self.x()},{self.y()}")

    def resolve_coords(self, country: str, city: str) -> Tuple[float, float]:
        return CITY_DB.get(country, {}).get(city, (41.0082, 28.9784))

    # ----- Loop & update -----
    async def start_weather_loop(self, interval_minutes: int = 5):
        while True:
            try:
                await self.update_weather_once()
            except Exception as e:
                print("[weather loop] error:", e)
            await asyncio.sleep(interval_minutes * 60)

    async def update_weather_once(self):
        async with self._fetch_lock:
            lat, lon = getattr(self, "_lat", None), getattr(self, "_lon", None)
            if lat is None or lon is None:
                return
            bundle = await fetch_weather_bundle(lat, lon, forecast_days=5)
            if not bundle:
                # offline cache
                cached = self._load_cache()
                if cached:
                    print("[weather] using cached bundle")
                    self._last_bundle = cached
                    self._update_consistency_from_bundle()
                    self.render_content()
                    return
                # son çare: sadece current
                current = await fetch_current_weather(lat, lon)
                if not current:
                    self._last_bundle = None
                    self._clear_layout_recursive(self.content_layout)
                    self.content_layout.addWidget(
                        self._make_label("Bağlantı yok", "condition")
                    )
                    self.consistency_label.setText("—")
                    self.consistency_label.setToolTip(
                        "Model tutarlılığı hesaplanamadı."
                    )
                    return
                bundle = {"current": current, "hourly": {}, "daily": {}}
            self._last_bundle = bundle
            self._save_cache(bundle)
            self._update_consistency_from_bundle()
            self.render_content()

    # ----- Cache helpers -----
    def _save_cache(self, bundle: Dict[str, Any]):
        try:
            s = QSettings("YourOrg", "WeatherWidget")
            s.setValue(self._cache_key, json.dumps(bundle))
        except Exception:
            pass

    def _load_cache(self) -> Optional[Dict[str, Any]]:
        try:
            s = QSettings("YourOrg", "WeatherWidget")
            raw = s.value(self._cache_key)
            if raw:
                return json.loads(raw)
        except Exception:
            return None
        return None

    # ----- Layout clear (derin) -----
    def _clear_layout_recursive(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            ch = item.layout()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
            if ch is not None:
                self._clear_layout_recursive(ch)

    # ----- Rendering -----
    def render_content(self):
        self._clear_layout_recursive(self.content_layout)

        v = self.card.property("sizeVariant") or "small"
        if not self._last_bundle:
            self.content_layout.addWidget(self._make_label("— °C", "tempValue"))
            self.content_layout.addWidget(self._make_label("—", "condition"))
            return

        current = self._last_bundle.get("current", {})
        hourly = self._last_bundle.get("hourly", {})
        daily = self._last_bundle.get("daily", {})

        if v == "small":
            self._render_small(current, daily)
        elif v == "medium":
            self._render_five_day_vertical(daily)
        else:
            # "şu andan itibaren" hizalı saatlik görünüm
            self._render_next_hours(hourly, start_from_now=True, step_hours=3, slots=8)

    def _render_small(self, current: Dict[str, Any], daily: Dict[str, Any]):
        cur_temp = current.get("temperature")
        cur_code = current.get("weathercode")
        cur_is_day = int(current.get("is_day", 1))
        icon_path = pick_icon_path(cur_code, cur_is_day)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        icon_lbl = QLabel(self.content_frame)
        icon_lbl.setObjectName("weatherIcon")
        if icon_path.exists():
            size = self._icon_px_for_variant()
            icon_lbl.setPixmap(
                QPixmap(str(icon_path)).scaled(
                    size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )
        row.addWidget(icon_lbl)

        temp_lbl = self._make_label(
            f"{int(round(cur_temp))} °C" if cur_temp is not None else "— °C",
            "tempValue",
        )
        row.addWidget(temp_lbl)
        row.addStretch(1)
        self.content_layout.addLayout(row)
        self.content_layout.addWidget(
            self._make_label(describe_weather(cur_code), "condition")
        )

        # bugün min
        if daily.get("temperature_2m_min"):
            today_min = daily["temperature_2m_min"][0]
            if today_min is not None:
                low_lbl = QLabel(
                    f"Bugün en düşük: {int(round(today_min))} °C", self.content_frame
                )
                self.content_layout.addWidget(low_lbl)

    def _render_five_day_vertical(self, daily: Dict[str, Any]):
        times: List[str] = daily.get("time", []) or []
        mins: List[Optional[float]] = daily.get("temperature_2m_min", []) or []
        maxs: List[Optional[float]] = daily.get("temperature_2m_max", []) or []
        codes: List[Optional[int]] = daily.get("weathercode", []) or []

        # 5 güne kadar göster
        n = min(5, len(times))
        today_iso = date.today().isoformat()

        for i in range(n):
            # tek satır: [ikon] [başlık] [max/min°]
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(6)

            code = codes[i] if i < len(codes) else None
            icon = pick_icon_path(code, 1)
            icon_lbl = QLabel(self.content_frame)
            icon_lbl.setObjectName("weatherIcon")
            if icon.exists():
                size = self._icon_px_for_variant()
                icon_lbl.setPixmap(
                    QPixmap(str(icon)).scaled(
                        size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                )
            row.addWidget(icon_lbl)

            # Başlık: Bugün / Yarın / Gün kısaltması
            title = "—"
            try:
                d = datetime.fromisoformat(times[i]).date()
                if times[i].startswith(today_iso):
                    title = "Bugün"
                elif (d - date.today()).days == 1:
                    title = "Yarın"
                else:
                    title = TR_WD[d.weekday()]
            except Exception:
                title = "—"
            title_lbl = QLabel(title, self.content_frame)
            row.addWidget(title_lbl)

            max_str = (
                int(round(maxs[i])) if i < len(maxs) and maxs[i] is not None else None
            )
            min_str = (
                int(round(mins[i])) if i < len(mins) and mins[i] is not None else None
            )
            combo = (
                f"{max_str}/{min_str}°"
                if (max_str is not None and min_str is not None)
                else "—"
            )
            mm_lbl = QLabel(combo, self.content_frame)

            row.addStretch(1)
            row.addWidget(mm_lbl)

            self.content_layout.addLayout(row)

    def _render_next_hours(
        self, hourly: Dict[str, Any], start_from_now: bool, step_hours: int, slots: int
    ):
        times: List[str] = hourly.get("time", []) or []
        temps: List[Optional[float]] = hourly.get("temperature_2m", []) or []
        codes: List[Optional[int]] = hourly.get("weathercode", []) or []
        is_day: List[int] = hourly.get("is_day", []) or []

        if not times:
            self.content_layout.addWidget(
                self._make_label("Saatlik veri yok", "condition")
            )
            return

        start_idx = 0
        if start_from_now:
            start_idx = self._nearest_future_index(times)

        idxs = list(
            range(
                start_idx, min(len(times), start_idx + step_hours * slots), step_hours
            )
        )
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        for idx in idxs[:slots]:
            col = QVBoxLayout()
            col.setContentsMargins(0, 0, 0, 0)
            col.setSpacing(0)

            try:
                t = datetime.fromisoformat(times[idx])
                t_label = QLabel(t.strftime("%H:%M"), self.content_frame)
            except Exception:
                t_label = QLabel("—", self.content_frame)
            t_label.setAlignment(Qt.AlignHCenter)
            col.addWidget(t_label)

            code = codes[idx] if idx < len(codes) else None
            dayf = int(is_day[idx]) if idx < len(is_day) else 1
            icon = pick_icon_path(code, dayf)
            icon_lbl = QLabel(self.content_frame)
            icon_lbl.setObjectName("weatherIcon")
            if icon.exists():
                size = self._icon_px_for_variant()
                icon_lbl.setPixmap(
                    QPixmap(str(icon)).scaled(
                        size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                )
            icon_lbl.setAlignment(Qt.AlignHCenter)
            col.addWidget(icon_lbl)

            temp = temps[idx] if idx < len(temps) else None
            temp_lbl = QLabel(
                f"{int(round(temp))}°" if temp is not None else "—", self.content_frame
            )
            temp_lbl.setAlignment(Qt.AlignHCenter)
            col.addWidget(temp_lbl)

            row.addLayout(col)

        self.content_layout.addLayout(row)

    def _nearest_future_index(self, iso_times: List[str]) -> int:
        """hourly time dizisinde 'şimdi'ye en yakın GELECEK/eşit saat indexi."""
        try:
            now = datetime.now()
            for i, t in enumerate(iso_times):
                try:
                    dt = datetime.fromisoformat(t)
                    if dt >= now:
                        return i
                except Exception:
                    continue
            return 0
        except Exception:
            return 0

    # ✨ MODEL tabanlı tutarlılık
    def _update_consistency_from_bundle(self):
        """
        self._last_bundle içindeki current sıcaklık ile model tahminini karşılaştır,
        % tutarlılık üret ve UI'a yaz.
        """
        try:
            if not self._last_bundle:
                self.consistency_label.setText("—")
                self.consistency_label.setToolTip("Model tutarlılığı hesaplanamadı.")
                return

            current = self._last_bundle.get("current", {})
            cur_temp = current.get("temperature")
            now = datetime.now()
            predict_dt = now.replace(minute=0, second=0, microsecond=0)

            if cur_temp is None or self.predictor is None:
                self.consistency_label.setText("—")
                tt = []
                if cur_temp is None:
                    tt.append("Anlık sıcaklık yok.")
                if self.predictor is None:
                    tt.append("Model yüklenmedi.")
                self.consistency_label.setToolTip(" ".join(tt) or "Hesaplanamadı.")
                return

            df = self.predictor.predict([predict_dt])
            if df is None or df.empty:
                self.consistency_label.setText("—")
                self.consistency_label.setToolTip("Model tahmini üretilemedi.")
                return

            if "prediction" in df.columns:
                pred = float(df["prediction"].iloc[0])
            else:
                pred_cols = [c for c in df.columns if c.startswith("prediction_")]
                pred = float(df[pred_cols[0]].iloc[0]) if pred_cols else None

            if pred is None or np.isnan(pred):
                self.consistency_label.setText("—")
                self.consistency_label.setToolTip("Model tahmini geçersiz.")
                return

            err = abs(float(cur_temp) - float(pred))
            # 0°C fark = 100%; 8°C fark ve üzeri = 0%
            score = max(0.0, 100.0 - (err / 8.0) * 100.0)
            score_i = int(round(score))

            self.consistency_label.setText(f"%{score_i} Tutarlılık")
            self.consistency_label.setToolTip(
                f"Model: {pred:.1f}°C · Anlık: {float(cur_temp):.1f}°C · Hata: {err:.1f}°C"
            )

        except Exception as e:
            print("[consistency] error:", e)
            self.consistency_label.setText("—")
            self.consistency_label.setToolTip("Model tutarlılığı hesaplanamadı.")

    def _make_label(self, text: str, obj_name: Optional[str] = None) -> QLabel:
        lbl = QLabel(text, self.content_frame)
        if obj_name:
            lbl.setObjectName(obj_name)
        return lbl

    # ----- Geo change -----
    def change_geo_location(self):
        try:
            current_city, current_country = [
                p.strip() for p in self.location_label.text().split(",", 1)
            ]
        except Exception:
            current_country, current_city = "Türkiye", "Karabük"
        dlg = LocationDialog(
            self, current_country=current_country, current_city=current_city
        )
        if dlg.exec() == QDialog.Accepted:
            country, city = dlg.selected()
            self.location_label.setText(f"{city}, {country}")
            self.settings.setValue("geo_country", country)
            self.settings.setValue("geo_city", city)
            self._lat, self._lon = self.resolve_coords(country, city)
            asyncio.create_task(self._safe_update())
