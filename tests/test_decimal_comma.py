# tests/test_decimal_comma.py
# project_root/tests/test_decimal_comma.py
# Python 3.11+, PyQt6
# Дробная часть: и точка, и запятая принимаются как разделитель,
# но отображается всегда точка.

import os
import sys
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication

from validators import Validator
from widgets.base_field import NumberField


class TestDecimalCommaSeparator(unittest.TestCase):
    """Запятая принимается как разделитель дробной части, на экране — точка."""

    # Ссылку держим на классе: без неё QApplication соберётся, и виджеты падут
    qapp: QApplication

    @classmethod
    def setUpClass(cls) -> None:
        cls.qapp = QApplication.instance() or QApplication(sys.argv)

    def _cursor_pos(self, field) -> int:
        return field.text_edit.textCursor().position()

    def test_validator_accepts_comma_and_dot(self) -> None:
        self.assertTrue(Validator.validate("3.14", "decimal"))
        self.assertTrue(Validator.validate("3,14", "decimal"))

    def test_comma_displayed_as_dot(self) -> None:
        field = NumberField("Десятичный код:", "decimal")
        field.text_edit.insertPlainText("3,14")
        self.assertEqual(field.text_edit.toPlainText(), "3.14")
        self.assertEqual(self._cursor_pos(field), 4)  # курсор остаётся в конце

    def test_comma_mid_text_cursor_stays(self) -> None:
        field = NumberField("Десятичный код:", "decimal")
        field.text_edit.insertPlainText("3")
        cursor = field.text_edit.textCursor()
        cursor.setPosition(1)
        field.text_edit.setTextCursor(cursor)
        field.text_edit.insertPlainText(",14")
        self.assertEqual(field.text_edit.toPlainText(), "3.14")
        self.assertEqual(self._cursor_pos(field), 4)

    def test_dot_stays_dot(self) -> None:
        field = NumberField("Десятичный код:", "decimal")
        field.text_edit.insertPlainText("3.14")
        self.assertEqual(field.text_edit.toPlainText(), "3.14")
        self.assertEqual(self._cursor_pos(field), 4)


if __name__ == "__main__":
    unittest.main()
