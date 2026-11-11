# tools/check_about_tab.py
# Проверка вкладки "О программе": вкладка существует и показывает версию и номер билда
# Запуск: python tools\check_about_tab.py -> ожидается "ABOUT TAB OK"
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication, QLabel
from version import APP_VERSION, APP_BUILD
from widgets.main_window import MainWindow

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.processEvents()

tab_texts = [window.tab_widget.tabText(i) for i in range(window.tab_widget.count())]
if "О программе" not in tab_texts:
    print("FAIL: вкладка 'О программе' отсутствует")
    sys.exit(1)

widget = window.tab_widget.widget(tab_texts.index("О программе"))
joined = " | ".join(label.text() for label in widget.findChildren(QLabel))
print(f"Содержимое: {joined}")
ok = (APP_VERSION in joined) and (str(APP_BUILD) in joined)
print("ABOUT TAB OK" if ok else "FAIL: версия/билд не найдены в содержимом")
sys.exit(0 if ok else 1)
