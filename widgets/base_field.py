# widgets/base_field.py (исправлен)
# Python 3.11+, PyQt6

import logging
from typing import Optional
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPlainTextEdit
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QPalette
from validators import Validator
from utils.font.font_loader import get_mono_font

logger = logging.getLogger(__name__)


class NumberField(QFrame):
    changed = pyqtSignal(str, object)

    def __init__(self, label: str, format_type: str, is_long: bool = False, parent: Optional[QFrame] = None) -> None:
        super().__init__(parent)
        self.format_type: str = format_type
        self.is_long: bool = is_long
        self._ignore_signal: bool = False
        self._last_valid_text: str = ""
        
        layout: QHBoxLayout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label: QLabel = QLabel(label)
        self.label.setFixedWidth(172)
        self.label.setIndent(4)
        layout.addWidget(self.label)
        
        self.text_edit: QPlainTextEdit = QPlainTextEdit()
        self.text_edit.setMaximumHeight(60 if is_long else 40)
        self.text_edit.setFont(get_mono_font(10))
        self.text_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.text_edit, stretch=1)
        
    def _on_text_changed(self) -> None:
        if self._ignore_signal:
            return
        raw_text: str = self.text_edit.toPlainText()
        
        if Validator.validate(raw_text, self.format_type):
            self._last_valid_text = raw_text
            self.changed.emit(raw_text, self)
        else:
            self._ignore_signal = True
            cursor = self.text_edit.textCursor()
            cursor_pos = cursor.position()
            self.text_edit.setPlainText(self._last_valid_text)
            cursor = self.text_edit.textCursor()
            new_pos = min(cursor_pos, len(self._last_valid_text))
            cursor.setPosition(new_pos)
            self.text_edit.setTextCursor(cursor)
            self._ignore_signal = False

    def set_value_silent(self, text: str) -> None:
        """Установка значения без генерации сигнала changed"""
        # Отключаем обработчик
        self._ignore_signal = True
        self._last_valid_text = text
        self.text_edit.setPlainText(text)
        self._ignore_signal = False

    def get_raw_value(self) -> str:
        return self.text_edit.toPlainText()
    
    def setPalette(self, palette: QPalette) -> None:
        self.text_edit.setPalette(palette)

