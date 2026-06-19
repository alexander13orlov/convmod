# widgets/modbus_widget.py
# Python 3.11+, PyQt6

import logging
from typing import Optional, Dict, Any, TYPE_CHECKING
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
                             QLabel, QLineEdit, QGroupBox, QTextEdit, QCheckBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QTextCursor, QColor, QTextCharFormat
from widgets.modbus.modbus_parser import ModbusParser
from widgets.log_widget import LogWidget

if TYPE_CHECKING:
    from widgets.main_window import MainWindow

logger = logging.getLogger(__name__)

class ModbusWidget(QWidget):
    def __init__(self, parent: Optional["MainWindow"] = None, config: Optional[Dict] = None):
        super().__init__(parent)
        self.parser = ModbusParser()
        self.config = config or {}
        self.log_widget: Optional[LogWidget] = None
        self._setup_ui()
        self._load_config()
        self._on_protocol_changed()
    
    def set_log_widget(self, log_widget: LogWidget):
        self.log_widget = log_widget
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)

        settings_group = QGroupBox()
        settings_layout = QHBoxLayout(settings_group)
        settings_layout.setContentsMargins(5, 5, 5, 5)
        
        settings_layout.addWidget(QLabel("Протокол:"))
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(["ASCII", "RTU", "TCP"])
        self.protocol_combo.currentTextChanged.connect(self._on_protocol_changed)
        settings_layout.addWidget(self.protocol_combo)
        
        settings_layout.addSpacing(20)
        
        settings_layout.addWidget(QLabel("Направление:"))
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["Request", "Response"])
        self.direction_combo.currentTextChanged.connect(self._on_direction_changed)
        settings_layout.addWidget(self.direction_combo)
        
        self.slave_checkbox = QCheckBox("Slave ID")
        self.slave_checkbox.setChecked(True)
        self.slave_checkbox.stateChanged.connect(self._on_analyze)
        
        self.crc_checkbox = QCheckBox("CRC16")
        self.crc_checkbox.setChecked(True)
        self.crc_checkbox.stateChanged.connect(self._on_analyze)
        
        self.rtu_options_layout = QHBoxLayout()
        self.rtu_options_layout.addWidget(self.slave_checkbox)
        self.rtu_options_layout.addWidget(self.crc_checkbox)
        self.rtu_options_layout.addStretch()
        
        settings_layout.addLayout(self.rtu_options_layout)
        settings_layout.addStretch()
        
        layout.addWidget(settings_group)

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("HEX (пробелы игнорируются)")
        self.input_edit.setFont(QFont("Courier New", 10))
        self.input_edit.setMaximumHeight(30)
        self.input_edit.textChanged.connect(self._on_analyze)
        layout.addWidget(self.input_edit)

        result_group = QGroupBox("Результаты анализа")
        result_layout = QVBoxLayout(result_group)
        result_layout.setContentsMargins(5, 5, 5, 5)
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setFont(QFont("Courier New", 9))
        self.result_text.setMaximumHeight(300)
        result_layout.addWidget(self.result_text)
        layout.addWidget(result_group)
    
    def _on_protocol_changed(self):
        protocol = self.protocol_combo.currentText()
        if protocol == "RTU":
            self.slave_checkbox.setVisible(True)
            self.crc_checkbox.setVisible(True)
        else:
            self.slave_checkbox.setVisible(False)
            self.crc_checkbox.setVisible(False)
        
        self._delayed_save()
        self._on_analyze()
    
    def _on_direction_changed(self):
        self._delayed_save()
        self._on_analyze()
    
    def _delayed_save(self):
        parent = self.parent()
        if parent is not None and hasattr(parent, 'save_config'):
            parent.save_config()  # type: ignore[attr-defined]
    
    def get_config(self) -> Dict:
        return {
            "protocol": self.protocol_combo.currentText(),
            "direction": self.direction_combo.currentText(),
            "rtu_slave_id_enabled": self.slave_checkbox.isChecked(),
            "rtu_crc_enabled": self.crc_checkbox.isChecked()
        }
    
    def _load_config(self):
        modbus_config = self.config.get("modbus", {})
        protocol = modbus_config.get("protocol", "TCP")
        direction = modbus_config.get("direction", "Request")
        
        index = self.protocol_combo.findText(protocol)
        if index >= 0:
            self.protocol_combo.setCurrentIndex(index)
        
        index = self.direction_combo.findText(direction)
        if index >= 0:
            self.direction_combo.setCurrentIndex(index)
        
        self.slave_checkbox.setChecked(modbus_config.get("rtu_slave_id_enabled", True))
        self.crc_checkbox.setChecked(modbus_config.get("rtu_crc_enabled", True))
    
    def _on_analyze(self):
        raw = self.input_edit.text()
        if not raw.strip():
            self.result_text.clear()
            return

        input_str = raw.replace(' ', '').replace('\n', '').replace('\r', '')
        protocol = self.protocol_combo.currentText()
        is_response = (self.direction_combo.currentText() == "Response")
        
        if protocol == "RTU":
            result = self.parser.parse_rtu_with_options(
                input_str, is_response, 
                include_slave=self.slave_checkbox.isChecked(),
                include_crc=self.crc_checkbox.isChecked()
            )
        else:
            result = self.parser.parse(input_str, protocol, is_response)
        
        self._display_result(result, input_str)
        
        if self.log_widget:
            direction_text = self.direction_combo.currentText()
            self.log_widget.add_entry(protocol, direction_text, input_str, result.get("valid", False))
    
    def _display_result(self, result: Dict[str, Any], raw_hex: str):
        self.result_text.clear()
        cursor = self.result_text.textCursor()

        self._append_color(cursor, "=== Modbus Analysis ===\n", QColor(0, 0, 255))

        if "protocol" in result:
            self._append_color(cursor, f"Protocol: ", QColor(0, 0, 0))
            self._append_color(cursor, f"{result['protocol']}\n", QColor(0, 128, 0))

        if result.get("settings"):
            settings = result["settings"]
            self._append_color(cursor, "Analysis Settings:\n", QColor(0, 100, 200))
            self._append_color(cursor, f"  Slave ID in data: ", QColor(0, 0, 0))
            color = QColor(0, 128, 0) if settings.get("slave_id_included") else QColor(255, 100, 0)
            self._append_color(cursor, f"{'Yes' if settings.get('slave_id_included') else 'No'}\n", color)
            self._append_color(cursor, f"  CRC in data: ", QColor(0, 0, 0))
            color = QColor(0, 128, 0) if settings.get("crc_included") else QColor(255, 100, 0)
            self._append_color(cursor, f"{'Yes' if settings.get('crc_included') else 'No'}\n", color)
            cursor.insertText("\n")

        if result.get("structure_valid"):
            self._append_color(cursor, "Frame structure: ", QColor(0, 0, 0))
            self._append_color(cursor, "MATCHES settings\n", QColor(0, 128, 0))
        else:
            self._append_color(cursor, "Frame structure: ", QColor(0, 0, 0))
            self._append_color(cursor, "DOES NOT MATCH settings\n", QColor(255, 0, 0))

        self._append_color(cursor, f"Direction: {self.direction_combo.currentText()}\n", QColor(0, 0, 255))
        cursor.insertText("\n")

        if result.get("errors"):
            self._append_color(cursor, "Errors:\n", QColor(255, 0, 0))
            for err in result["errors"]:
                self._append_color(cursor, f"  • {err}\n", QColor(255, 0, 0))
            cursor.insertText("\n")

        self._append_color(cursor, "Frame Details:\n", QColor(0, 0, 255))

        if "slave_address" in result and result["slave_address"] is not None:
            self._append_color(cursor, "  Slave Address: ", QColor(0, 0, 0))
            self._append_color(cursor, f"0x{result['slave_address']:02X} ({result['slave_address']})\n", QColor(128, 0, 128))

        if "unit_id" in result:
            self._append_color(cursor, "  Unit ID: ", QColor(0, 0, 0))
            self._append_color(cursor, f"0x{result['unit_id']:02X} ({result['unit_id']})\n", QColor(128, 0, 128))

        if "function_code" in result:
            self._append_color(cursor, "  Function Code: ", QColor(0, 0, 0))
            self._append_color(cursor, f"0x{result['function_code']:02X} ", QColor(128, 0, 128))
            self._append_color(cursor, f"({result.get('function_name', 'Unknown')})\n", QColor(128, 0, 128))

        if result.get("is_exception"):
            if "original_function_code" in result:
                self._append_color(cursor, "  Original Function: ", QColor(0, 0, 0))
                self._append_color(cursor, f"0x{result['original_function_code']:02X}\n", QColor(255, 0, 0))
            if "exception_code" in result:
                self._append_color(cursor, "  Exception Code: ", QColor(0, 0, 0))
                self._append_color(cursor, f"0x{result['exception_code']:02X}\n", QColor(255, 0, 0))
            if "exception_description" in result:
                self._append_color(cursor, "  Exception Description: ", QColor(0, 0, 0))
                self._append_color(cursor, f"{result['exception_description']}\n", QColor(255, 0, 0))

        if "start_address" in result:
            self._append_color(cursor, "  Start Address: ", QColor(0, 0, 0))
            self._append_color(cursor, f"0x{result['start_address']:04X} ({result['start_address']})\n", QColor(128, 0, 128))

        if "quantity" in result:
            self._append_color(cursor, "  Quantity: ", QColor(0, 0, 0))
            self._append_color(cursor, f"{result['quantity']}\n", QColor(128, 0, 128))

        if "value" in result:
            self._append_color(cursor, "  Value: ", QColor(0, 0, 0))
            self._append_color(cursor, f"0x{result['value']:04X} ({result['value']})\n", QColor(128, 0, 128))

        if "byte_count" in result:
            self._append_color(cursor, "  Byte Count: ", QColor(0, 0, 0))
            self._append_color(cursor, f"{result['byte_count']}\n", QColor(128, 0, 128))

        if "registers" in result and result["registers"]:
            self._append_color(cursor, "  Register Values:\n", QColor(0, 0, 0))
            for i, val in enumerate(result["registers"]):
                self._append_color(cursor, f"    Register {i+1}: ", QColor(0, 0, 0))
                self._append_color(cursor, f"0x{val:04X} ({val})\n", QColor(128, 0, 128))

        if "crc_received" in result:
            self._append_color(cursor, "\n  CRC Received: ", QColor(0, 0, 0))
            self._append_color(cursor, f"{result['crc_received']}\n", QColor(128, 0, 128))
            self._append_color(cursor, "  CRC Calculated: ", QColor(0, 0, 0))
            crc_calc = result.get('crc_calculated', 'Unknown')
            if crc_calc == "Unknown (Slave ID missing)":
                self._append_color(cursor, f"{crc_calc}\n", QColor(255, 165, 0))
            else:
                self._append_color(cursor, f"{crc_calc}\n", QColor(128, 0, 128))
            
            self._append_color(cursor, "  CRC Valid: ", QColor(0, 0, 0))
            crc_valid = result.get("crc_valid")
            if crc_valid is True:
                self._append_color(cursor, "Yes\n", QColor(0, 128, 0))
            elif crc_valid is False:
                self._append_color(cursor, "No\n", QColor(255, 0, 0))
            else:
                self._append_color(cursor, "Cannot determine (missing Slave ID)\n", QColor(255, 165, 0))
            cursor.insertText("\n")

        if "lrc_received" in result:
            self._append_color(cursor, "\n  LRC Received: ", QColor(0, 0, 0))
            self._append_color(cursor, f"{result['lrc_received']}\n", QColor(128, 0, 128))
            self._append_color(cursor, "  LRC Calculated: ", QColor(0, 0, 0))
            self._append_color(cursor, f"{result['lrc_calculated']}\n", QColor(128, 0, 128))
            self._append_color(cursor, "  LRC Valid: ", QColor(0, 0, 0))
            color = QColor(0, 128, 0) if result.get("lrc_valid") else QColor(255, 0, 0)
            self._append_color(cursor, "Yes" if result.get("lrc_valid") else "No", color)
            cursor.insertText("\n")

        if "transaction_id" in result:
            self._append_color(cursor, "\n  Transaction ID: ", QColor(0, 0, 0))
            self._append_color(cursor, f"0x{result['transaction_id']:04X}\n", QColor(128, 0, 128))
            self._append_color(cursor, "  Protocol ID: ", QColor(0, 0, 0))
            self._append_color(cursor, f"0x{result['protocol_id']:04X}\n", QColor(128, 0, 128))
            self._append_color(cursor, "  Length: ", QColor(0, 0, 0))
            self._append_color(cursor, f"{result['length']}\n", QColor(128, 0, 128))

        cursor.insertText("\n")
        self._append_color(cursor, "Raw Data (HEX):\n", QColor(0, 0, 255))
        
        display_hex = result.get("original_raw", raw_hex)
        formatted_hex = ' '.join([display_hex[i:i+2] for i in range(0, len(display_hex), 2)])
        for i in range(0, len(formatted_hex), 48):
            line = "  " + formatted_hex[i:i+48]
            self._append_color(cursor, f"{line}\n", QColor(100, 100, 100))

    def _append_color(self, cursor: QTextCursor, text: str, color: QColor):
        fmt = QTextCharFormat()
        fmt.setForeground(color)
        cursor.insertText(text, fmt)
    
    def on_tab_activated(self):
        QTimer.singleShot(50, self._set_focus)
    
    def _set_focus(self):
        self.input_edit.setFocus()
        self.input_edit.selectAll()