# widgets/byte_field.py (полностью исправленный)
# Python 3.11+, PyQt6

from typing import Optional
from PyQt6.QtCore import QTimer
from widgets.base_field import NumberField
from widgets.highlighters import ByteHighlighter


class ByteGroupField(NumberField):
    """Поле с подсветкой байтов, без пробелов"""
    
    def __init__(self, label: str, format_type: str, is_long: bool = False, parent: Optional[NumberField] = None) -> None:
        super().__init__(label, format_type, is_long, parent)
        self.highlighter: Optional[ByteHighlighter] = None
        
    def set_value_silent(self, text: str) -> None:
        """Установка значения без генерации сигнала changed"""
        self._ignore_signal = True
        self.text_edit.setPlainText(text)
        QTimer.singleShot(1, self._init_highlighter)
        self._ignore_signal = False
    
    def _init_highlighter(self) -> None:
        doc = self.text_edit.document()
        if doc is not None and self.highlighter is None:
            self.highlighter = ByteHighlighter(doc, self.format_type)

    
