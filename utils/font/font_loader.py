# utils/font/font_loader.py
# Python 3.11+, PyQt6

import os
import sys
import logging
from typing import Optional
from PyQt6.QtGui import QFontDatabase, QFont

logger = logging.getLogger(__name__)


def _hack_dir() -> str:
    """Путь к папке со шрифтами: в dev — рядом с файлом, в EXE — из sys._MEIPASS."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass is not None:
        candidate = os.path.join(meipass, "utils", "font", "hack")
        if os.path.isdir(candidate):
            return candidate
    candidate = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hack")
    if os.path.isdir(candidate):
        return candidate
    if meipass is not None:
        return os.path.join(meipass, "utils", "font", "hack")
    return candidate


# Путь к папке со шрифтами (dev: рядом с файлом; EXE: из sys._MEIPASS)
FONT_PATH = _hack_dir()

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


_fallback_warmed: bool = False


def warmup_font_fallback() -> None:
    """Одноразовый прогрев механизма fallback-шрифтов Qt/Windows.

    Первая отрисовка глифа, которого нет в шрифте (например CJK-символ
    в поле "UNICODE символ"), стоит ~0.7 c: система ищет резервный шрифт.
    Рисуем такие символы в невидимый QPixmap при запуске, чтобы разовая
    стоимость упала до первого ввода пользователя.
    """
    global _fallback_warmed
    if _fallback_warmed:
        return
    _fallback_warmed = True
    try:
        from PyQt6.QtGui import QPixmap, QPainter
        pm = QPixmap(64, 16)
        pm.fill()
        p = QPainter(pm)
        p.setFont(get_mono_font(10))
        # Символы вне покрытия Hack: CJK, хангыль, эмодзи
        p.drawText(0, 12, "\u3039\uAC00\U0001F514")
        p.end()
    except Exception:
        _fallback_warmed = False
        logger.debug("Прогрев fallback-шрифтов не выполнен", exc_info=True)