# main.py
import sys
import os
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from widgets.main_window import MainWindow

# Устанавливаем уникальный AppUserModelID для Windows
try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("company.converter.convmod.v1")
except AttributeError:
    pass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def main() -> None:
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("favicon.ico"))
    
    window = MainWindow()
    
    # Получаем полный путь к исполняемому файлу
    exe_path = QApplication.applicationFilePath()
    
    # Устанавливаем заголовок с полным путем
    window.setWindowTitle(f"ConvMod - {exe_path}")
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()