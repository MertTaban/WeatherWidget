from pathlib import Path

from PySide6.QtCore import QEvent, QPoint, QSettings, Qt
from PySide6.QtGui import QAction, QIcon, QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Örnek ülke/şehir verisi (tam: Türkiye 81 il, Kıbrıs 6 şehir)
COUNTRIES = {
    "Türkiye": [
        "Adana",
        "Adıyaman",
        "Afyonkarahisar",
        "Ağrı",
        "Aksaray",
        "Amasya",
        "Ankara",
        "Antalya",
        "Ardahan",
        "Artvin",
        "Aydın",
        "Balıkesir",
        "Bartın",
        "Batman",
        "Bayburt",
        "Bilecik",
        "Bingöl",
        "Bitlis",
        "Bolu",
        "Burdur",
        "Bursa",
        "Çanakkale",
        "Çankırı",
        "Çorum",
        "Denizli",
        "Diyarbakır",
        "Düzce",
        "Edirne",
        "Elazığ",
        "Erzincan",
        "Erzurum",
        "Eskişehir",
        "Gaziantep",
        "Giresun",
        "Gümüşhane",
        "Hakkari",
        "Hatay",
        "Iğdır",
        "Isparta",
        "İstanbul",
        "İzmir",
        "Kahramanmaraş",
        "Karabük",
        "Karaman",
        "Kars",
        "Kastamonu",
        "Kayseri",
        "Kırıkkale",
        "Kırklareli",
        "Kırşehir",
        "Kilis",
        "Kocaeli",
        "Konya",
        "Kütahya",
        "Malatya",
        "Manisa",
        "Mardin",
        "Mersin",
        "Muğla",
        "Muş",
        "Nevşehir",
        "Niğde",
        "Ordu",
        "Osmaniye",
        "Rize",
        "Sakarya",
        "Samsun",
        "Siirt",
        "Sinop",
        "Sivas",
        "Şanlıurfa",
        "Şırnak",
        "Tekirdağ",
        "Tokat",
        "Trabzon",
        "Tunceli",
        "Uşak",
        "Van",
        "Yalova",
        "Yozgat",
        "Zonguldak",
    ],
    "Kıbrıs": ["Lefkoşa", "Limasol", "Larnaka", "Baf", "Mağusa", "Girne"],
    "Almanya": [
        "Berlin",
        "Hamburg",
        "Münih",
        "Köln",
        "Frankfurt",
        "Stuttgart",
        "Düsseldorf",
        "Dortmund",
        "Essen",
        "Leipzig",
        "Bremen",
        "Dresden",
        "Hannover",
        "Nürnberg",
        "Bochum",
        "Duisburg",
        "Wuppertal",
        "Bielefeld",
        "Bonn",
        "Münster",
    ],
    "Fransa": [
        "Paris",
        "Marsilya",
        "Lyon",
        "Toulouse",
        "Nice",
        "Nantes",
        "Strazburg",
        "Montpellier",
        "Bordeaux",
        "Lille",
        "Rennes",
        "Reims",
        "Le Havre",
        "Saint-Étienne",
        "Toulon",
        "Grenoble",
        "Dijon",
        "Angers",
        "Nîmes",
        "Villeurbanne",
    ],
    "İtalya": [
        "Roma",
        "Milano",
        "Napoli",
        "Torino",
        "Palermo",
        "Cenova",
        "Bologna",
        "Floransa",
        "Bari",
        "Catania",
        "Venedik",
        "Verona",
        "Messina",
        "Padova",
        "Trieste",
        "Brescia",
        "Parma",
        "Modena",
        "Reggio Calabria",
        "Perugia",
    ],
    "İspanya": [
        "Madrid",
        "Barselona",
        "Valensiya",
        "Sevilla",
        "Zaragoza",
        "Málaga",
        "Murcia",
        "Palma de Mallorca",
        "Las Palmas",
        "Bilbao",
        "Alicante",
        "Córdoba",
        "Valladolid",
        "Vigo",
        "Gijón",
        "Hospitalet",
        "La Coruña",
        "Granada",
        "Vitoria-Gasteiz",
        "Elche",
    ],
    "Birleşik Krallık": [
        "Londra",
        "Manchester",
        "Birmingham",
        "Liverpool",
        "Leeds",
        "Sheffield",
        "Bristol",
        "Newcastle",
        "Nottingham",
        "Leicester",
        "Edinburgh",
        "Glasgow",
        "Cardiff",
        "Belfast",
        "Coventry",
        "Hull",
        "Stoke-on-Trent",
        "Wolverhampton",
        "Derby",
        "Swansea",
    ],
    "ABD": [
        "New York",
        "Los Angeles",
        "Chicago",
        "Houston",
        "Phoenix",
        "Philadelphia",
        "San Antonio",
        "San Diego",
        "Dallas",
        "San Jose",
        "Austin",
        "Jacksonville",
        "Fort Worth",
        "Columbus",
        "San Francisco",
        "Charlotte",
        "Indianapolis",
        "Seattle",
        "Denver",
        "Washington D.C.",
        "Boston",
        "El Paso",
        "Detroit",
        "Nashville",
        "Portland",
        "Memphis",
        "Oklahoma City",
        "Las Vegas",
        "Louisville",
        "Baltimore",
        "Milwaukee",
        "Albuquerque",
        "Tucson",
        "Fresno",
        "Sacramento",
        "Kansas City",
        "Atlanta",
        "Miami",
        "Omaha",
        "Raleigh",
        "Colorado Springs",
    ],
    "Kanada": [
        "Toronto",
        "Vancouver",
        "Montreal",
        "Ottawa",
        "Calgary",
        "Edmonton",
        "Winnipeg",
        "Quebec City",
        "Hamilton",
        "Kitchener",
        "London",
        "Victoria",
        "Halifax",
        "Oshawa",
        "Windsor",
        "Saskatoon",
        "Regina",
        "St. John's",
        "Sherbrooke",
        "Barrie",
    ],
    "Japonya": [
        "Tokyo",
        "Yokohama",
        "Osaka",
        "Nagoya",
        "Sapporo",
        "Kobe",
        "Kyoto",
        "Fukuoka",
        "Kawasaki",
        "Hiroşima",
        "Sendai",
        "Kitakyushu",
        "Chiba",
        "Sakai",
        "Niigata",
        "Hamamatsu",
        "Shizuoka",
        "Okayama",
        "Kumamoto",
        "Kagoshima",
    ],
    "Çin": [
        "Pekin",
        "Şanghay",
        "Guangzhou",
        "Shenzhen",
        "Chengdu",
        "Chongqing",
        "Tianjin",
        "Wuhan",
        "Xi'an",
        "Hangzhou",
        "Nanjing",
        "Shenyang",
        "Harbin",
        "Suzhou",
        "Qingdao",
        "Dalian",
        "Zhengzhou",
        "Changsha",
        "Kunming",
        "Fuzhou",
    ],
    "Rusya": [
        "Moskova",
        "St. Petersburg",
        "Novosibirsk",
        "Yekaterinburg",
        "Nijniy Novgorod",
        "Kazan",
        "Çelyabinsk",
        "Omsk",
        "Samara",
        "Rostov-na-Donu",
        "Ufa",
        "Krasnoyarsk",
        "Perm",
        "Voronej",
        "Volgograd",
        "Krasnodar",
        "Saratov",
        "Tolyatti",
        "İjevsk",
        "Barnaul",
    ],
}


