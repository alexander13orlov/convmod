# widgets/base_field.py (исправлен)
# Python 3.11+, PyQt6

import logging
import re
from typing import Optional
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPlainTextEdit
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QPalette
from validators import Validator
from utils.font.font_loader import get_mono_font

logger = logging.getLogger(__name__)


class NumberField(QFrame):
    changed = pyqtSignal(str, object)
    layout_hint = pyqtSignal(str)

    # Подсказка при отклонении кириллицы (русская раскладка клавиатуры)
    LAYOUT_HINT = "Введена кириллица — переключите раскладку на английскую"
    _CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")

    def __init__(self, label: str, format_type: str, is_long: bool = False, parent: Optional[QFrame] = None) -> None:
        super().__init__(parent)
        self.format_type: str = format_type
        self.is_long: bool = is_long
        self._ignore_signal: bool = False
        self._last_valid_text: str = ""
        
        layout: QHBoxLayout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label: QLabel = QLabel(label)
        self.label.setFixedWidth(146)
        self.label.setIndent(4)
        layout.addWidget(self.label)
        
        self.text_edit: QPlainTextEdit = QPlainTextEdit()
        self.text_edit.setMaximumHeight(60 if is_long else 40)
        self.text_edit.setFont(get_mono_font(10))
        self.text_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.text_edit, stretch=1)
        
    @staticmethod
    def _common_prefix_len(a: str, b: str) -> int:
        """Длина общего префикса: позиция, где новый текст расходится с валидным."""
        n: int = min(len(a), len(b))
        i: int = 0
        while i < n and a[i] == b[i]:
            i += 1
        return i

    def _on_text_changed(self) -> None:
        if self._ignore_signal:
            return
        raw_text: str = self.text_edit.toPlainText()
        
        if Validator.validate(raw_text, self.format_type):
            # Для decimal запятая принимается как разделитель, но на экране — точка
            if self.format_type == "decimal" and "," in raw_text:
                normalized: str = raw_text.replace(",", ".")
                cursor_pos = self.text_edit.textCursor().position()
                self._ignore_signal = True
                self.text_edit.setPlainText(normalized)
                cursor = self.text_edit.textCursor()
                cursor.setPosition(min(cursor_pos, len(normalized)))
                self.text_edit.setTextCursor(cursor)
                self._ignore_signal = False
                raw_text = normalized
            self._last_valid_text = raw_text
            self.changed.emit(raw_text, self)
        else:
            # Откат: курсор возвращается в точку, где вводилось недопустимое
            pos = self._common_prefix_len(self._last_valid_text, raw_text)
            self._ignore_signal = True
            self.text_edit.setPlainText(self._last_valid_text)
            cursor = self.text_edit.textCursor()
            cursor.setPosition(min(pos, len(self._last_valid_text)))
            self.text_edit.setTextCursor(cursor)
            self._ignore_signal = False
            # Новая часть (от первого расхождения до конца): если там кириллица — подсказка
            if self._CYRILLIC_RE.search(raw_text[pos:]):
                self.layout_hint.emit(self.LAYOUT_HINT)

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

