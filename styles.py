# styles.py
# project_root/styles.py
# Python 3.11+

# Стили для PyQt6 (опционально, можно закомментировать)
STYLESHEET: str = """
QPlainTextEdit {
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 4px;
    font-family: "Courier New";
    font-size: 10pt;
}
QPlainTextEdit:focus {
    border: 2px solid #4a90e2;
}
QPushButton {
    padding: 4px 12px;
}
"""