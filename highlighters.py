# highlighters.py
# project_root/highlighters.py
# Python 3.11+, PyQt6

from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtCore import QObject


class ByteHighlighter(QSyntaxHighlighter):
    """Подсветка каждого байта разным цветом фона (с младшего байта)"""
    
    def __init__(self, document: QObject, format_type: str) -> None:
        super().__init__(document)
        self.format_type: str = format_type
        self._setup_formats()
        
    def _setup_formats(self) -> None:
        self.bg_colors: list = [
            # QColor(200, 220, 255),   # 0 - голубой
            QColor(250, 175, 175),   # 0 - красный
            QColor(220, 220, 220),   # 1 - серый
            QColor(255, 220, 200),   # 2 - оранжевый
            QColor(200, 255, 200),   # 3 - салатовый
            QColor(255, 200, 255),   # 4 - розовый
            QColor(200, 255, 255),   # 5 - бирюзовый
            QColor(255, 255, 200),   # 6 - желтый
            QColor(200, 200, 255),   # 7 - фиолетовый
        ]
        
        self.formats: list = []
        for i in range(16):
            fmt: QTextCharFormat = QTextCharFormat()
            fmt.setBackground(self.bg_colors[i % len(self.bg_colors)])
            self.formats.append(fmt)
    
    def highlightBlock(self, text: str) -> None:
        if not text or text.strip() == "":
            return
        
        # Удаляем знак минуса для подсветки байтов
        sign_offset: int = 0
        if text.startswith('-'):
            sign_offset = 1
            text_without_sign: str = text[1:]
        else:
            text_without_sign = text
        
        if self.format_type in ["bin_direct", "bin_complement", "ieee_bin"]:
            step: int = 8
        elif self.format_type in ["hex_direct", "hex_complement", "ieee_hex"]:
            step: int = 2
        else:
            return
        
        # Добавляем виртуальные нули для корректной подсветки с младшего байта
        padded_text: str = text_without_sign
        if len(padded_text) % step != 0:
            padded_text = '0' * (step - len(padded_text) % step) + padded_text
        
        num_bytes: int = len(padded_text) // step
        for i in range(num_bytes):
            byte_index_from_right: int = num_bytes - 1 - i
            # Вычисляем позицию в исходном тексте (без виртуальных нулей)
            if i * step < len(padded_text) - (step - len(text_without_sign) % step if len(text_without_sign) % step != 0 else 0):
                start_pos: int = sign_offset + i * step - (step - len(text_without_sign) % step if len(text_without_sign) % step != 0 and i * step >= (step - len(text_without_sign) % step) else 0)
                if start_pos >= sign_offset and start_pos + step <= len(text):
                    fmt_index: int = byte_index_from_right % len(self.formats)
                    self.setFormat(start_pos, step, self.formats[fmt_index])