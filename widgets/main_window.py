# widgets/main_window.py (исправлен - обработка ошибки disconnect)
# Python 3.11+, PyQt6

from typing import Optional, Dict
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QStatusBar, QTabWidget, QLabel
)
from PyQt6.QtCore import Qt, QTimer
from widgets.converter_widget import ConverterWidget
from widgets.settings_widget import SettingsWidget
from widgets.help_widget import HelpWidget
from widgets.modbus_widget import ModbusWidget
from widgets.log_widget import LogWidget
from config_manager import ConfigManager


class MainWindow(QMainWindow):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("ConvMod")
        self.setMinimumSize(400, 200)
        
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load()
        self._modbus_signals_connected = False
        
        self._setup_ui()
        self._setup_status_bar()
        
        QTimer.singleShot(50, self._initial_resize)
        QTimer.singleShot(100, self._set_focus_to_converter)
    
    def _set_focus_to_converter(self) -> None:
        if hasattr(self, 'converter_widget') and self.converter_widget.fields:
            decimal_field = self.converter_widget.fields.get("decimal")
            if decimal_field is not None:
                decimal_field.text_edit.setFocus()
                cursor = decimal_field.text_edit.textCursor()
                cursor.movePosition(cursor.MoveOperation.End)
                decimal_field.text_edit.setTextCursor(cursor)
    
    def _initial_resize(self) -> None:
        if self.converter_widget.fields:
            visible_count = sum(1 for v in self.converter_widget.visible_fields.values() if v)
            first_field = next(iter(self.converter_widget.fields.values()))
            if first_field is not None:
                field_height = first_field.minimumSizeHint().height()
                self.resize_to_fit(visible_count, field_height)
    
    def _setup_ui(self) -> None:
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        
        self.converter_widget = ConverterWidget(self, self._update_status_info, self._update_status_info)
        self.converter_widget.update_visible_fields(self.config.get("converter", {}).get("visible_fields", {}))
        
        self.settings_widget = SettingsWidget(self, self.converter_widget.visible_fields)
        self.settings_widget.settingsChanged.connect(self._apply_settings)
        
        self.log_widget = LogWidget(self)
        
        self.modbus_widget = ModbusWidget(self, self.config)
        self.modbus_widget.set_log_widget(self.log_widget)
        
        self.help_widget = HelpWidget(self)
        
        self.tab_widget.addTab(self.converter_widget, "Конвертер")
        self.tab_widget.addTab(self.settings_widget, "Настройка")
        self.tab_widget.addTab(self.modbus_widget, "Modbus")
        self.tab_widget.addTab(self.log_widget, "Лог")
        self.tab_widget.addTab(self.help_widget, "Справка")
        
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
    
    def _on_tab_changed(self, index: int) -> None:
        tab_text = self.tab_widget.tabText(index)
        if tab_text == "Modbus":
            self.modbus_widget.on_tab_activated()
            if not self._modbus_signals_connected:
                self.modbus_widget.input_edit.textChanged.connect(self._update_status_from_modbus)
                self.modbus_widget.input_edit.cursorPositionChanged.connect(self._update_status_from_modbus)
                self.modbus_widget.input_edit.selectionChanged.connect(self._update_status_from_modbus)
                self._modbus_signals_connected = True
            self._update_status_from_modbus()
            self.resize(650, 500)
        elif tab_text == "Конвертер":
            if self._modbus_signals_connected:
                try:
                    self.modbus_widget.input_edit.textChanged.disconnect(self._update_status_from_modbus)
                    self.modbus_widget.input_edit.cursorPositionChanged.disconnect(self._update_status_from_modbus)
                    self.modbus_widget.input_edit.selectionChanged.disconnect(self._update_status_from_modbus)
                except TypeError:
                    pass
                self._modbus_signals_connected = False
            self._update_status_info()
            if self.converter_widget.fields:
                visible_count = sum(1 for v in self.converter_widget.visible_fields.values() if v)
                first_field = next(iter(self.converter_widget.fields.values()))
                if first_field is not None:
                    field_height = first_field.minimumSizeHint().height()
                    self.resize_to_fit(visible_count, field_height)
    
    def _update_status_from_modbus(self) -> None:
        """Обновление статусной строки для Modbus вкладки"""
        text = self.modbus_widget.input_edit.text()
        total_chars = len(text)
        selected_chars = len(self.modbus_widget.input_edit.selectedText())
        
        clean_text = text.replace(' ', '').replace('\n', '').replace('\r', '')
        byte_count = len(clean_text) // 2 if len(clean_text) % 2 == 0 else len(clean_text) // 2 + 1
        
        self.status_info.setText(f"Байт: {byte_count} | Символов: {total_chars} | Выделено: {selected_chars}")
    
    def resize_to_fit(self, visible_count: int, field_height: int) -> None:
        status_bar = self.statusBar()
        status_height = status_bar.height() if status_bar is not None else 25
        tab_bar = self.tab_widget.tabBar()
        tab_height = tab_bar.height() if tab_bar is not None else 30
        total_height = tab_height + status_height + visible_count * (field_height + 2) + 10
        self.setMinimumHeight(total_height)
        self.resize(self.width(), total_height)
    
    def _apply_settings(self, new_visible: Dict[str, bool]) -> None:
        self.converter_widget.update_visible_fields(new_visible)
        self.config["converter"]["visible_fields"] = new_visible
        self.save_config()
        self._update_status_info()
    
    def save_config(self) -> None:
        if hasattr(self, 'modbus_widget') and self.modbus_widget is not None:
            self.config["modbus"] = self.modbus_widget.get_config()
        self.config_manager.save(self.config)
    
    def _setup_status_bar(self) -> None:
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_info = QLabel("Готов")
        self.status_bar.addWidget(self.status_info)
    
    def _update_status_info(self) -> None:
        active = self.converter_widget.get_active_field()
        if active is not None:
            text = active.get_raw_value()
            total_chars = len(text)
            
            text_edit = active.text_edit
            cursor = text_edit.textCursor()
            selected_text = cursor.selectedText()
            selected_chars = len(selected_text)
            
            nb_text = self.converter_widget.nb_display.text()
            
            self.status_info.setText(f"Байт: {nb_text} | Символов: {total_chars} | Выделено: {selected_chars}")
        else:
            nb_text = self.converter_widget.nb_display.text()
            self.status_info.setText(f"Байт: {nb_text} | Символов: 0 | Выделено: 0")