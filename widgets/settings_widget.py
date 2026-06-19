# widgets/settings_widget.py
# project_root/widgets/settings_widget.py
# Python 3.11+, PyQt6

from typing import Dict, Optional
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QGroupBox, QScrollArea
from PyQt6.QtCore import pyqtSignal


class SettingsWidget(QWidget):
    settingsChanged = pyqtSignal(dict)
    
    def __init__(self, parent: Optional[QWidget] = None, visible_fields: Optional[Dict[str, bool]] = None) -> None:
        super().__init__(parent)
        
        self.visible_fields: Dict[str, bool] = visible_fields.copy() if visible_fields else {
            "decimal": True,
            "hex_direct": True,
            "bin_direct": True,
            "bin_complement": False,
            "hex_complement": False,
            "ieee_bin": False,
            "ieee_hex": False,
            "unicode_char": False,
            "utf8_char": False,
        }
        
        layout: QVBoxLayout = QVBoxLayout(self)
        
        scroll: QScrollArea = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget: QWidget = QWidget()
        scroll_layout: QVBoxLayout = QVBoxLayout(scroll_widget)
        
        group1: QGroupBox = QGroupBox("Прямые коды")
        group1_layout: QVBoxLayout = QVBoxLayout(group1)
        self.cb_decimal: QCheckBox = QCheckBox("Десятичный код")
        self.cb_hex_direct: QCheckBox = QCheckBox("HEX прямой код")
        self.cb_bin_direct: QCheckBox = QCheckBox("Двоичный прямой код")
        self.cb_decimal.stateChanged.connect(self._on_change)
        self.cb_hex_direct.stateChanged.connect(self._on_change)
        self.cb_bin_direct.stateChanged.connect(self._on_change)
        group1_layout.addWidget(self.cb_decimal)
        group1_layout.addWidget(self.cb_hex_direct)
        group1_layout.addWidget(self.cb_bin_direct)
        scroll_layout.addWidget(group1)
        
        group2: QGroupBox = QGroupBox("Дополнительные коды")
        group2_layout: QVBoxLayout = QVBoxLayout(group2)
        self.cb_bin_complement: QCheckBox = QCheckBox("Двоичный доп. код")
        self.cb_hex_complement: QCheckBox = QCheckBox("HEX доп. код")
        self.cb_bin_complement.stateChanged.connect(self._on_change)
        self.cb_hex_complement.stateChanged.connect(self._on_change)
        group2_layout.addWidget(self.cb_bin_complement)
        group2_layout.addWidget(self.cb_hex_complement)
        scroll_layout.addWidget(group2)
        
        group3: QGroupBox = QGroupBox("IEEE754")
        group3_layout: QVBoxLayout = QVBoxLayout(group3)
        self.cb_ieee_bin: QCheckBox = QCheckBox("IEEE754 двоичный")
        self.cb_ieee_hex: QCheckBox = QCheckBox("IEEE754 HEX")
        self.cb_ieee_bin.stateChanged.connect(self._on_change)
        self.cb_ieee_hex.stateChanged.connect(self._on_change)
        group3_layout.addWidget(self.cb_ieee_bin)
        group3_layout.addWidget(self.cb_ieee_hex)
        scroll_layout.addWidget(group3)
        
        group4: QGroupBox = QGroupBox("Символы")
        group4_layout: QVBoxLayout = QVBoxLayout(group4)
        self.cb_unicode: QCheckBox = QCheckBox("UNICODE символ")
        self.cb_utf8: QCheckBox = QCheckBox("UTF-8 символ")
        self.cb_unicode.stateChanged.connect(self._on_change)
        self.cb_utf8.stateChanged.connect(self._on_change)
        group4_layout.addWidget(self.cb_unicode)
        group4_layout.addWidget(self.cb_utf8)
        scroll_layout.addWidget(group4)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        self._load_settings()
    
    def _on_change(self) -> None:
        self.settingsChanged.emit(self.get_visible_fields())
    
    def _load_settings(self) -> None:
        self.cb_decimal.setChecked(self.visible_fields.get("decimal", True))
        self.cb_hex_direct.setChecked(self.visible_fields.get("hex_direct", True))
        self.cb_bin_direct.setChecked(self.visible_fields.get("bin_direct", True))
        self.cb_bin_complement.setChecked(self.visible_fields.get("bin_complement", False))
        self.cb_hex_complement.setChecked(self.visible_fields.get("hex_complement", False))
        self.cb_ieee_bin.setChecked(self.visible_fields.get("ieee_bin", False))
        self.cb_ieee_hex.setChecked(self.visible_fields.get("ieee_hex", False))
        self.cb_unicode.setChecked(self.visible_fields.get("unicode_char", False))
        self.cb_utf8.setChecked(self.visible_fields.get("utf8_char", False))
    
    def get_visible_fields(self) -> Dict[str, bool]:
        return {
            "decimal": self.cb_decimal.isChecked(),
            "hex_direct": self.cb_hex_direct.isChecked(),
            "bin_direct": self.cb_bin_direct.isChecked(),
            "bin_complement": self.cb_bin_complement.isChecked(),
            "hex_complement": self.cb_hex_complement.isChecked(),
            "ieee_bin": self.cb_ieee_bin.isChecked(),
            "ieee_hex": self.cb_ieee_hex.isChecked(),
            "unicode_char": self.cb_unicode.isChecked(),
            "utf8_char": self.cb_utf8.isChecked(),
        }