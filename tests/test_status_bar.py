# tests/test_status_bar.py
# project_root/tests/test_status_bar.py
# Python 3.11+, PyQt6
# Статусная строка: счётчик байтов Modbus (только HEX цифры),
# nb_display в выражениях (операторы не считаются байтами),
# сброс подсказки на служебных вкладках.

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication


class TestModbusByteCount(unittest.TestCase):
    """Счётчик байтов Modbus: только HEX цифры, как в парсере."""

    def test_dashes_and_spaces_not_counted(self) -> None:
        from widgets.main_window import MainWindow
        # 18 HEX цифр = 9 байт; тире и пробелы не учитываются
        text = "01-10-4B-00-00-01-02-00-------01    "
        self.assertEqual(MainWindow._modbus_byte_count(text), 9)

    def test_plain_hex(self) -> None:
        from widgets.main_window import MainWindow
        self.assertEqual(MainWindow._modbus_byte_count("0110"), 2)

    def test_odd_rounds_up(self) -> None:
        from widgets.main_window import MainWindow
        self.assertEqual(MainWindow._modbus_byte_count("01F"), 2)

    def test_only_separators(self) -> None:
        from widgets.main_window import MainWindow
        self.assertEqual(MainWindow._modbus_byte_count("----   "), 0)

    def test_empty(self) -> None:
        from widgets.main_window import MainWindow
        self.assertEqual(MainWindow._modbus_byte_count(""), 0)


class TestNbDisplayExpressions(unittest.TestCase):
    """nb_display: в выражениях считаются только цифры формата."""

    qapp: "QApplication"

    @classmethod
    def setUpClass(cls) -> None:
        cls.qapp = QApplication.instance() or QApplication(sys.argv)

    def _nb(self, value: str, fmt: str) -> str:
        from widgets.converter_widget import ConverterWidget
        w = ConverterWidget()
        w._update_nb_display(value, fmt)
        return w.nb_display.text()

    def test_hex_expression(self) -> None:
        # FF+01: 4 цифры = 2 байта; «+» не считается
        self.assertEqual(self._nb("FF+01", "hex_direct"), "2")

    def test_hex_expression_with_spaces(self) -> None:
        self.assertEqual(self._nb("FF + 01", "hex_direct"), "2")

    def test_bin_expression(self) -> None:
        # 1010+1010: 8 цифр = 1 байт
        self.assertEqual(self._nb("1010+1010", "bin_direct"), "1")

    def test_decimal_expression_by_result(self) -> None:
        # 5+3 = 8 → по значению 1 байт
        self.assertEqual(self._nb("5+3", "decimal"), "1")

    def test_decimal_division_result_float(self) -> None:
        # 7/2 = 3.5 → дробный результат → 4 байта (float32)
        self.assertEqual(self._nb("7/2", "decimal"), "4")

    def test_incomplete_expression(self) -> None:
        self.assertEqual(self._nb("5+", "decimal"), "0")

    def test_plain_hex_regression(self) -> None:
        self.assertEqual(self._nb("08", "hex_direct"), "1")
        self.assertEqual(self._nb("0808", "hex_direct"), "2")

    def test_signed_hex_sign_is_not_a_byte(self) -> None:
        # -08: знак не байт, 2 цифры = 1 байт
        self.assertEqual(self._nb("-08", "hex_direct"), "1")

    def test_plain_bin_regression(self) -> None:
        self.assertEqual(self._nb("10", "bin_complement"), "1")
        self.assertEqual(self._nb("1010101010", "bin_direct"), "2")


class TestServiceTabsStatusReset(unittest.TestCase):
    """На служебных вкладках статус-бар не держит подсказку о байтах."""

    qapp: "QApplication"

    @classmethod
    def setUpClass(cls) -> None:
        cls.qapp = QApplication.instance() or QApplication(sys.argv)

    def test_only_data_tabs_show_byte_hint(self) -> None:
        from PyQt6.QtTest import QTest
        from widgets.main_window import MainWindow
        w = MainWindow()
        w.show()
        QTest.qWait(100)  # отложенная сборка полей конвертера
        try:
            for idx in range(w.tab_widget.count()):
                w.tab_widget.setCurrentIndex(idx)
                text = w.status_info.text()
                if w.tab_widget.tabText(idx) in ("Modbus", "Конвертер"):
                    self.assertIn("Байт", text)
                else:
                    self.assertEqual(text, "Готов")
        finally:
            w.close()


if __name__ == "__main__":
    unittest.main()