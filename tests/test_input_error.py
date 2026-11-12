# tests/test_input_error.py
# project_root/tests/test_input_error.py
# Python 3.11+, PyQt6
# Ошибка ввода: поле не блокирует ввод — запрещённые символы и
# последовательности остаются в тексте, остальные поля обнуляются,
# статус-бар показывает яркий значок ошибки с подсказкой.

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from validators import Validator


class TestInputErrorMessages(unittest.TestCase):
    """Validator.input_error: конкретные ошибки по символам и последовательностям."""

    def test_forbidden_char(self) -> None:
        self.assertIn("Запрещённый символ: «G»", Validator.input_error("G+1", "hex_direct"))
        self.assertIn("Запрещённый символ: «a»", Validator.input_error("12a4", "decimal"))
        self.assertIn("Запрещённый символ: «2»", Validator.input_error("1012", "bin_direct"))
        self.assertIn("Запрещённый символ: «Ф»", Validator.input_error("1Ф", "hex_direct"))

    def test_three_signs_in_row(self) -> None:
        self.assertIn("«---»", Validator.input_error("10---1", "decimal"))
        self.assertIn("«---»", Validator.input_error("10 - - - 1", "decimal"))
        self.assertIn("«---»", Validator.input_error("FF---1", "hex_direct"))

    def test_operator_in_row(self) -> None:
        self.assertIn("«-*»", Validator.input_error("BD -54+890-*64", "hex_direct"))
        self.assertIn("«**»", Validator.input_error("5**3", "decimal"))
        self.assertIn("«+*»", Validator.input_error("5+*3", "decimal"))
        self.assertIn("оператор без числа", Validator.input_error("*5", "decimal"))

    def test_numbers_in_row(self) -> None:
        self.assertIn("числа подряд", Validator.input_error("325 234523 4563 ", "decimal"))
        self.assertIn("числа подряд", Validator.input_error("1 000", "decimal"))
        self.assertIn("числа подряд", Validator.input_error("1010 1010", "bin_direct"))

    def test_paren_errors(self) -> None:
        self.assertIsNotNone(Validator.input_error("5(3)", "decimal"))
        self.assertIsNotNone(Validator.input_error("5)", "decimal"))
        self.assertIsNotNone(Validator.input_error("()", "decimal"))

    def test_bad_separator(self) -> None:
        self.assertIsNotNone(Validator.input_error("3.5.2", "decimal"))
        self.assertIsNotNone(Validator.input_error("5..2", "decimal"))

    def test_char_field(self) -> None:
        self.assertIsNone(Validator.input_error("А", "unicode_char"))
        self.assertIn("один символ", Validator.input_error("АБ", "unicode_char"))

    def test_in_progress_is_not_error(self) -> None:
        # Неоконченное выражение — не ошибка ввода: его ещё можно дополнить
        self.assertIsNone(Validator.input_error("5+", "decimal"))
        self.assertIsNone(Validator.input_error("10--", "decimal"))
        self.assertIsNone(Validator.input_error("3.", "decimal"))
        self.assertIsNone(Validator.input_error("(5", "decimal"))
        self.assertIsNone(Validator.input_error("-", "decimal"))

    def test_valid_values(self) -> None:
        self.assertIsNone(Validator.input_error("10--1", "decimal"))
        self.assertIsNone(Validator.input_error("10-+1", "decimal"))
        self.assertIsNone(Validator.input_error("2^10", "decimal"))
        self.assertIsNone(Validator.input_error("FF+01", "hex_direct"))
        self.assertIsNone(Validator.input_error("1010+1010", "bin_direct"))
        self.assertIsNone(Validator.input_error(".5", "decimal"))

    def test_validate_consistent(self) -> None:
        self.assertFalse(Validator.validate("10---1", "decimal"))
        self.assertTrue(Validator.validate("10--1", "decimal"))
        self.assertTrue(Validator.validate("42", "decimal"))


