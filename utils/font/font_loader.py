# utils/font/font_loader.py
# Python 3.11+, PyQt6

import os
import logging
from typing import Optional
from PyQt6.QtGui import QFontDatabase, QFont

logger = logging.getLogger(__name__)

# Путь к папке со шрифтами относительно корня проекта
FONT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "utils", "font", "hack")

def load_hack_font() -> bool:
    """Загружает шрифт Hack из папки проекта в QFontDatabase.
    Возвращает True если загрузка успешна."""
    hack_ttf = os.path.join(FONT_PATH, "Hack-Regular.ttf")
    if os.path.exists(hack_ttf):
        try:
            font_id = QFontDatabase.addApplicationFont(hack_ttf)
            if font_id != -1:
                families = QFontDatabase.applicationFontFamilies(font_id)
                if families and families[0] == "Hack":
                    logger.info("Hack font loaded from project resources")
                    return True
            else:
                logger.warning(f"Failed to load Hack font from {hack_ttf}")
        except Exception as e:
            logger.warning(f"Error loading Hack font: {e}")
    else:
        logger.debug(f"Hack font file not found: {hack_ttf}")
    return False

def get_mono_font(size: int = 10) -> QFont:
    """
    Возвращает шрифт Hack если он доступен (из проекта или системы),
    иначе Courier New.
    """
    # Проверяем, загружен ли шрифт из проекта
    if "Hack" in QFontDatabase.families():
        return QFont("Hack", size)
    
    # Пытаемся загрузить из проекта
    if load_hack_font():
        return QFont("Hack", size)
    
    # Проверяем системный шрифт
    if "Hack" in QFontDatabase.families():
        return QFont("Hack", size)
    
    # Шрифт по умолчанию
    logger.debug("Hack font not found, using Courier New")
    return QFont("Courier New", size)