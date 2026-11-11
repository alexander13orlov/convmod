# tools/check_converter_layout.py
# Проверка вкладки Конвертер: подпись смещена вправо (indent = 4 px),
# левый край поля подтянут к подписям (фикс. ширина подписи 146 px),
# текст самой длинной подписи не обрезается,
# зазор от конца самой длинной подписи до левого края поля = 8 px.
# Запуск: python tools\check_converter_layout.py -> ожидается "LAYOUT OK"
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication
from widgets.main_window import MainWindow

LABEL_WIDTH = 146
LABEL_INDENT = 4
GAP_EXPECTED = 8


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    QTimer.singleShot(300, app.quit)
    app.exec()

    cw = window.tab_widget.widget(0)
    problems: list[str] = []
    longest_ftype = ""
    longest_w = 0
    for ftype, field in cw.fields.items():
        width = field.label.width()
        indent = field.label.indent()
        text_w = field.label.fontMetrics().horizontalAdvance(field.label.text())
        if width != LABEL_WIDTH:
            problems.append(f"{ftype}: width={width} (ожидается {LABEL_WIDTH})")
        if indent != LABEL_INDENT:
            problems.append(f"{ftype}: indent={indent} (ожидается {LABEL_INDENT})")
        if text_w + indent > LABEL_WIDTH:
            problems.append(f"{ftype}: текст {text_w} + indent {indent} не помещается в {LABEL_WIDTH}")
        if text_w > longest_w:
            longest_ftype, longest_w = ftype, text_w

    longest = cw.fields[longest_ftype]
    gap = longest.text_edit.pos().x() - (longest.label.pos().x() + longest.label.indent() + longest_w)
    if gap != GAP_EXPECTED:
        problems.append(f"{longest_ftype}: зазор до поля {gap} (ожидается {GAP_EXPECTED})")

    if problems:
        for p in problems:
            print("FAIL:", p)
        sys.exit(1)
    print("LAYOUT OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