class TestInputErrorGui(unittest.TestCase):
    """ConverterWidget: ошибка ввода — текст остаётся в поле, остальные
    поля обнуляются, ошибка запоминается."""

    qapp: "QApplication"

    @classmethod
    def setUpClass(cls) -> None:
        cls.qapp = QApplication.instance() or QApplication(sys.argv)

    def _widget(self):
        from PyQt6.QtTest import QTest
        from widgets.converter_widget import ConverterWidget
        w = ConverterWidget()
        w.show()
        QTest.qWait(50)  # дождаться отложенной сборки полей
        return w

    def _set(self, w, ftype: str, text: str) -> None:
        field = w.fields[ftype]
        field.set_value_silent(text)
        w._convert_from_source(text, field)

    def test_three_signs_zeroes_others(self) -> None:
        w = self._widget()
        try:
            self._set(w, "decimal", "10--")  # неоконченное: ошибки нет
            self.assertIsNone(w.get_input_error())
            self._set(w, "decimal", "10---")  # третий знак — ошибка
            error = w.get_input_error()
            self.assertIsNotNone(error)
            self.assertIn("«---»", error)
            self.assertEqual(w.fields["decimal"].text_edit.toPlainText(), "10---")
            self.assertEqual(w.fields["hex_direct"].text_edit.toPlainText(), "00")
            self.assertEqual(w.fields["bin_direct"].text_edit.toPlainText(), "00000000")
        finally:
            w.deleteLater()

    def test_user_example_and_fix(self) -> None:
        w = self._widget()
        try:
            self._set(w, "decimal", "10---+-++-+--1")
            self.assertIsNotNone(w.get_input_error())
            self._set(w, "decimal", "10--1")  # поле исправлено — ошибка уходит
            self.assertIsNone(w.get_input_error())
            self.assertEqual(w.fields["hex_direct"].text_edit.toPlainText(), "0B")
        finally:
            w.deleteLater()

    def test_numbers_in_row(self) -> None:
        w = self._widget()
        try:
            self._set(w, "decimal", "325 234523 4563 ")
            self.assertIn("числа подряд", w.get_input_error())
            self.assertEqual(w.fields["hex_direct"].text_edit.toPlainText(), "00")
        finally:
            w.deleteLater()

    def test_operator_row_from_hex_source(self) -> None:
        w = self._widget()
        try:
            self._set(w, "hex_direct", "BD -54+890-*64")
            self.assertIn("«-*»", w.get_input_error())
            self.assertEqual(w.fields["decimal"].text_edit.toPlainText(), "0")
        finally:
            w.deleteLater()

    def test_incomplete_expression_no_error(self) -> None:
        w = self._widget()
        try:
            self._set(w, "decimal", "5+")
            self.assertIsNone(w.get_input_error())
            # Неоконченное: поля очищаются, а не обнуляются
            self.assertEqual(w.fields["hex_direct"].text_edit.toPlainText(), "")
        finally:
            w.deleteLater()


class TestInputErrorStatusBar(unittest.TestCase):
    """Статус-бар: при ошибке ввода — яркий значок и красная подсказка."""

    qapp: "QApplication"

    @classmethod
    def setUpClass(cls) -> None:
        cls.qapp = QApplication.instance() or QApplication(sys.argv)

    def _main(self):
        from PyQt6.QtTest import QTest
        from widgets.main_window import MainWindow
        w = MainWindow()
        w.show()
        QTest.qWait(100)  # отложенная сборка полей конвертера
        return w

    def test_error_shows_icon_and_message(self) -> None:
        w = self._main()
        try:
            dec = w.converter_widget.fields["decimal"]
            dec.set_value_silent("325 234523")
            w.converter_widget._convert_from_source("325 234523", dec)
            self.assertTrue(w.status_icon.isVisible())
            self.assertIn("Запрещённая последовательность", w.status_info.text())
        finally:
            w.close()

    def test_forbidden_char_message_and_zeroing(self) -> None:
        w = self._main()
        try:
            dec = w.converter_widget.fields["decimal"]
            dec.set_value_silent("12a4")
            w.converter_widget._convert_from_source("12a4", dec)
            self.assertTrue(w.status_icon.isVisible())
            self.assertIn("Запрещённый символ: «a»", w.status_info.text())
            self.assertEqual(
                w.converter_widget.fields["hex_direct"].text_edit.toPlainText(), "00")
        finally:
            w.close()

    def test_valid_input_clears_error(self) -> None:
        w = self._main()
        try:
            dec = w.converter_widget.fields["decimal"]
            dec.set_value_silent("325 234523")
            w.converter_widget._convert_from_source("325 234523", dec)
            self.assertTrue(w.status_icon.isVisible())
            dec.set_value_silent("42")
            w.converter_widget._convert_from_source("42", dec)
            self.assertFalse(w.status_icon.isVisible())
            self.assertIn("Байт:", w.status_info.text())
        finally:
            w.close()


if __name__ == "__main__":
    unittest.main()