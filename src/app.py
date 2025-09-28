import asyncio
import sys
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

from frontend.views.main_widget import MainWidget


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""


def make_style(theme_key: str) -> str:
    base = Path(__file__).resolve().parent / "frontend" / "assets"
    fname = "styles_dark.qss" if theme_key == "dark" else "styles_light.qss"
    qss_path = base / fname
    qss = read_text(qss_path)
    if not qss.strip():
        qss = "#card { background-color: #222; color: white; border-radius: 16px; }"
    return qss


def load_styles(app: QApplication, theme_key: str):
    app.setStyle("Fusion")
    app.setStyleSheet(make_style(theme_key))


async def main_async(app: QApplication):
    ui = MainWidget()
    ui.show()

    # 🔑 açılışta ve her 5 dakikada bir güncelle
    asyncio.create_task(ui.start_weather_loop(interval_minutes=5))
    asyncio.create_task(ui.update_weather_once())

    done = asyncio.get_event_loop().create_future()
    app.aboutToQuit.connect(lambda: done.set_result(True))
    await done


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon())

    s = QSettings("YourOrg", "WeatherWidget")
    app.load_styles = lambda theme_key: load_styles(app, theme_key)  # type: ignore
    app.load_styles(s.value("theme", "dark"))

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    with loop:
        loop.run_until_complete(main_async(app))
