from PySide6.QtCore import QObject, Signal


class EventBus(QObject):
    data_updated = Signal(dict)  # UI'ye veri taşımak için
