# frontend/views/main_widget.py (değiştir)
from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QWidget


class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._drag_pos = QPoint()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(220, 120)

        # Dış root: şeffaf
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # İç "kart" kap: asıl stil burada
        self.card = QFrame(self)
        self.card.setObjectName("card")
        inner = QVBoxLayout(self.card)
        inner.setContentsMargins(12, 12, 12, 12)

        self.value_label = QLabel("—", self.card)
        self.value_label.setObjectName("valueLabel")

        self.refresh_btn = QPushButton("Refresh", self.card)
        self.refresh_btn.setObjectName("primaryBtn")

        inner.addWidget(self.value_label)
        inner.addWidget(self.refresh_btn)
        outer.addWidget(self.card)

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
