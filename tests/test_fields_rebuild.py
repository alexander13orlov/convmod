# tests/test_fields_rebuild.py
# project_root/tests/test_fields_rebuild.py
# Python 3.11+, PyQt6
# Пересборка полей конвертера (смена настроек): значения не должны
# теряться; вновь показанное поле получает сконвертированное значение.

import os
import sys
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from widgets.converter_widget import ConverterWidget


class TestFieldsRebuildKeepsValues(unittest.TestCase):
    """После пересборки (смена настроек) значения полей сохраняются."""

    # Ссылку держим на классе: без неё QApplication соберётся, и виджеты падут
    qapp: QApplication

    @classmethod
    def setUpClass(cls) -> None:
        cls.qapp = QApplication.instance() or QApplication(sys.argv)

    def _make_widget(self) -> ConverterWidget:
        widget = ConverterWidget()
        widget.show()
        QTest.qWait(100)  # дожидаемся _build_fields (QTimer 10 мс)
        return widget

    def test_rebuild_keeps_converted_values(self) -> None:
        widget = self._make_widget()
        try:
            # Пользователь ввёл 25: источник и остальные поля заполнены
            widget.fields["decimal"].set_value_silent("25")
            widget.fields["hex_direct"].set_value_silent("19")
            widget.fields["bin_direct"].set_value_silent("00011001")
            QTest.qWait(50)  # отложенные singleShot подсветки сработают, пока поля живы
            # Смена настроек (таб «Настройка») — пересборка полей
            widget.update_visible_fields(dict(widget.visible_fields))
            QTest.qWait(100)
            self.assertEqual(widget.fields["decimal"].get_raw_value(), "25")
            self.assertEqual(widget.fields["hex_direct"].get_raw_value(), "19")
            self.assertEqual(widget.fields["bin_direct"].get_raw_value(), "00011001")
        finally:
            QTest.qWait(100)  # досмотреть отложенные singleShot живыми объектами
            widget.deleteLater()

    def test_newly_shown_field_gets_value(self) -> None:
        widget = self._make_widget()
        try:
            widget.fields["decimal"].set_value_silent("25")
            QTest.qWait(50)
            # Скрываем hex_direct (пользователь убрал поле в настройках)
            hidden = dict(widget.visible_fields)
            hidden["hex_direct"] = False
            widget.update_visible_fields(hidden)
            QTest.qWait(100)
            self.assertNotIn("hex_direct", widget.fields)
            # Включаем обратно — новое поле должно получить значение
            shown = dict(widget.visible_fields)
            shown["hex_direct"] = True
            widget.update_visible_fields(shown)
            QTest.qWait(100)
            self.assertEqual(widget.fields["decimal"].get_raw_value(), "25")
            self.assertEqual(widget.fields["hex_direct"].get_raw_value(), "19")
        finally:
            QTest.qWait(100)
            widget.deleteLater()


if __name__ == "__main__":
    unittest.main()
