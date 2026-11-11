# tests/test_layout_hint.py
# project_root/tests/test_layout_hint.py
# Python 3.11+, PyQt6
# Подсказка при отклонении кириллицы (русская раскладка): поле шлёт
# сигнал layout_hint, виджет конвертера передаёт текст в статус-бар.

import os
import sys
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from widgets.base_field import NumberField
from widgets.byte_field import ByteGroupField
from widgets.converter_widget import ConverterWidget


class TestLayoutHintField(unittest.TestCase):
    """Поле шлёт layout_hint только когда в ОТКЛОНЁННЫХ данных есть кириллица."""

    # Ссылку держим на классе: без неё QApplication соберётся, и виджеты падут
    qapp: QApplication

    @classmethod
    def setUpClass(cls) -> None:
        cls.qapp = QApplication.instance() or QApplication(sys.argv)

    def _collect(self, field) -> list:
        messages: list = []
        field.layout_hint.connect(messages.append)
        return messages

    def test_cyrillic_rejected_emits_hint(self) -> None:
        field = ByteGroupField("HEX прямой код:", "hex_direct", is_long=True)
        messages = self._collect(field)
        field.text_edit.insertPlainText("Ф")  # кириллица не допускается в HEX
        self.assertEqual(field.text_edit.toPlainText(), "")
        self.assertEqual(messages, [NumberField.LAYOUT_HINT])

    def test_non_cyrillic_invalid_no_hint(self) -> None:
        field = ByteGroupField("HEX прямой код:", "hex_direct", is_long=True)
        messages = self._collect(field)
        field.text_edit.insertPlainText("G")  # латиница, но не HEX-цифра
        self.assertEqual(messages, [])

    def test_valid_cyrillic_in_unicode_no_hint(self) -> None:
        field = NumberField("UNICODE символ:", "unicode_char")
        messages = self._collect(field)
        field.text_edit.insertPlainText("Ф")  # для unicode-символа валидно
        self.assertEqual(field.text_edit.toPlainText(), "Ф")
        self.assertEqual(messages, [])

    def test_second_latin_char_in_unicode_no_hint(self) -> None:
        # Второй символ отклоняется (длина), но это не кириллица — подсказки нет
        field = NumberField("UNICODE символ:", "unicode_char")
        messages = self._collect(field)
        field.text_edit.insertPlainText("Ф")
        field.text_edit.insertPlainText("a")
        self.assertEqual(field.text_edit.toPlainText(), "Ф")
        self.assertEqual(messages, [])


class TestLayoutHintWidget(unittest.TestCase):
    """Подсказка доходит до статус-колбэка и исчезает после валидной правки."""

    qapp: QApplication

    @classmethod
    def setUpClass(cls) -> None:
        cls.qapp = QApplication.instance() or QApplication(sys.argv)

    def test_hint_reaches_status_and_clears_on_valid_edit(self) -> None:
        calls: list = []
        widget = ConverterWidget(focus_callback=lambda hint=None: calls.append(hint))
        widget.show()
        QTest.qWait(100)  # дожидаемся _build_fields (QTimer 10 мс)
        try:
            field = widget.fields["hex_direct"]
            field.text_edit.insertPlainText("Ф")
            self.assertIn(NumberField.LAYOUT_HINT, calls)
            calls.clear()
            field.text_edit.insertPlainText("A")  # валидная правка
            self.assertIn(None, calls)
        finally:
            QTest.qWait(20)  # досмотреть отложенные singleShot(1) живыми объектами
            widget.deleteLater()


if __name__ == "__main__":
    unittest.main()
