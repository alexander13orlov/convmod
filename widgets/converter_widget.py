# widgets/converter_widget.py
# project_root/widgets/converter_widget.py
# Python 3.11+, PyQt6

import math
import logging
from typing import Optional, Dict, Any, Callable
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPalette, QColor, QFocusEvent
from PyQt6.QtCore import Qt, QTimer, QEvent
from converters import Converter
from widgets.base_field import NumberField
from widgets.byte_field import ByteGroupField

logger = logging.getLogger(__name__)


class ConverterWidget(QWidget):
    def __init__(self, parent: Optional[QWidget] = None, status_callback: Optional[Callable[[], None]] = None, focus_callback: Optional[Callable[[], None]] = None) -> None:
        super().__init__(parent)
        self.fields: Dict[str, NumberField] = {}
        self.active_source: Optional[NumberField] = None
        self.updating: bool = False
        self.nb_display: QLabel = QLabel("0")
        self.converter: Converter = Converter()
        self.status_callback = status_callback
        self.focus_callback = focus_callback
        self.parent_window: Optional[Any] = parent
        self.visible_fields: Dict[str, bool] = {
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
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        self.main_layout: QVBoxLayout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.fields_layout: QVBoxLayout = QVBoxLayout()
        self.fields_layout.setContentsMargins(0, 0, 0, 0)
        self.fields_layout.setSpacing(2)
        self.main_layout.addLayout(self.fields_layout)
        self.main_layout.addStretch()
        QTimer.singleShot(10, self._build_fields)
    
    def _build_fields(self) -> None:
        active_format = None
        active_text = None
        if self.active_source is not None:
            active_format = self.active_source.format_type
            active_text = self.active_source.get_raw_value()
        
        for key in list(self.fields.keys()):
            widget = self.fields.get(key)
            if widget is not None:
                widget.deleteLater()
        self.fields.clear()
        
        while self.fields_layout.count():
            item = self.fields_layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
        
        fields_order = [
            ("Десятичный код:", "decimal"),
            ("HEX прямой код:", "hex_direct"),
            ("Двоичный прямой код:", "bin_direct"),
            ("Двоичный доп. код:", "bin_complement"),
            ("HEX доп. код:", "hex_complement"),
            ("IEEE754 двоичный:", "ieee_bin"),
            ("IEEE754 HEX:", "ieee_hex"),
            ("UNICODE символ:", "unicode_char"),
            ("UTF-8 символ:", "utf8_char"),
        ]
        
        visible_count = 0
        field_height = 40
        for label, ftype in fields_order:
            if not self.visible_fields.get(ftype, False):
                continue
            visible_count += 1
            is_long: bool = ftype in ["bin_direct", "bin_complement", "hex_direct", "hex_complement", "ieee_bin", "ieee_hex"]
            if ftype in ["hex_direct", "hex_complement", "ieee_hex", "bin_direct", "bin_complement", "ieee_bin"]:
                field: NumberField = ByteGroupField(label, ftype, is_long)
            else:
                field = NumberField(label, ftype, is_long)
            field.changed.connect(self._on_field_changed)
            field.text_edit.selectionChanged.connect(self._on_selection_or_focus)
            field.text_edit.textChanged.connect(self._on_selection_or_focus)
            field.text_edit.installEventFilter(self)
            self.fields_layout.addWidget(field)
            self.fields[ftype] = field
            field_height = max(field_height, field.minimumSizeHint().height())
        
        if active_format is not None and active_format in self.fields:
            self.active_source = self.fields[active_format]
            if active_text is not None:
                self.active_source.set_value_silent(active_text)
            QTimer.singleShot(50, lambda: self._set_focus_to_field(self.active_source))
        else:
            decimal_field = self.fields.get("decimal")
            if decimal_field is not None:
                self.active_source = decimal_field
                QTimer.singleShot(50, lambda: self._set_focus_to_field(decimal_field))
            else:
                self.active_source = None
        
        self._update_source_highlight()
        
        if self.parent_window and hasattr(self.parent_window, 'resize_to_fit'):
            self.parent_window.resize_to_fit(visible_count, field_height)
    
    def _set_focus_to_field(self, field: Optional[NumberField]) -> None:
        if field is not None:
            field.text_edit.setFocus()
            cursor = field.text_edit.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            field.text_edit.setTextCursor(cursor)
            if self.active_source != field:
                self.active_source = field
                self._update_source_highlight()
    
    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.Type.FocusIn:
            for ftype, field in self.fields.items():
                if field is not None and field.text_edit is obj:
                    if self.active_source != field:
                        self.active_source = field
                        self._update_source_highlight()
                    if self.focus_callback:
                        self.focus_callback()
                    break
        return super().eventFilter(obj, event)
    
    def _on_selection_or_focus(self) -> None:
        if self.focus_callback:
            self.focus_callback()
    
    def update_visible_fields(self, visible: Dict[str, bool]) -> None:
        self.visible_fields = visible.copy()
        self._build_fields()
    
    def _get_nb_for_conversion(self, target_fmt: str) -> int:
        if target_fmt in ['ieee_bin', 'ieee_hex']:
            return 4  # 4 байта = 32 бита (single precision)
        elif target_fmt in ['bin_complement', 'hex_complement']:
            return 0
        elif target_fmt in ['bin_direct', 'hex_direct']:
            return 0
        else:
            return 8
    
    def _update_nb_display(self, value_str: str, format_type: str) -> None:
        try:
            if not value_str or value_str.strip() == "":
                self.nb_display.setText("0")
                return
                
            if format_type == "decimal":
                if '.' in value_str:
                    num = float(value_str)
                    if -3.4e38 <= num <= 3.4e38:
                        self.nb_display.setText("4")
                    else:
                        self.nb_display.setText("8")
                    return
                else:
                    num = int(value_str)
                    if num == 0:
                        self.nb_display.setText("1")
                        return
                    bits: int = num.bit_length() + (1 if num < 0 else 0)
                    bytes_count: float = bits / 8
                    rounded_bytes: int = math.ceil(bytes_count)
                    self.nb_display.setText(str(max(1, rounded_bytes)))
                    
            elif format_type in ["bin_direct", "bin_complement", "ieee_bin"]:
                clean: str = value_str.replace(" ", "")
                if clean:
                    bytes_count: float = len(clean) / 8
                    rounded_bytes: int = math.ceil(bytes_count)
                    self.nb_display.setText(str(rounded_bytes) if rounded_bytes > 0 else "0")
                else:
                    self.nb_display.setText("0")
                    
            elif format_type in ["hex_direct", "hex_complement", "ieee_hex"]:
                clean = value_str.replace(" ", "")
                if clean:
                    bytes_count: float = len(clean) / 2
                    rounded_bytes: int = math.ceil(bytes_count)
                    self.nb_display.setText(str(rounded_bytes) if rounded_bytes > 0 else "0")
                else:
                    self.nb_display.setText("0")
                    
            elif format_type in ["unicode_char", "utf8_char"]:
                if value_str:
                    self.nb_display.setText("4")
                else:
                    self.nb_display.setText("0")
            else:
                self.nb_display.setText("0")
        except Exception:
            self.nb_display.setText("0")
   

    def _on_field_changed(self, text: str, source: NumberField) -> None:
        if self.updating:
            return
        
        if not source.text_edit.hasFocus():
            logger.debug(f"[Converter] _on_field_changed: IGNORE (no focus), source={source.format_type}")
            return
        
        self.updating = True
        
        if self.active_source != source:
            logger.debug(f"[Converter] _on_field_changed: active source changed to {source.format_type}")
            self.active_source = source
            self._update_source_highlight()
        
        self._update_nb_display(text, source.format_type)
        
        if self.status_callback:
            self.status_callback()
        
        if not text or text.strip() == "":
            for ftype, widget in self.fields.items():
                if widget is not None and widget != self.active_source:
                    widget.set_value_silent("")
            self.updating = False
            self._update_source_highlight()
            return
        
        # Определяем правильный nb для источника
        if source.format_type in ['ieee_bin', 'ieee_hex']:
            nb = 4
        else:
            nb = 8
        
        num_value = self.converter.parse(text, source.format_type, nb)
        logger.debug(f"[Converter] parse: source={source.format_type}, nb={nb}, num_value={num_value}")
        
        if num_value is not None:
            for ftype, widget in self.fields.items():
                if widget is None or widget == self.active_source:
                    continue
                nb_for_convert = self._get_nb_for_conversion(ftype)
                converted = self.converter.convert(num_value, ftype, nb_for_convert)
                if converted is not None:
                    widget.set_value_silent(converted)
                else:
                    widget.set_value_silent("")
        else:
            logger.debug(f"[Converter] num_value is None, clearing other fields")
            for ftype, widget in self.fields.items():
                if widget is not None and widget != self.active_source:
                    widget.set_value_silent("")
        
        self.updating = False
        self._update_source_highlight()
  
  
    
    def _update_source_highlight(self) -> None:
        for widget in self.fields.values():
            if widget is not None:
                palette: QPalette = widget.palette()
                palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
                widget.setPalette(palette)
        
        if self.active_source is not None:
            try:
                palette = self.active_source.palette()
                palette.setColor(QPalette.ColorRole.Base, QColor(200, 230, 255))
                self.active_source.setPalette(palette)
            except RuntimeError:
                self.active_source = None
    
    def reset_fields(self) -> None:
        for widget in self.fields.values():
            if widget is not None:
                widget.set_value_silent("")
        self.active_source = None
        self.nb_display.setText("0")
        self._update_source_highlight()
        
        decimal_field = self.fields.get("decimal")
        if decimal_field is not None:
            self.active_source = decimal_field
            QTimer.singleShot(50, lambda: self._set_focus_to_field(decimal_field))
            self._update_source_highlight()
        
        if self.status_callback:
            self.status_callback()
    
    def get_active_field(self) -> Optional[NumberField]:
        if self.active_source is not None:
            try:
                _ = self.active_source.format_type
                return self.active_source
            except RuntimeError:
                self.active_source = None
        return None
    
    def get_active_field_text(self) -> str:
        active = self.get_active_field()
        if active is not None:
            return active.get_raw_value()
        return ""
    
    def get_active_field_format(self) -> str:
        active = self.get_active_field()
        if active is not None:
            return active.format_type
        return ""