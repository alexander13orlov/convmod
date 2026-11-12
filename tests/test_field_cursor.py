# tests/test_field_cursor.py
# project_root/tests/test_field_cursor.py
# Python 3.11+, PyQt6
# Регрессия: поле принимает любой ввод без отката; курсор
# сдвигается по вставке и не прыгает в начало поля.

import os
import sys
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication

from widgets.base_field import NumberField
from widgets.byte_field import ByteGroupField


class TestFieldAcceptsAnyInput(unittest.TestCase):
    """Любой символ остаётся в поле; курсор не прыгает."""

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

    def test_bin_direct_invalid_char_stays(self) -> None:
        field = ByteGroupField("Двоичный прямой код:", "bin_direct", is_long=True)
        field.set_value_silent("101")
        self._move_cursor_to_end(field)
        field.text_edit.insertPlainText("2")  # '2' не двоичная цифра
        self.assertEqual(field.text_edit.toPlainText(), "1012")
        self.assertEqual(self._cursor_pos(field), 4)  # в конце, а не 0

    def test_bin_complement_invalid_char_stays(self) -> None:
        field = ByteGroupField("Двоичный доп. код:", "bin_complement", is_long=True)
        field.set_value_silent("110")
        self._move_cursor_to_end(field)
        field.text_edit.insertPlainText("9")  # '9' не двоичная цифра
        self.assertEqual(field.text_edit.toPlainText(), "1109")
        self.assertEqual(self._cursor_pos(field), 4)

    def test_hex_direct_invalid_char_stays(self) -> None:
        field = ByteGroupField("HEX прямой код:", "hex_direct", is_long=True)
        field.set_value_silent("1F")
        self._move_cursor_to_end(field)
        field.text_edit.insertPlainText("G")  # 'G' не HEX-цифра
        self.assertEqual(field.text_edit.toPlainText(), "1FG")
        self.assertEqual(self._cursor_pos(field), 3)

    def test_bin_direct_invalid_char_mid_text_cursor_advances(self) -> None:
        # Курсор в СЕРЕДИНЕ текста: вставка сдвигает его вправо на один
        field = ByteGroupField("Двоичный прямой код:", "bin_direct", is_long=True)
        field.set_value_silent("101")
        cursor = field.text_edit.textCursor()
        cursor.setPosition(1)  # между "1" и "0"
        field.text_edit.setTextCursor(cursor)
        field.text_edit.insertPlainText("2")  # '2' не двоичная цифра
        self.assertEqual(field.text_edit.toPlainText(), "1201")
        self.assertEqual(self._cursor_pos(field), 2)  # после вставки, а не 1

    def test_hex_direct_invalid_char_mid_text_cursor_advances(self) -> None:
        field = ByteGroupField("HEX прямой код:", "hex_direct", is_long=True)
        field.set_value_silent("1F2")
        cursor = field.text_edit.textCursor()
        cursor.setPosition(1)
        field.text_edit.setTextCursor(cursor)
        field.text_edit.insertPlainText("G")
        self.assertEqual(field.text_edit.toPlainText(), "1GF2")
        self.assertEqual(self._cursor_pos(field), 2)

    def test_decimal_invalid_char_stays(self) -> None:
        field = NumberField("Десятичный код:", "decimal")
        field.set_value_silent("123")
        self._move_cursor_to_end(field)
        field.text_edit.insertPlainText("a")  # 'a' недопустим в десятичном
        self.assertEqual(field.text_edit.toPlainText(), "123a")
        self.assertEqual(self._cursor_pos(field), 4)

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
