from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._drag_pos = QPoint()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)

        self.value_label = QLabel("—")
        self.value_label.setObjectName("valueLabel")

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setObjectName("primaryBtn")

        root.addWidget(self.value_label)
        root.addWidget(self.refresh_btn)

        self.setFixedSize(220, 120)

    # sürükle-bırak (frameless pencere için)
    def mousePressEvent(self, e):
        if e.button() == 1:
            self._drag_pos = (
                e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            e.accept()

    def mouseMoveEvent(self, e):
        if e.buttons() & 1:
            self.move(e.globalPosition().toPoint() - self._drag_pos)
            e.accept()
