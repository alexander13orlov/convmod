# tests/test_hex_input.py
# project_root/tests/test_hex_input.py
# Python 3.11+, PyQt6
# HEX-поля: латинские буквы A-F должны приниматься и валидатором,
# и путём ввода через виджет (key events).

import os
import sys
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from validators import Validator
from widgets.byte_field import ByteGroupField


class TestHexInput(unittest.TestCase):
    """HEX-поле принимает латинские A-F и отклоняет кириллицу."""

    qapp: QApplication

    @classmethod
    def setUpClass(cls) -> None:
        cls.qapp = QApplication.instance() or QApplication(sys.argv)

    def test_validator_accepts_latin_hex(self) -> None:
        self.assertTrue(Validator.validate("A1bC", "hex_direct"))
        self.assertTrue(Validator.validate("f", "hex_complement"))
        self.assertTrue(Validator.validate("4D3A", "ieee_hex"))

    def test_validator_rejects_cyrillic(self) -> None:
        # Кириллица внешне похожа на латиницу (А, В, Е, Н, С), но не допустима
        self.assertFalse(Validator.validate("А", "hex_direct"))
        self.assertFalse(Validator.validate("Ф", "hex_direct"))

    def test_hex_field_accepts_latin_letters_via_key_events(self) -> None:
        field = ByteGroupField("HEX прямой код:", "hex_direct", is_long=True)
        field.show()
        field.text_edit.setFocus()
        for key in (Qt.Key.Key_A, Qt.Key.Key_B, Qt.Key.Key_C,
                    Qt.Key.Key_D, Qt.Key.Key_E, Qt.Key.Key_F):
            QTest.keyClick(field.text_edit, key)
        self.assertEqual(field.text_edit.toPlainText(), "abcdef")


if __name__ == "__main__":
    unittest.main()
