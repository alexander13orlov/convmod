# tests/test_highlighter.py
# project_root/tests/test_highlighter.py
# Python 3.11+, PyQt6

import unittest

from widgets.highlighters import ByteHighlighter


class TestByteHighlighterRanges(unittest.TestCase):
    """Тесты compute_byte_ranges — диапазоны подсветки байтов."""

    def test_full_byte(self) -> None:
        self.assertEqual(
            ByteHighlighter.compute_byte_ranges("11001100", 8, 8),
            [(0, 8, 0)]
        )

    def test_less_than_byte(self) -> None:
        self.assertEqual(
            ByteHighlighter.compute_byte_ranges("1100", 8, 8),
            [(0, 4, 0)]
        )

    def test_two_bytes_with_padding(self) -> None:
        # 10 бит: старший байт неполный (2 бита), младший полный (8 бит)
        self.assertEqual(
            ByteHighlighter.compute_byte_ranges("1100110011", 8, 8),
            [(0, 2, 1), (2, 8, 0)]
        )

    def test_sign_does_not_shift_bytes(self) -> None:
        self.assertEqual(
            ByteHighlighter.compute_byte_ranges("-1100", 8, 8),
            [(1, 4, 0)]
        )

    def test_hex_two_bytes(self) -> None:
        self.assertEqual(
            ByteHighlighter.compute_byte_ranges("FF00", 2, 8),
            [(0, 2, 1), (2, 2, 0)]
        )

    def test_hex_single_byte(self) -> None:
        self.assertEqual(
            ByteHighlighter.compute_byte_ranges("F0", 2, 8),
            [(0, 2, 0)]
        )


if __name__ == "__main__":
    unittest.main()
