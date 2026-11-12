# tests/test_math_eval.py
# project_root/tests/test_math_eval.py
# Калькулятор в полях конвертера: арифметические выражения
# (+, -, *, /, ^, скобки) в числовых форматах.

import os
import sys
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication

import math_eval
from converters import Converter


class TestMathEvalCore(unittest.TestCase):
    """Вычисление выражений: приоритеты, ассоциативность, системы счисления."""

    def test_simple_add(self) -> None:
        self.assertEqual(math_eval.evaluate("2+3", "decimal"), 5)

    def test_precedence(self) -> None:
        self.assertEqual(math_eval.evaluate("2+3*4", "decimal"), 14)
        self.assertEqual(math_eval.evaluate("(2+3)*4", "decimal"), 20)

    def test_left_associativity(self) -> None:
        self.assertEqual(math_eval.evaluate("10-2-3", "decimal"), 5)
        self.assertEqual(math_eval.evaluate("100/10/2", "decimal"), 5.0)

    def test_power(self) -> None:
        self.assertEqual(math_eval.evaluate("2^10", "decimal"), 1024)
        # Правая ассоциативность: 2^(10^2) = 2^100
        self.assertEqual(math_eval.evaluate("2^10^2", "decimal"), 2 ** 100)
        self.assertEqual(math_eval.evaluate("(-2)^2", "decimal"), 4)
        self.assertEqual(math_eval.evaluate("2^-1", "decimal"), 0.5)
        self.assertEqual(math_eval.evaluate("9^0.5", "decimal"), 3.0)

    def test_division_gives_float(self) -> None:
        self.assertEqual(math_eval.evaluate("7/2", "decimal"), 3.5)
        self.assertEqual(math_eval.evaluate("4/2", "decimal"), 2.0)

    def test_division_by_zero(self) -> None:
        self.assertIsNone(math_eval.evaluate("1/0", "decimal"))
        self.assertIsNone(math_eval.evaluate("5/(3-3)", "decimal"))

    def test_decimal_comma_and_point(self) -> None:
        self.assertEqual(math_eval.evaluate("5,5+4,5", "decimal"), 10)
        self.assertEqual(math_eval.evaluate("2.5*2", "decimal"), 5.0)
        self.assertEqual(math_eval.evaluate("-1,5*2", "decimal"), -3.0)

    def test_hex(self) -> None:
        self.assertEqual(math_eval.evaluate("FF+01", "hex_direct"), 256)
        self.assertEqual(math_eval.evaluate("FF*2", "hex_complement"), 510)
        self.assertEqual(math_eval.evaluate("F-A", "hex_direct"), 5)

    def test_bin(self) -> None:
        self.assertEqual(math_eval.evaluate("101+11", "bin_direct"), 8)
        self.assertEqual(math_eval.evaluate("1111*10", "bin_complement"), 30)
        self.assertEqual(math_eval.evaluate("10^100", "bin_direct"), 16)

    def test_spaces(self) -> None:
        self.assertEqual(math_eval.evaluate("5 + 3", "decimal"), 8)
        self.assertEqual(math_eval.evaluate(" FF + 01 ", "hex_direct"), 256)

    def test_unary(self) -> None:
        self.assertEqual(math_eval.evaluate("--5", "decimal"), 5)
        self.assertEqual(math_eval.evaluate("5*-2", "decimal"), -10)
        self.assertEqual(math_eval.evaluate("-(2+3)", "decimal"), -5)

    def test_syntax_errors(self) -> None:
        self.assertIsNone(math_eval.evaluate("5+", "decimal"))
        self.assertIsNone(math_eval.evaluate("(5", "decimal"))
        self.assertIsNone(math_eval.evaluate("5*", "decimal"))
        self.assertIsNone(math_eval.evaluate("5 5", "decimal"))
        self.assertIsNone(math_eval.evaluate("", "decimal"))
        self.assertIsNone(math_eval.evaluate("   ", "decimal"))

    def test_invalid_char(self) -> None:
        self.assertIsNone(math_eval.evaluate("5&3", "decimal"))
        self.assertIsNone(math_eval.evaluate("GG+1", "hex_direct"))

    def test_too_big_result(self) -> None:
        # 9^9^9 — сотни миллионов цифр: защита от зависания UI
        self.assertIsNone(math_eval.evaluate("9^9^9", "decimal"))
        self.assertIsNone(math_eval.evaluate("2^10000", "decimal"))
        self.assertEqual(math_eval.evaluate("2^4000", "decimal"), 2 ** 4000)

    def test_char_format_not_supported(self) -> None:
        self.assertIsNone(math_eval.evaluate("A+B", "unicode_char"))

    def test_is_expression(self) -> None:
        self.assertFalse(math_eval.is_expression("42"))
        self.assertFalse(math_eval.is_expression("-42"))
        self.assertFalse(math_eval.is_expression("4.5"))
        self.assertTrue(math_eval.is_expression("42+2"))
        self.assertTrue(math_eval.is_expression("5*-2"))
        self.assertTrue(math_eval.is_expression("2^2"))
        self.assertTrue(math_eval.is_expression("(2)"))
        self.assertFalse(math_eval.is_expression(" "))


