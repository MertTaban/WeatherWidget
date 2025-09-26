import asyncio
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop, asyncSlot

from backend.bus import EventBus
from backend.services import ticker
from frontend.views.main_widget import MainWidget


async def main_async(app: QApplication):
    bus = EventBus()
    ui = MainWidget()
    ui.show()

    # sinyaller
    @asyncSlot(dict)
    async def on_manual_refresh(_=None):
        # burada anlık fetch örneği yapılabilir
        pass

    ui.refresh_btn.clicked.connect(lambda: bus.data_updated.emit({"value": "↻"}))

    # background döngü
    async for data in ticker():
        bus.data_updated.emit(data)
        ui.value_label.setText(str(data["value"]))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon())  # istersen ikon ekle
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    with loop:
        loop.run_until_complete(main_async(app))
