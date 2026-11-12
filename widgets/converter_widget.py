# widgets/converter_widget.py
# project_root/widgets/converter_widget.py
# Python 3.11+, PyQt6

import math
import logging
from typing import Optional, Dict, Any, Callable
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPalette, QColor, QFocusEvent
from PyQt6.QtCore import Qt, QTimer, QEvent
import math_eval
from converters import Converter
from config_manager import DEFAULT_VISIBLE_FIELDS
from widgets.base_field import NumberField
from widgets.byte_field import ByteGroupField

logger = logging.getLogger(__name__)


class ConverterWidget(QWidget):
    # Форматы с подсветкой байтов (длинные поля, ByteGroupField)
    GROUP_FORMATS = ("bin_direct", "bin_complement", "hex_direct", "hex_complement", "ieee_bin", "ieee_hex")
    # Сколько подсказка о раскладке показывается в статус-баре
    HINT_TIMEOUT_MS = 4000

    def __init__(self, parent: Optional[QWidget] = None, status_callback: Optional[Callable[[], None]] = None, focus_callback: Optional[Callable[[Optional[str]], None]] = None, log_callback: Optional[Callable[[str, str, str], None]] = None) -> None:
        super().__init__(parent)
        self.fields: Dict[str, NumberField] = {}
        self.active_source: Optional[NumberField] = None
        self.updating: bool = False
        self.nb_display: QLabel = QLabel("0")
        self.converter: Converter = Converter()
        self.status_callback = status_callback
        self.focus_callback = focus_callback
        self.log_callback: Optional[Callable[[str, str, str], None]] = log_callback
        self.parent_window: Optional[Any] = parent
        self.visible_fields: Dict[str, bool] = dict(DEFAULT_VISIBLE_FIELDS)
        self._hint: Optional[str] = None
        self._hint_timer: QTimer = QTimer(self)
        self._hint_timer.setSingleShot(True)
        self._hint_timer.timeout.connect(self._clear_hint)
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
            is_long: bool = ftype in self.GROUP_FORMATS
            if is_long:
                field: NumberField = ByteGroupField(label, ftype, is_long)
            else:
                field = NumberField(label, ftype, is_long)
            field.changed.connect(self._on_field_changed)
            field.changed.connect(self._on_valid_edit)
            field.layout_hint.connect(self._on_layout_hint)
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
                # Пересборка не должна терять значения: повторяем конвертацию из источника
                self._convert_from_source(active_text, self.active_source)
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
            try:
                field.text_edit.setFocus()
                cursor = field.text_edit.textCursor()
                cursor.movePosition(cursor.MoveOperation.End)
                field.text_edit.setTextCursor(cursor)
                if self.active_source != field:
                    self.active_source = field
                    self._update_source_highlight()
            except RuntimeError:
                # Поле уже удалено (пересборка) — таймер устарел, игнорируем
                pass
    
    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.Type.FocusIn:
            for ftype, field in self.fields.items():
                if field is not None and field.text_edit is obj:
                    if self.active_source != field:
                        self.active_source = field
                        self._update_source_highlight()
                    if self.focus_callback:
                        self.focus_callback(self._hint)
                    break
            return super().eventFilter(obj, event)
        if (event.type() == QEvent.Type.KeyPress
                and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)):
            for ftype, field in self.fields.items():
                if field is not None and field.text_edit is obj:
                    if ftype in Converter._EXPR_FORMATS:
                        self._on_enter_pressed(field)
                        return True
                    break
        return super().eventFilter(obj, event)
    
    def _on_selection_or_focus(self) -> None:
        self._notify_status()

    def _on_layout_hint(self, message: str) -> None:
        self._hint = message
        self._hint_timer.start(self.HINT_TIMEOUT_MS)
        self._notify_status()

    def _on_valid_edit(self, text: str, source: NumberField) -> None:
        # Произошла валидная правка — подсказка о раскладке больше не нужна
        self._clear_hint()

    def _on_enter_pressed(self, source: NumberField) -> None:
        """Enter в поле с выражением: замена на результат + запись в лог."""
        text: str = source.get_raw_value()
        fmt: str = source.format_type
        if not text or not math_eval.is_expression(text):
            return
        nb: int = 4 if fmt in ('ieee_bin', 'ieee_hex') else 8
        value = self.converter.parse(text, fmt, nb)
        if value is None:
            return
        result_text: Optional[str] = self.converter.convert(
            value, fmt, self._get_nb_for_conversion(fmt))
        if result_text is None or result_text == text:
            return
        source.set_value_silent(result_text)
        self._convert_from_source(result_text, source)
        if self.log_callback is not None:
            self.log_callback(text, result_text, fmt)

    def _clear_hint(self) -> None:
        if self._hint is None:
            return
        self._hint = None
        self._hint_timer.stop()
        self._notify_status()

    def _notify_status(self) -> None:
        if self.focus_callback:
            self.focus_callback(self._hint)
    
    def update_visible_fields(self, visible: Dict[str, bool]) -> None:
        self.visible_fields = visible.copy()
        if self.fields:
            self._build_fields()
    
    def _get_nb_for_conversion(self, target_fmt: str) -> int:
        if target_fmt in ('ieee_bin', 'ieee_hex'):
            return 4  # 4 байта = 32 бита (single precision)
        if target_fmt in ('bin_complement', 'hex_complement', 'bin_direct', 'hex_direct'):
            return 0  # ширина в байтах для этих форматов не используется
        return 8
    
    def _set_nb_from_chars(self, value_str: str, chars_per_byte: int) -> None:
        """nb по количеству символов: целые байты с округлением вверх."""
        clean: str = value_str.replace(" ", "")
        if clean:
            self.nb_display.setText(str(max(1, math.ceil(len(clean) / chars_per_byte))))
        else:
            self.nb_display.setText("0")

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
                self._set_nb_from_chars(value_str, 8)

            elif format_type in ["hex_direct", "hex_complement", "ieee_hex"]:
                self._set_nb_from_chars(value_str, 2)
                    
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
        
        if self.active_source != source:
            logger.debug(f"[Converter] _on_field_changed: active source changed to {source.format_type}")
            self.active_source = source
            self._update_source_highlight()
        
        self._convert_from_source(text, source)

    def _convert_from_source(self, text: str, source: NumberField) -> None:
        """Конвертация значения источника во все остальные поля (без проверки фокуса)."""
        self.updating = True
        
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
        self._clear_hint()
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