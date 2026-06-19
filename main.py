import sys
import ctypes
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from widgets.main_window import MainWindow

# Устанавливаем уникальный AppUserModelID для Windows (до создания QApplication)
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("company.converter.numconverter.v1")
except AttributeError:
    # Не Windows — игнорируем
    pass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def main() -> None:
    app = QApplication(sys.argv)
    
    # Устанавливаем иконку приложения (для заголовка окна)
    app.setWindowIcon(QIcon("favicon.ico"))
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()