class LocationDialog(QDialog):
    def __init__(self, parent=None, current_country="Türkiye", current_city="İstanbul"):
        super().__init__(parent)
        self.setWindowTitle("Konum Seç")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        layout = QVBoxLayout(self)
        self.country = QComboBox(self)
        self.city = QComboBox(self)

        self.country.addItems(COUNTRIES.keys())
        if current_country in COUNTRIES:
            self.country.setCurrentText(current_country)

        def load_cities(cn):
            self.city.clear()
            self.city.addItems(COUNTRIES.get(cn, []))
            if current_city in COUNTRIES.get(cn, []):
                self.city.setCurrentText(current_city)

        load_cities(self.country.currentText())
        self.country.currentTextChanged.connect(load_cities)

        layout.addWidget(QLabel("Ülke:"))
        layout.addWidget(self.country)
        layout.addWidget(QLabel("Şehir:"))
        layout.addWidget(self.city)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected(self):
        return self.country.currentText(), self.city.currentText()


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

        # Header (drag area)
        header = QFrame(self.card)
        header.setObjectName("header")
        h = QHBoxLayout(header)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)

        stored_country = self.settings.value("geo_country", "Türkiye")
        stored_city = self.settings.value("geo_city", "Karabük")
        self.location_label = QLabel(f"{stored_city}, {stored_country}", header)
        self.location_label.setObjectName("locationLabel")
        h.addWidget(self.location_label)
        h.addStretch(1)

        self.settings_btn = QPushButton("", header)
        self.settings_btn.setObjectName("settingsBtn")
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.setFixedSize(24, 24)
        gear = Path(__file__).resolve().parent.parent / "assets" / "gear.svg"
        if gear.exists():
            self.settings_btn.setIcon(QIcon(str(gear)))
        else:
            self.settings_btn.setText("⚙")
        self.settings_btn.clicked.connect(self.open_settings_menu)
        h.addWidget(self.settings_btn)
        self.root.addWidget(header)

        # Content
        self.temp_value = QLabel("30 °C", self.card)
        self.temp_value.setObjectName("tempValue")
        self.root.addWidget(self.temp_value)

        self.condition_label = QLabel("Güneşli", self.card)
        self.condition_label.setObjectName("condition")
        self.root.addWidget(self.condition_label)

        self.consistency_row = QFrame(self.card)
        c = QHBoxLayout(self.consistency_row)
        c.setContentsMargins(0, 0, 0, 0)
        c.setSpacing(6)

        ai_png = Path(__file__).resolve().parent.parent / "assets" / "ai.png"

        self.consistency_icon = QLabel(self.consistency_row)
        if ai_png.exists():
            pix = QPixmap(str(ai_png)).scaled(
                14, 14, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.consistency_icon.setPixmap(pix)
        else:
            # fallback (dosya yoksa)
            self.consistency_icon.setText("🤖")

        self.consistency_label = QLabel("%87 Tutarlılık", self.consistency_row)
        self.consistency_label.setObjectName("consistency")

        c.addWidget(self.consistency_icon)
        c.addWidget(self.consistency_label)
        c.addStretch(1)

        self.root.addWidget(self.consistency_row)

        # self.consistency_label = QLabel("🤖 %87 Tutarlılık", self.card)
        # self.consistency_label.setObjectName("consistency")
        # self.root.addWidget(self.consistency_label)

        # Load size/theme
        self.apply_size(self.settings.value("size", "small"))
        self.apply_theme(self.settings.value("theme", "dark"))

        # Restore screen pos (if any)
        if pt := self.settings.value("pos"):
            try:
                x, y = map(int, str(pt).split(","))
                self.move(x, y)
            except Exception:
                pass

        header.installEventFilter(self)

    # Drag only on header
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

    # Settings menu
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

        # Coğrafi konum (ülke/şehir)
        menu.addSeparator()
        geo_act = QAction("Konumu Değiştir (Ülke/Şehir)…", self)
        geo_act.triggered.connect(self.change_geo_location)
        menu.addAction(geo_act)

        menu.exec(self.settings_btn.mapToGlobal(self.settings_btn.rect().bottomRight()))

    # Helpers
    def apply_size(self, key: str):
        # Görsel farklar: pencere boyutu, kart padding/spacing, bazı satırların görünürlüğü
        if key == "small":
            w, h, variant = 240, 160, "small"
            self.root.setContentsMargins(12, 12, 12, 12)
            self.root.setSpacing(6)
            self.condition_label.setVisible(True)
            self.consistency_label.setVisible(True)
        elif key == "medium":
            w, h, variant = 300, 200, "medium"
            self.root.setContentsMargins(14, 14, 14, 14)
            self.root.setSpacing(8)
            self.condition_label.setVisible(True)
            self.consistency_label.setVisible(True)
        else:  # large
            w, h, variant = 360, 240, "large"
            self.root.setContentsMargins(18, 18, 18, 18)
            self.root.setSpacing(10)
            self.condition_label.setVisible(True)
            self.consistency_label.setVisible(True)

        self.setFixedSize(w, h)
        self.card.setProperty("sizeVariant", variant)
        # QSS yeniden uygula
        self.card.style().unpolish(self.card)
        self.card.style().polish(self.card)
        for child in self.findChildren(QWidget):  # altlara da tazele
            child.style().unpolish(child)
            child.style().polish(child)
        self.settings.setValue("size", key)

    def apply_theme(self, key: str):
        self.settings.setValue("theme", key)
        app = QApplication.instance()
        if hasattr(app, "load_styles"):
            app.load_styles(key)
        # polish yenile
        self.card.style().unpolish(self.card)
        self.card.style().polish(self.card)

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

    def change_geo_location(self):
        # Şu anki değerleri parçala
        try:
            current_city, current_country = [
                p.strip() for p in self.location_label.text().split(",", 1)
            ]
        except Exception:
            current_country, current_city = "Türkiye", "İstanbul"
        dialog = LocationDialog(
            self, current_country=current_country, current_city=current_city
        )
        if dialog.exec() == QDialog.Accepted:
            country, city = dialog.selected()
            self.location_label.setText(f"{city}, {country}")
            self.settings.setValue("geo_country", country)
            self.settings.setValue("geo_city", city)
