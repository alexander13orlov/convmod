# tests/test_field_cursor.py
# project_root/tests/test_field_cursor.py
# Python 3.11+, PyQt6
# Регрессия: ввод недопустимого символа должен откатывать текст,
# но НЕ должен прыгать курсором в начало поля.

import os
import sys
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication

from widgets.base_field import NumberField
from widgets.byte_field import ByteGroupField


class TestFieldCursorOnInvalidInput(unittest.TestCase):
    """Недопустимый символ: текст откатывается, курсор остаётся на месте ввода."""

    # Ссылку держим на классе: без неё QApplication соберётся, и виджеты падут
    qapp: QApplication

    @classmethod
    def setUpClass(cls) -> None:
        cls.qapp = QApplication.instance() or QApplication(sys.argv)

    def _move_cursor_to_end(self, field) -> None:
        cursor = field.text_edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        field.text_edit.setTextCursor(cursor)

    def _cursor_pos(self, field) -> int:
        return field.text_edit.textCursor().position()

    def test_bin_direct_invalid_char_keeps_cursor_at_end(self) -> None:
        field = ByteGroupField("Двоичный прямой код:", "bin_direct", is_long=True)
        field.set_value_silent("101")
        self._move_cursor_to_end(field)
        field.text_edit.insertPlainText("2")  # '2' недопустим в двоичном
        self.assertEqual(field.text_edit.toPlainText(), "101")
        self.assertEqual(self._cursor_pos(field), 3)  # в конце, а не 0

    def test_bin_complement_invalid_char_keeps_cursor_at_end(self) -> None:
        field = ByteGroupField("Двоичный доп. код:", "bin_complement", is_long=True)
        field.set_value_silent("110")
        self._move_cursor_to_end(field)
        field.text_edit.insertPlainText("9")  # '9' недопустим в двоичном
        self.assertEqual(field.text_edit.toPlainText(), "110")
        self.assertEqual(self._cursor_pos(field), 3)

    def test_hex_direct_invalid_char_keeps_cursor_at_end(self) -> None:
        field = ByteGroupField("HEX прямой код:", "hex_direct", is_long=True)
        field.set_value_silent("1F")
        self._move_cursor_to_end(field)
        field.text_edit.insertPlainText("G")  # 'G' недопустим в HEX
        self.assertEqual(field.text_edit.toPlainText(), "1F")
        self.assertEqual(self._cursor_pos(field), 2)

    def test_decimal_invalid_char_keeps_cursor_at_end(self) -> None:
        field = NumberField("Десятичный код:", "decimal")
        field.set_value_silent("123")
        self._move_cursor_to_end(field)
        field.text_edit.insertPlainText("a")  # 'a' недопустим в десятичном
        self.assertEqual(field.text_edit.toPlainText(), "123")
        self.assertEqual(self._cursor_pos(field), 3)

    def test_valid_input_advances_cursor(self) -> None:
        field = ByteGroupField("Двоичный прямой код:", "bin_direct", is_long=True)
        field.text_edit.insertPlainText("1")
        self.assertEqual(field.text_edit.toPlainText(), "1")
        self.assertEqual(self._cursor_pos(field), 1)
        field.text_edit.insertPlainText("0")
        self.assertEqual(field.text_edit.toPlainText(), "10")
        self.assertEqual(self._cursor_pos(field), 2)


if __name__ == "__main__":
    unittest.main()
