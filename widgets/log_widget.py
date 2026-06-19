# widgets/log_widget.py (исправленный)
# Python 3.11+, PyQt6

import logging
from typing import Optional
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
                             QPushButton, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)

class LogWidget(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.log_file = "modbus_commands.log"
        self._setup_ui()
        self._load_log()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Кнопки управления
        btn_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("Очистить лог")
        self.clear_btn.clicked.connect(self._clear_log)
        btn_layout.addWidget(self.clear_btn)
        
        self.save_btn = QPushButton("Сохранить лог как...")
        self.save_btn.clicked.connect(self._save_log_as)
        btn_layout.addWidget(self.save_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Текстовое поле для лога
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier New", 9))
        layout.addWidget(self.log_text)
    
    def _load_log(self):
        """Загрузка существующего лога из файла"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.log_text.setPlainText(content)
                self._scroll_to_bottom()
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.error(f"Failed to load log: {e}")
    
    def add_entry(self, protocol: str, direction: str, raw_hex: str, result_valid: bool):
        """Добавление записи в лог"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        status = "VALID" if result_valid else "INVALID"
        
        entry = f"[{timestamp}] {protocol} | {direction} | {status} | {raw_hex}\n"
        
        # Добавление в виджет
        self.log_text.append(entry)
        self._scroll_to_bottom()
        
        # Запись в файл
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(entry)
        except Exception as e:
            logger.error(f"Failed to write log: {e}")
    
    def _clear_log(self):
        """Очистка лога"""
        reply = QMessageBox.question(self, "Очистка лога", 
                                     "Удалить все записи из лога?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.log_text.clear()
            try:
                open(self.log_file, 'w', encoding='utf-8').close()
            except Exception as e:
                logger.error(f"Failed to clear log: {e}")
    
    def _save_log_as(self):
        """Сохранение лога в другой файл"""
        filename, _ = QFileDialog.getSaveFileName(self, "Сохранить лог", "", "Log files (*.log);;Text files (*.txt)")
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                QMessageBox.information(self, "Сохранено", f"Лог сохранен в {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")
    
    def _scroll_to_bottom(self):
        """Прокрутка к последней записи"""
        scrollbar = self.log_text.verticalScrollBar()
        if scrollbar is not None:
            scrollbar.setValue(scrollbar.maximum())