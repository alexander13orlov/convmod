# widgets/byte_field.py (полностью исправленный)
# Python 3.11+, PyQt6

from typing import Optional
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer
from widgets.base_field import NumberField
from highlighters import ByteHighlighter
from validators import Validator


class ByteGroupField(NumberField):
    """Поле с подсветкой байтов, без пробелов"""
    
    def __init__(self, label: str, format_type: str, is_long: bool = False, parent: Optional[NumberField] = None) -> None:
        super().__init__(label, format_type, is_long, parent)
        self.highlighter: Optional[ByteHighlighter] = None
        
    def set_value_silent(self, text: str) -> None:
        """Установка значения без генерации сигнала changed"""
        self._ignore_signal = True
        self._last_valid_text = text
        self.text_edit.setPlainText(text)
        QTimer.singleShot(1, self._init_highlighter)
        self._ignore_signal = False
    
    def _init_highlighter(self) -> None:
        doc = self.text_edit.document()
        if doc is not None and self.highlighter is None:
            self.highlighter = ByteHighlighter(doc, self.format_type)
    
    def _on_text_changed(self) -> None:
        if self._ignore_signal:
            return
        raw_text: str = self.text_edit.toPlainText()
        if Validator.validate(raw_text, self.format_type):
            self._last_valid_text = raw_text
            self.changed.emit(raw_text, self)
        else:
            self._ignore_signal = True
            self.text_edit.setPlainText(self._last_valid_text)
            self._ignore_signal = False
    
    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_C and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            clipboard = QApplication.clipboard()
            if clipboard is not None:
                clipboard.setText(self.get_raw_value())
            event.accept()
        elif event.key() == Qt.Key.Key_V and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            clipboard = QApplication.clipboard()
            if clipboard is not None:
                text = clipboard.text()
                if text is not None:
                    clean_text: str = text.replace(" ", "")
                    self._ignore_signal = True
                    self.text_edit.setPlainText(clean_text)
                    self._ignore_signal = False
                    if Validator.validate(clean_text, self.format_type):
                        self._last_valid_text = clean_text
                        self.changed.emit(clean_text, self)
                    QTimer.singleShot(1, self._init_highlighter)
            event.accept()
        else:
            self.text_edit.keyPressEvent(event)