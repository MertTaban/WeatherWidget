from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Dict, Optional, Tuple

from PySide6.QtCore import QEvent, QPoint, QSettings, Qt
from PySide6.QtGui import QAction, QIcon, QMouseEvent, QPixmap
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

from backend.weather_service import describe_weather, fetch_current_weather

# -------- Helpers: paths & city DB --------
ASSETS_DIR = (Path(__file__).resolve().parent.parent / "assets").resolve()


def load_city_db() -> Dict[str, Dict[str, Tuple[float, float]]]:
    path = ASSETS_DIR / "cities.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        # tip güvenliği: list -> tuple
        fixed = {
            country: {
                city: (float(lat), float(lon)) for city, (lat, lon) in cities.items()
            }
            for country, cities in data.items()
        }
        return fixed
    except Exception as e:
        print("[WARN] cities.json okunamadı:", e)
        # en azından bir fallback bırak
        return {
            "Türkiye": {"İstanbul": (41.0082, 28.9784), "Karabük": (41.2040, 32.6260)},
        }


CITY_DB: Dict[str, Dict[str, Tuple[float, float]]] = load_city_db()


# -------- LocationDialog (tema uyumlu “kart” diyalog) --------
class LocationDialog(QDialog):
    def __init__(self, parent=None, current_country="Türkiye", current_city="İstanbul"):
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

        # soft shadow
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
        self.settings = QSettings("YourOrg", "WeatherWidget")

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.card = QFrame(self)
        self.card.setObjectName("card")
        outer.addWidget(self.card)

        self.root = QVBoxLayout(self.card)
        self.root.setContentsMargins(12, 12, 12, 12)
        self.root.setSpacing(8)

        # ----- Header (drag alanı) -----
        header = QFrame(self.card)
        header.setObjectName("header")
        h = QHBoxLayout(header)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)

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
        header.installEventFilter(self)  # drag sadece header'da

        # ----- Content -----
        self.temp_value = QLabel("— °C", self.card)
        self.temp_value.setObjectName("tempValue")
        self.root.addWidget(self.temp_value)

        self.condition_label = QLabel("—", self.card)
        self.condition_label.setObjectName("condition")
        self.root.addWidget(self.condition_label)

        # AI consistency: png + metin
        self.consistency_row = QFrame(self.card)
        c = QHBoxLayout(self.consistency_row)
        c.setContentsMargins(0, 0, 0, 0)
        c.setSpacing(6)
        ai_png = ASSETS_DIR / "ai.png"
        self.consistency_icon = QLabel(self.consistency_row)
        if ai_png.exists():
            pix = QPixmap(str(ai_png)).scaled(
                14, 14, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.consistency_icon.setPixmap(pix)
        else:
            self.consistency_icon.setText("🤖")
        self.consistency_label = QLabel("%87 Tutarlılık", self.consistency_row)
        self.consistency_label.setObjectName("consistency")
        c.addWidget(self.consistency_icon)
        c.addWidget(self.consistency_label)
        c.addStretch(1)
        self.root.addWidget(self.consistency_row)

        # ----- Başlangıç ayarları -----
        self.apply_size(self.settings.value("size", "small"))
        self.apply_theme(self.settings.value("theme", "dark"))

        # ekran konumu geri yükle
        if pt := self.settings.value("pos"):
            try:
                x, y = map(int, str(pt).split(","))
                self.move(x, y)
            except Exception:
                pass

        # şehir->koordinat
        self._lat, self._lon = self.resolve_coords(country, city)

    # ---------- Drag sadece header ----------
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
                if event.button() == Qt.LeftButton:
                    self._drag_active = False
                    return True
        return super().eventFilter(obj, event)

    # ---------- Menü ----------
    def open_settings_menu(self):
        menu = QMenu(self)

        # Boyut
        size_menu = menu.addMenu("Boyut")
        for key, text in [("small", "Küçük"), ("medium", "Orta"), ("large", "Büyük")]:
            act = QAction(text, self, checkable=True)
            act.setChecked(self.settings.value("size", "small") == key)
            act.triggered.connect(lambda _, k=key: self.apply_size(k))
            size_menu.addAction(act)

        # Ekran konumu
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

        # Tema
        theme_menu = menu.addMenu("Tema")
        for key, text in [("dark", "Modern Karanlık"), ("light", "Modern Aydınlık")]:
            act = QAction(text, self, checkable=True)
            act.setChecked(self.settings.value("theme", "dark") == key)
            act.triggered.connect(lambda _, k=key: self.apply_theme(k))
            theme_menu.addAction(act)

        # Coğrafi konum
        menu.addSeparator()
        geo_act = QAction("Konumu Değiştir (Ülke/Şehir)…", self)
        geo_act.triggered.connect(self.change_geo_location)
        menu.addAction(geo_act)

        # Manuel güncelle
        refresh_act = QAction("Şimdi güncelle", self)
        refresh_act.triggered.connect(
            lambda: asyncio.create_task(self.update_weather_once())
        )
        menu.addAction(refresh_act)

        menu.exec(self.settings_btn.mapToGlobal(self.settings_btn.rect().bottomRight()))

    # ---------- Helpers ----------
    def apply_size(self, key: str):
        if key == "small":
            w, h, variant = 240, 160, "small"
            self.root.setContentsMargins(12, 12, 12, 12)
            self.root.setSpacing(6)
        elif key == "medium":
            w, h, variant = 300, 200, "medium"
            self.root.setContentsMargins(14, 14, 14, 14)
            self.root.setSpacing(8)
        else:
            w, h, variant = 360, 240, "large"
            self.root.setContentsMargins(18, 18, 18, 18)
            self.root.setSpacing(10)

        self.setFixedSize(w, h)
        self.card.setProperty("sizeVariant", variant)
        for wgt in [self.card, self]:
            wgt.style().unpolish(wgt)
            wgt.style().polish(wgt)
        self.settings.setValue("size", key)

    def apply_theme(self, key: str):
        self.settings.setValue("theme", key)
        app = QApplication.instance()
        if hasattr(app, "load_styles"):
            app.load_styles(key)
        for w in [self.card, self]:
            w.style().unpolish(w)
            w.style().polish(w)

    def snap_to(self, corner: str):
        screen = QApplication.primaryScreen().availableGeometry()
        m = 12
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
        latlon = CITY_DB.get(country, {}).get(city)
        if not latlon:
            return CITY_DB["Türkiye"]["İstanbul"]
        return latlon

    async def start_weather_loop(self, interval_minutes: int = 5):
        while True:
            try:
                await self.update_weather_once()
            except Exception as e:
                print("[weather loop] error:", e)
            await asyncio.sleep(interval_minutes * 60)

    async def update_weather_once(self):
        lat, lon = getattr(self, "_lat", None), getattr(self, "_lon", None)
        if lat is None or lon is None:
            return
        data = await fetch_current_weather(lat, lon)
        if not data:
            self.temp_value.setText("— °C")
            self.condition_label.setText("Bağlantı yok")
            return
        temp = data.get("temperature")
        code = data.get("weathercode")
        self.temp_value.setText(
            f"{int(round(temp))} °C" if temp is not None else "— °C"
        )
        self.condition_label.setText(describe_weather(code))

    def change_geo_location(self):
        # mevcut değerleri böl
        try:
            current_city, current_country = [
                p.strip() for p in self.location_label.text().split(",", 1)
            ]
        except Exception:
            current_country, current_city = "Türkiye", "İstanbul"

        dlg = LocationDialog(
            self, current_country=current_country, current_city=current_city
        )
        if dlg.exec() == QDialog.Accepted:
            country, city = dlg.selected()
            self.location_label.setText(f"{city}, {country}")
            self.settings.setValue("geo_country", country)
            self.settings.setValue("geo_city", city)
            self._lat, self._lon = self.resolve_coords(country, city)
            asyncio.create_task(self.update_weather_once())
