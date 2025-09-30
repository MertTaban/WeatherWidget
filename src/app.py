# src/app.py
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from qasync import QEventLoop

from frontend.views.main_widget import MainWidget


# -----------------------
# PyInstaller resource helper
# -----------------------
def resource_path(relative: str) -> Path:
    """
    Gömülü (PyInstaller) veya kaynak ağaçtan dosya yolu döndürür.
    Örn: resource_path("assets/styles_dark.qss")
    """
    if hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base = Path(__file__).parent  # src/
    return (base / relative).resolve()


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception as e:
        print(f"[read_text] {p} okunamadı: {e}")
        return ""


def make_style(theme_key: str) -> str:
    # QSS dosyaları exe’ye şu şekilde eklenecek:
    # --add-data "src/frontend/assets/styles_dark.qss;assets"
    # --add-data "src/frontend/assets/styles_light.qss;assets"
    qss_path = (
        resource_path("assets/styles_dark.qss")
        if theme_key == "dark"
        else resource_path("assets/styles_light.qss")
    )
    return read_text(qss_path)


async def main_async(app: QApplication):
    ui = MainWidget()
    ui.show()

    # ilk veri çekimi ve periyodik döngü
    await ui.update_weather_once()
    asyncio.create_task(ui.start_weather_loop(interval_minutes=5))
    return ui


def build_tray(app: QApplication, ui: MainWidget) -> QSystemTrayIcon:
    # Tray ikonu: --icon ile exe ikonunu ayarlayacağız ama tepside kullanmak üzere
    # ayrıca figma/sunny.png dosyasını da gömelim:
    # --add-data "src/frontend/assets/figma;figma"
    icon_path = resource_path("figma/sunny.png")
    tray_icon = QIcon(str(icon_path)) if icon_path.exists() else app.windowIcon()

    tray = QSystemTrayIcon(tray_icon, app)
    menu = QMenu()

    act_show = QAction("Göster", menu)
    act_hide = QAction("Gizle", menu)
    act_quit = QAction("Çıkış", menu)

    act_show.triggered.connect(ui.show)
    act_hide.triggered.connect(ui.hide)
    act_quit.triggered.connect(app.quit)

    # Boyut
    size_menu = menu.addMenu("Boyut")
    for key, text in [("small", "Küçük"), ("medium", "Orta"), ("large", "Büyük")]:
        a = QAction(text, size_menu)
        a.triggered.connect(lambda _, k=key: ui.apply_size(k))
        size_menu.addAction(a)

    # Tema
    theme_menu = menu.addMenu("Tema")
    for key, text in [("dark", "Modern Karanlık"), ("light", "Modern Aydınlık")]:
        a = QAction(text, theme_menu)
        a.triggered.connect(lambda _, k=key: ui.apply_theme(k))
        theme_menu.addAction(a)

    # Konum & Güncelle
    act_geo = QAction("Konumu Değiştir…", menu)
    act_geo.triggered.connect(ui.change_geo_location)
    act_refresh = QAction("Şimdi güncelle", menu)
    act_refresh.triggered.connect(lambda: asyncio.create_task(ui.update_weather_once()))

    menu.addAction(act_show)
    menu.addAction(act_hide)
    menu.addSeparator()
    menu.addMenu(size_menu)
    menu.addMenu(theme_menu)
    menu.addAction(act_geo)
    menu.addAction(act_refresh)
    menu.addSeparator()
    menu.addAction(act_quit)

    tray.setContextMenu(menu)
    tray.setToolTip("WeatherWidget")
    tray.show()
    return tray


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Tema yükleyici referansı (MainWidget içinden çağrılıyor)
    def load_styles(theme_key: str):
        app.setStyle("Fusion")
        app.setStyleSheet(make_style(theme_key))

    app.load_styles = load_styles  # type: ignore[attr-defined]

    # Varsayılan temayı uygula
    s = QSettings("YourOrg", "WeatherWidget")
    app.load_styles(s.value("theme", "dark"))

    # Uygulama ikonu (derleme sırasında ayrıca --icon verilebilir)
    app.setWindowIcon(QIcon(str(resource_path("figma/sunny.png"))))

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    with loop:
        ui = loop.run_until_complete(main_async(app))
        tray = build_tray(app, ui)
        loop.run_forever()
