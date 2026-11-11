# widgets/highlighters.py
# Python 3.11+, PyQt6

from typing import List, Tuple
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

    @staticmethod
    def compute_byte_ranges(text: str, step: int, color_count: int) -> List[Tuple[int, int, int]]:
        """Вычисляет диапазоны (начало, длина, индекс_цвета) подсветки для каждого байта.

        text — строка (может начинаться с минуса),
        step — символов на байт (8 для двоичных, 2 для HEX),
        color_count — количество доступных цветов.
        Старший байт может быть неполным — подсвечивается имеющаяся часть.
        """
        if not text:
            return []
        sign_offset: int = 1 if text.startswith('-') else 0
        body: str = text[sign_offset:]
        pad: int = (step - len(body) % step) % step
        num_bytes: int = (len(body) + pad) // step
        ranges: List[Tuple[int, int, int]] = []
        for i in range(num_bytes):
            start: int = sign_offset + i * step - pad
            end: int = start + step
            if start < sign_offset:
                start = sign_offset
            if end > len(text):
                end = len(text)
            if end > start:
                color_index: int = (num_bytes - 1 - i) % color_count
                ranges.append((start, end - start, color_index))
        return ranges

    def highlightBlock(self, text: str) -> None:
        if not text or text.strip() == "":
            return

        if self.format_type in ["bin_direct", "bin_complement", "ieee_bin"]:
            step: int = 8
        elif self.format_type in ["hex_direct", "hex_complement", "ieee_hex"]:
            step: int = 2
        else:
            return

        for start_pos, length, fmt_index in self.compute_byte_ranges(text, step, len(self.formats)):
            self.setFormat(start_pos, length, self.formats[fmt_index])
