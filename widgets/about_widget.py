# widgets/about_widget.py
# Python 3.11+, PyQt6

from typing import Optional
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from version import APP_NAME, APP_VERSION, APP_BUILD


class AboutWidget(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        self.title_label: QLabel = QLabel(APP_NAME)
        self.version_label: QLabel = QLabel(f"Версия: {APP_VERSION}")
        self.build_label: QLabel = QLabel(f"Номер билда: {APP_BUILD}")

        layout.addWidget(self.title_label)
        layout.addWidget(self.version_label)
        layout.addWidget(self.build_label)
        layout.addStretch()
