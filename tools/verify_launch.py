# verify_launch.py
# Проверка запуска приложения без окна (offscreen).
# Запуск: python tools\verify_launch.py  -> ожидается "APP LAUNCH OK"
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from widgets.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("favicon.ico"))
    window = MainWindow()
    window.show()
    QTimer.singleShot(1500, app.quit)
    app.exec()
    print("APP LAUNCH OK")


if __name__ == "__main__":
    main()
