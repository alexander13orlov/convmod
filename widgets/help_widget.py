# widgets/help_widget.py (кликабельные ссылки)
# Python 3.11+, PyQt6

from typing import Optional
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser
from PyQt6.QtGui import QFont, QDesktopServices
from PyQt6.QtCore import QUrl

HELP_TEXT = """ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ

==================================================
1. КОНВЕРТЕР
==================================================
- Ввод числа в любом поддерживаемом формате
- Автоматическое преобразование во все остальные форматы
- Подсветка байтов разными цветами (с младшего байта)
- Копирование: Ctrl+C в активном поле
- Вставка: Ctrl+V в активное поле
- Настройка видимости форматов: вкладка "Настройка"

Поддерживаемые форматы:
  • Десятичный код (целые и вещественные числа)
  • HEX прямой код (знак + шестнадцатеричное)
  • HEX дополнительный код
  • Двоичный прямой код (знак + бинарное)
  • Двоичный дополнительный код
  • IEEE754 (binary и hex) - 32-битный single precision
  • Unicode символ (кодовая точка → символ)
  • UTF-8 символ (кодовая точка → UTF-8)

==================================================
2. MODBUS АНАЛИЗАТОР
==================================================
Назначение: разбор Modbus кадров (запросов и ответов)

Порядок работы:
  1. Выбрать протокол (RTU / ASCII / TCP)
  2. Выбрать направление (Request / Response)
  3. Ввести HEX строку (пробелы игнорируются)

Примеры:
  TCP запрос: 03E50000000601030FA00002
  TCP ответ: 03E60000000701030400070003
  RTU запрос: 01030FA00002CRC
  RTU ответ: 01030400070003CRC

Результаты анализа:
  • Номер функции и её название
  • Адрес регистра/катушки
  • Количество регистров
  • Значения данных (для ответов)
  • CRC16 (RTU) / LRC (ASCII) с проверкой
  • MBAP заголовок (TCP)

==================================================
3. ЛОГ
==================================================
- Автоматическое сохранение всех анализируемых Modbus команд
- Файл лога: modbus_commands.log (в папке программы)
- Формат записи: [таймштамп] Протокол | Направление | Статус | HEX
- Кнопка "Очистить лог" - удаление всех записей
- Кнопка "Сохранить лог как..." - экспорт в файл

==================================================
4. НАСТРОЙКИ
==================================================
- Выбор видимых форматов в конвертере
- Настройки сохраняются в файл settings.yaml
- При следующем запуске применяются сохранённые настройки

==================================================
5. ГОРЯЧИЕ КЛАВИШИ
==================================================
Ctrl+C - копирование из активного поля
Ctrl+V - вставка в активное поле

==================================================
ССЫЛКИ
==================================================
<a href="https://ru.wikipedia.org/wiki/IEEE_754">IEEE 754 (Wikipedia)</a>
<a href="https://ru.wikipedia.org/wiki/Дополнительный_код">Дополнительный код (Wikipedia)</a>
<a href="https://ru.wikipedia.org/wiki/UTF-8">UTF-8 (Wikipedia)</a>
<a href="https://symbl.cc/ru/unicode-table/">Unicode таблица (symbl.cc)</a>
<a href="https://ru.wikipedia.org/wiki/Modbus">Modbus (Wikipedia)</a>
"""


class HelpWidget(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.text_browser: QTextBrowser = QTextBrowser()
        self.text_browser.setHtml(HELP_TEXT.replace('\n', '<br>'))
        self.text_browser.setOpenExternalLinks(True)
        self.text_browser.setFont(QFont("Courier New", 10))
        self.text_browser.anchorClicked.connect(self._link_clicked)
        layout.addWidget(self.text_browser)
    
    def _link_clicked(self, url: QUrl) -> None:
        """Открытие ссылки в браузере по умолчанию"""
        QDesktopServices.openUrl(url)