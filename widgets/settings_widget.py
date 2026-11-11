# widgets/settings_widget.py
# project_root/widgets/settings_widget.py
# Python 3.11+, PyQt6

from typing import Dict, List, Optional, Tuple
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QGroupBox, QScrollArea
from PyQt6.QtCore import pyqtSignal
from config_manager import DEFAULT_VISIBLE_FIELDS

# Структура групп: название группы -> [(ключ поля, подпись чекбокса), ...]
FIELD_GROUPS: List[Tuple[str, List[Tuple[str, str]]]] = [
    ("Прямые коды", [
        ("decimal", "Десятичный код"),
        ("hex_direct", "HEX прямой код"),
        ("bin_direct", "Двоичный прямой код"),
    ]),
    ("Дополнительные коды", [
        ("bin_complement", "Двоичный доп. код"),
        ("hex_complement", "HEX доп. код"),
    ]),
    ("IEEE754", [
        ("ieee_bin", "IEEE754 двоичный"),
        ("ieee_hex", "IEEE754 HEX"),
    ]),
    ("Символы", [
        ("unicode_char", "UNICODE символ"),
        ("utf8_char", "UTF-8 символ"),
    ]),
]


class SettingsWidget(QWidget):
    settingsChanged = pyqtSignal(dict)
    
    def __init__(self, parent: Optional[QWidget] = None, visible_fields: Optional[Dict[str, bool]] = None) -> None:
        super().__init__(parent)
        
        self.visible_fields: Dict[str, bool] = (
            visible_fields.copy() if visible_fields else dict(DEFAULT_VISIBLE_FIELDS)
        )
        
        layout: QVBoxLayout = QVBoxLayout(self)
        
        scroll: QScrollArea = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget: QWidget = QWidget()
        scroll_layout: QVBoxLayout = QVBoxLayout(scroll_widget)
        
        self.boxes: Dict[str, QCheckBox] = {}
        for group_title, fields in FIELD_GROUPS:
            group: QGroupBox = QGroupBox(group_title)
            group_layout: QVBoxLayout = QVBoxLayout(group)
            for key, label in fields:
                box: QCheckBox = QCheckBox(label)
                box.stateChanged.connect(self._on_change)
                group_layout.addWidget(box)
                self.boxes[key] = box
            scroll_layout.addWidget(group)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        self._load_settings()
    
    def _on_change(self) -> None:
        self.settingsChanged.emit(self.get_visible_fields())
    
    def _load_settings(self) -> None:
        for key, box in self.boxes.items():
            box.setChecked(self.visible_fields.get(key, DEFAULT_VISIBLE_FIELDS.get(key, False)))
    
    def get_visible_fields(self) -> Dict[str, bool]:
        return {key: box.isChecked() for key, box in self.boxes.items()}