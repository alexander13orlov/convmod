# widgets/modbus_widget.py
# Python 3.11+, PyQt6

import logging
import re
from typing import Optional, Dict, Any, TYPE_CHECKING
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
                             QLabel, QLineEdit, QGroupBox, QTextEdit, QCheckBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QTextCursor, QColor, QTextCharFormat
from widgets.modbus.modbus_parser import ModbusParser
from widgets.modbus.parser_pdu import PDUParser
from widgets.log_widget import LogWidget
from widgets.base_field import get_mono_font

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
        self.input_edit.setFont(get_mono_font(10))
        self.input_edit.setMaximumHeight(30)
        self.input_edit.textChanged.connect(self._on_analyze)
        layout.addWidget(self.input_edit)

        result_group = QGroupBox("Результаты анализа")
        result_layout = QVBoxLayout(result_group)
        result_layout.setContentsMargins(5, 5, 5, 5)
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setFont(get_mono_font(9))
        result_layout.addWidget(self.result_text)
        result_layout.setStretchFactor(self.result_text, 1)
        
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
            save_func = getattr(parent, 'save_config', None)
            if save_func is not None and callable(save_func):
                save_func()
    
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

        protocol = self.protocol_combo.currentText()
        is_response = (self.direction_combo.currentText() == "Response")
        
        if protocol == "RTU":
            result = self.parser.parse_rtu_with_options(
                raw, is_response, 
                include_slave=self.slave_checkbox.isChecked(),
                include_crc=self.crc_checkbox.isChecked()
            )
        else:
            result = self.parser.parse(raw, protocol, is_response)
        
        self._display_result(result, raw)
        
        if self.log_widget:
            direction_text = self.direction_combo.currentText()
            self.log_widget.add_entry(protocol, direction_text, raw, result.get("valid", False))

    def _display_result(self, result: Dict[str, Any], raw_hex: str):
        self.result_text.clear()
        cursor = self.result_text.textCursor()
        
        colors = {
            'header': QColor(0, 0, 255),
            'transaction': QColor(128, 0, 128),
            'protocol': QColor(0, 128, 128),
            'length': QColor(255, 140, 0),
            'unit': QColor(0, 100, 200),
            'function': QColor(0, 128, 0),
            'address': QColor(200, 50, 50),
            'quantity': QColor(200, 100, 0),
            'byte_count': QColor(0, 150, 200),
            'register': QColor(100, 100, 200),
            'crc': QColor(200, 0, 200),
            'lrc': QColor(0, 150, 150),
            'warning': QColor(255, 165, 0),
            'default': QColor(100, 100, 100)
        }
        
        protocol = result.get("protocol", "")
        is_tcp = protocol == "TCP"
        is_rtu = protocol == "RTU"
        is_ascii = protocol == "ASCII"
        
        # Для ASCII используем raw_hex_full из результата
        if is_ascii:
            display_hex = result.get("raw_hex_full", raw_hex)
            # Убираем не-HEX символы
            display_hex = re.sub(r'[^0-9A-Fa-f]', '', display_hex)
        else:
            display_hex = result.get("raw_hex_clean", raw_hex)
        
        hex_bytes = [display_hex[i:i+2].upper() for i in range(0, len(display_hex), 2)]
        byte_colors = [colors['default']] * len(hex_bytes)
        byte_index = 0
        
        self._append_color(cursor, "=== Modbus Analysis ===\n", colors['header'])
        
        if protocol:
            self._append_color(cursor, f"Protocol: {protocol}\n", QColor(0, 0, 0))
        
        if result.get("structure_valid"):
            self._append_color(cursor, "Frame structure: ", QColor(0, 0, 0))
            self._append_color(cursor, "MATCHES settings\n", QColor(0, 128, 0))
        else:
            self._append_color(cursor, "Frame structure: ", QColor(0, 0, 0))
            self._append_color(cursor, "DOES NOT MATCH settings\n", QColor(255, 0, 0))
        
        self._append_color(cursor, f"Direction: {self.direction_combo.currentText()}\n", QColor(0, 0, 0))
        cursor.insertText("\n")
        
        if result.get("errors"):
            self._append_color(cursor, "Errors:\n", QColor(255, 0, 0))
            for err in result["errors"]:
                self._append_color(cursor, f"  • {err}\n", QColor(255, 0, 0))
            cursor.insertText("\n")
        
        if result.get("warnings"):
            self._append_color(cursor, "Warnings:\n", colors['warning'])
            for warn in result["warnings"]:
                self._append_color(cursor, f"  ⚠ {warn}\n", colors['warning'])
            cursor.insertText("\n")
        
        # ========== TCP ==========
        if is_tcp:
            if "transaction_id" in result:
                desc = result.get("transaction_id_desc", "")
                self._append_color(cursor, "Transaction ID: ", colors['default'])
                self._append_color(cursor, f"0x{result['transaction_id']:04X}", colors['transaction'])
                if desc:
                    self._append_color(cursor, f"  [{desc}]", QColor(128, 128, 128))
                cursor.insertText("\n")
                if byte_index < len(hex_bytes):
                    byte_colors[byte_index] = colors['transaction']
                    byte_colors[byte_index+1] = colors['transaction']
                    byte_index += 2
            
            if "protocol_id" in result:
                desc = result.get("protocol_id_desc", "")
                self._append_color(cursor, "Protocol ID: ", colors['default'])
                self._append_color(cursor, f"0x{result['protocol_id']:04X}", colors['protocol'])
                if desc:
                    self._append_color(cursor, f"  [{desc}]", QColor(128, 128, 128))
                cursor.insertText("\n")
                if byte_index < len(hex_bytes):
                    byte_colors[byte_index] = colors['protocol']
                    byte_colors[byte_index+1] = colors['protocol']
                    byte_index += 2
            
            if "length" in result:
                desc = result.get("length_desc", "")
                self._append_color(cursor, "Length: ", colors['default'])
                self._append_color(cursor, f"0x{result['length']:04X} ({result['length']})", colors['length'])
                if desc:
                    self._append_color(cursor, f"  [{desc}]", QColor(128, 128, 128))
                cursor.insertText("\n")
                if byte_index < len(hex_bytes):
                    byte_colors[byte_index] = colors['length']
                    byte_colors[byte_index+1] = colors['length']
                    byte_index += 2
            
            if "unit_id" in result:
                desc = result.get("unit_id_desc", "")
                self._append_color(cursor, "Unit ID: ", colors['default'])
                self._append_color(cursor, f"0x{result['unit_id']:02X} ({result['unit_id']})", colors['unit'])
                if desc:
                    self._append_color(cursor, f"  [{desc}]", QColor(128, 128, 128))
                cursor.insertText("\n")
                if byte_index < len(hex_bytes):
                    byte_colors[byte_index] = colors['unit']
                    byte_index += 1
            
            cursor.insertText("\n")
            self._append_color(cursor, "Frame Details:\n", colors['header'])
        
        # ========== RTU/ASCII ==========
        if is_rtu or is_ascii:
            if "slave_address" in result and result["slave_address"] is not None:
                desc = result.get("slave_address_desc", "")
                self._append_color(cursor, "Slave Address: ", colors['default'])
                self._append_color(cursor, f"0x{result['slave_address']:02X} ({result['slave_address']})", colors['unit'])
                if desc:
                    self._append_color(cursor, f"  [{desc}]", QColor(128, 128, 128))
                cursor.insertText("\n")
                if byte_index < len(hex_bytes):
                    byte_colors[byte_index] = colors['unit']
                    byte_index += 1
            
            cursor.insertText("\n")
            self._append_color(cursor, "Frame Details:\n", colors['header'])
        
        # ========== Function Code ==========
        if "function_code" in result:
            desc = result.get("function_code_desc", "")
            self._append_color(cursor, "  Function Code: ", colors['default'])
            self._append_color(cursor, f"0x{result['function_code']:02X} ", colors['function'])
            self._append_color(cursor, f"({result.get('function_name', 'Unknown')})", colors['function'])
            if desc:
                self._append_color(cursor, f"  [{desc}]", QColor(128, 128, 128))
            cursor.insertText("\n")
            if byte_index < len(hex_bytes):
                byte_colors[byte_index] = colors['function']
                byte_index += 1
        
        # ========== Exception ==========
        if result.get("is_exception"):
            if "original_function_code" in result:
                self._append_color(cursor, "  Original Function: ", colors['default'])
                self._append_color(cursor, f"0x{result['original_function_code']:02X}\n", colors['function'])
            if "exception_code" in result:
                desc = result.get("exception_code_desc", "")
                self._append_color(cursor, "  Exception Code: ", colors['default'])
                self._append_color(cursor, f"0x{result['exception_code']:02X}", QColor(255, 0, 0))
                if desc:
                    self._append_color(cursor, f"  [{desc}]", QColor(128, 128, 128))
                cursor.insertText("\n")
            if "exception_description" in result:
                self._append_color(cursor, "  Exception Description: ", colors['default'])
                self._append_color(cursor, f"{result['exception_description']}\n", QColor(255, 0, 0))
        
        # ========== Start Address ==========
        if "start_address" in result:
            desc = result.get("start_address_desc", "")
            self._append_color(cursor, "  Start Address: ", colors['default'])
            self._append_color(cursor, f"0x{result['start_address']:04X} ({result['start_address']})", colors['address'])
            if desc:
                self._append_color(cursor, f"  [{desc}]", QColor(128, 128, 128))
            cursor.insertText("\n")
            if byte_index < len(hex_bytes):
                byte_colors[byte_index] = colors['address']
                byte_colors[byte_index+1] = colors['address']
                byte_index += 2
        
        # ========== Quantity ==========
        if "quantity" in result:
            desc = result.get("quantity_desc", "")
            self._append_color(cursor, "  Quantity: ", colors['default'])
            self._append_color(cursor, f"0x{result['quantity']:04X} ({result['quantity']})", colors['quantity'])
            if desc:
                self._append_color(cursor, f"  [{desc}]", QColor(128, 128, 128))
            cursor.insertText("\n")
            if byte_index < len(hex_bytes):
                byte_colors[byte_index] = colors['quantity']
                byte_colors[byte_index+1] = colors['quantity']
                byte_index += 2
        
        # ========== Value ==========
        if "value" in result:
            desc = result.get("value_desc", "")
            self._append_color(cursor, "  Value: ", colors['default'])
            self._append_color(cursor, f"0x{result['value']:04X} ({result['value']})", colors['register'])
            if desc:
                self._append_color(cursor, f"  [{desc}]", QColor(128, 128, 128))
            cursor.insertText("\n")
            if byte_index < len(hex_bytes):
                byte_colors[byte_index] = colors['register']
                byte_colors[byte_index+1] = colors['register']
                byte_index += 2
        
        # ========== Byte Count ==========
        if "byte_count" in result:
            desc = result.get("byte_count_desc", "")
            self._append_color(cursor, "  Byte Count: ", colors['default'])
            self._append_color(cursor, f"0x{result['byte_count']:02X} ({result['byte_count']})", colors['byte_count'])
            if desc:
                self._append_color(cursor, f"  [{desc}]", QColor(128, 128, 128))
            cursor.insertText("\n")
            if byte_index < len(hex_bytes):
                byte_colors[byte_index] = colors['byte_count']
                byte_index += 1
        
        # ========== Register Values ==========
        if "registers" in result and result["registers"]:
            desc = result.get("registers_desc", "")
            self._append_color(cursor, "  Register Values:\n", colors['default'])
            if desc:
                self._append_color(cursor, f"    [{desc}]\n", QColor(128, 128, 128))
            for i, val in enumerate(result["registers"]):
                self._append_color(cursor, f"    Register {i+1}: ", colors['default'])
                self._append_color(cursor, f"0x{val:04X} ({val})", colors['register'])
                if byte_index < len(hex_bytes):
                    byte_colors[byte_index] = colors['register']
                    byte_colors[byte_index+1] = colors['register']
                    byte_index += 2
                cursor.insertText("\n")
        
        # ========== CRC ==========
        if "crc_received" in result:
            self._append_color(cursor, "\n  CRC Received: ", colors['default'])
            self._append_color(cursor, f"{result['crc_received']}\n", colors['crc'])
            if byte_index < len(hex_bytes):
                byte_colors[byte_index] = colors['crc']
                byte_colors[byte_index+1] = colors['crc']
                byte_index += 2
            
            self._append_color(cursor, "  CRC Calculated: ", colors['default'])
            crc_calc = result.get('crc_calculated', 'Unknown')
            if crc_calc == "Unknown (Slave ID missing)":
                self._append_color(cursor, f"{crc_calc}\n", QColor(255, 165, 0))
            else:
                self._append_color(cursor, f"{crc_calc}\n", colors['crc'])
            
            self._append_color(cursor, "  CRC Valid: ", colors['default'])
            crc_valid = result.get("crc_valid")
            if crc_valid is True:
                self._append_color(cursor, "Yes\n", QColor(0, 128, 0))
            elif crc_valid is False:
                self._append_color(cursor, "No\n", QColor(255, 0, 0))
            else:
                self._append_color(cursor, "Cannot determine (missing Slave ID)\n", QColor(255, 165, 0))
        
        # ========== LRC ==========
        if "lrc_received" in result:
            self._append_color(cursor, "\n  LRC Received: ", colors['default'])
            self._append_color(cursor, f"{result['lrc_received']}\n", colors['lrc'])
            if byte_index < len(hex_bytes):
                byte_colors[byte_index] = colors['lrc']
                byte_index += 1
            
            self._append_color(cursor, "  LRC Calculated: ", colors['default'])
            self._append_color(cursor, f"{result['lrc_calculated']}\n", colors['lrc'])
            self._append_color(cursor, "  LRC Valid: ", colors['default'])
            color = QColor(0, 128, 0) if result.get("lrc_valid") else QColor(255, 0, 0)
            self._append_color(cursor, "Yes" if result.get("lrc_valid") else "No", color)
        
        cursor.insertText("\n")
        
        # ========== Raw Data с группировкой ==========
        self._append_color(cursor, "Raw Data (HEX):\n", colors['header'])
        
        is_response = self.direction_combo.currentText() == "Response"
        groups = PDUParser.get_display_groups(result, is_tcp, is_response)
        
        if not groups:
            hex_bytes_upper = [b.upper() for b in hex_bytes]
            for i, byte in enumerate(hex_bytes_upper):
                color = byte_colors[i] if i < len(byte_colors) else colors['default']
                self._append_color(cursor, byte, color)
                if i < len(hex_bytes_upper) - 1:
                    cursor.insertText(" ")
            cursor.insertText("\n")
            return
        
        for i, group in enumerate(groups):
            color = colors.get(group.get("color", "default"), colors["default"])
            self._append_color(cursor, group["bytes"], color)
            if i < len(groups) - 1:
                cursor.insertText(" ")
        cursor.insertText("\n")

    def _append_color(self, cursor: QTextCursor, text: str, color: QColor):
        fmt = QTextCharFormat()
        fmt.setForeground(color)
        cursor.insertText(text, fmt)
    
    def on_tab_activated(self):
        QTimer.singleShot(50, self._set_focus)
    
    def _set_focus(self):
        self.input_edit.setFocus()
        self.input_edit.selectAll()