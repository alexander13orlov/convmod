# widgets/highlighters.py
# Python 3.11+, PyQt6

from typing import List, Optional, Tuple
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtCore import QObject


class ByteHighlighter(QSyntaxHighlighter):
    """Подсветка каждого байта разным цветом фона (с младшего байта).

    Байты группируются по цифрам формата: в выражениях пробелы и
    операторы цифрами не являются и не подсвечиваются."""

    BIN_DIGITS = "01"
    HEX_DIGITS = "0123456789ABCDEFabcdef"

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
    def compute_byte_ranges(text: str, step: int, color_count: int,
                            digits: Optional[str] = None) -> List[Tuple[int, int, int]]:
        """Вычисляет диапазоны (начало, длина, индекс_цвета) подсветки для каждого байта.

        text — строка (число со знаком или выражение),
        step — цифр на байт (8 для двоичных, 2 для HEX),
        color_count — количество доступных цветов,
        digits — цифры формата; None — любые символы, кроме минуса
        (минус — знак числа или оператор, цифрой не является).
        Байты группируются по цифрам справа налево (с младшего),
        старший байт может быть неполным — подсвечивается имеющаяся часть.
        """
        if not text:
            return []
        if digits is None:
            positions: List[int] = [i for i, ch in enumerate(text) if ch != '-']
        else:
            positions = [i for i, ch in enumerate(text) if ch in digits]
        n: int = len(positions)
        if n == 0:
            return []
        num_bytes: int = (n + step - 1) // step
        ranges: List[Tuple[int, int, int]] = []
        for k in range(num_bytes - 1, -1, -1):
            # байт k: 0 — младший (правые step цифр)
            first: int = max(n - (k + 1) * step, 0)
            last: int = n - k * step - 1
            i: int = first
            while i <= last:
                # подряд идущие позиции цифр байта — один диапазон
                j: int = i
                while j + 1 <= last and positions[j + 1] == positions[j] + 1:
                    j += 1
                ranges.append((positions[i], positions[j] - positions[i] + 1,
                               k % color_count))
                i = j + 1
        return ranges

    def highlightBlock(self, text: str) -> None:
        if not text or text.strip() == "":
            return

        if self.format_type in ["bin_direct", "bin_complement", "ieee_bin"]:
            step: int = 8
            digits: str = ByteHighlighter.BIN_DIGITS
        elif self.format_type in ["hex_direct", "hex_complement", "ieee_hex"]:
            step: int = 2
            digits: str = ByteHighlighter.HEX_DIGITS
        else:
            return

        for start_pos, length, fmt_index in self.compute_byte_ranges(
                text, step, len(self.formats), digits):
            self.setFormat(start_pos, length, self.formats[fmt_index])