class TestMathEvalParseIntegration(unittest.TestCase):
    """Converter.parse: выражения считаются, обычные числа — как раньше."""

    def test_parse_expression_decimal(self) -> None:
        self.assertEqual(Converter.parse("2+2", "decimal", 8), 4)
        self.assertEqual(Converter.parse("5+3.5", "decimal", 8), 8.5)

    def test_parse_expression_hex(self) -> None:
        self.assertEqual(Converter.parse("FF+01", "hex_direct", 8), 256)

    def test_parse_expression_bin(self) -> None:
        self.assertEqual(Converter.parse("101+11", "bin_direct", 8), 8)

    def test_parse_plain_unchanged(self) -> None:
        self.assertEqual(Converter.parse("42", "decimal", 8), 42)
        self.assertEqual(Converter.parse("-42", "decimal", 8), -42)
        self.assertEqual(Converter.parse("42.5", "decimal", 8), 42.5)
        self.assertEqual(Converter.parse("FF", "hex_direct", 8), 255)

    def test_parse_big_int_unchanged(self) -> None:
        self.assertEqual(
            Converter.parse("-72057594037927935", "decimal", 8),
            -72057594037927935,
        )

    def test_round_trip_expression_to_hex(self) -> None:
        value = Converter.parse("2+2", "decimal", 8)
        self.assertEqual(Converter.convert(value, "hex_direct", 8), "04")

    def test_fractional_expression_integer_formats_empty(self) -> None:
        value = Converter.parse("7/2", "decimal", 8)
        self.assertIsNone(Converter.convert(value, "hex_direct", 8))
        self.assertIsNotNone(Converter.convert(value, "ieee_hex", 4))


class TestCalculatorEnterField(unittest.TestCase):
    """Enter в поле с выражением: замена на результат + запись в лог."""

    qapp: "QApplication"

    @classmethod
    def setUpClass(cls) -> None:
        cls.qapp = QApplication.instance() or QApplication(sys.argv)

    def test_enter_replaces_expression_and_logs(self) -> None:
        from PyQt6.QtCore import Qt
        from PyQt6.QtTest import QTest
        from widgets.converter_widget import ConverterWidget

        logs: list = []
        w = ConverterWidget(None, None, None, lambda e, r, f: logs.append((e, r, f)))
        w.show()
        QTest.qWait(50)  # дождаться отложенной сборки полей (QTimer.singleShot(10))
        dec = w.fields["decimal"]
        # Живая конвертация: другие поля сразу получили результат
        # (offscreen не даёт фокус, поэтому вызываем ту же процедуру,
        #  что _on_field_changed вызывает после проверки фокуса)
        w._convert_from_source("5+3", dec)
        self.assertEqual(w.fields["hex_direct"].text_edit.toPlainText(), "08")
        # Выражение в поле, Enter — замена на результат и запись в лог
        dec.set_value_silent("5+3")
        QTest.keyClick(dec.text_edit, Qt.Key.Key_Return)
        self.assertEqual(dec.text_edit.toPlainText(), "8")
        self.assertEqual(logs, [("5+3", "8", "decimal")])

    def test_enter_on_plain_number_does_nothing(self) -> None:
        from PyQt6.QtCore import Qt
        from PyQt6.QtTest import QTest
        from widgets.converter_widget import ConverterWidget

        logs: list = []
        w = ConverterWidget(None, None, None, lambda e, r, f: logs.append((e, r, f)))
        w.show()
        QTest.qWait(50)  # дождаться отложенной сборки полей (QTimer.singleShot(10))
        dec = w.fields["decimal"]
        dec.set_value_silent("42")
        QTest.keyClick(dec.text_edit, Qt.Key.Key_Return)
        self.assertEqual(dec.text_edit.toPlainText(), "42")
        self.assertEqual(logs, [])


if __name__ == "__main__":
    unittest.main()
