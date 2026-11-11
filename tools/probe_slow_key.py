# probe_slow_key.py
# Точечный замер пайплайна для значения 12345 (пятая цифра первого набора):
# чистая конвертация vs set_value_silent по каждому полю.
# Запуск: .venv\Scripts\python.exe tools\probe_slow_key.py
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication
from widgets.main_window import MainWindow
from converters import Converter


def pump(app, timeout_ms):
    deadline = time.perf_counter() + timeout_ms / 1000
    while time.perf_counter() < deadline:
        app.processEvents()
        time.sleep(0.001)


def nb_for(fmt):
    if fmt in ('ieee_bin', 'ieee_hex'):
        return 4
    if fmt in ('bin_complement', 'hex_complement', 'bin_direct', 'hex_direct'):
        return 0
    return 8


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    pump(app, 500)
    time.sleep(0.3)
    pump(app, 200)

    decimal = window.converter_widget.fields["decimal"]
    decimal.text_edit.setFocus()
    pump(app, 200)

    # Четыре цифры — как набирает пользователь
    for ch in "1234":
        decimal.text_edit.insertPlainText(ch)
        pump(app, 120)

    val = 12345
    conv = Converter()
    widget = window.converter_widget

    print("== чистая convert (без Qt) ==", flush=True)
    for ftype in [f for f in widget.fields if f != "decimal"]:
        t0 = time.perf_counter()
        r = conv.convert(val, ftype, nb_for(ftype))
        t1 = time.perf_counter()
        print(f"  {ftype:16s} {r!r:24s} {(t1 - t0) * 1000:7.1f} ms", flush=True)

    print("== set_value_silent (Qt, по полям) ==", flush=True)
    for ftype, field in widget.fields.items():
        if ftype == "decimal":
            continue
        r = conv.convert(val, ftype, nb_for(ftype))
        t0 = time.perf_counter()
        field.set_value_silent(r if r is not None else "")
        t1 = time.perf_counter()
        print(f"  {ftype:16s} {r!r:24s} {(t1 - t0) * 1000:7.1f} ms", flush=True)

    # Повторно в unicode-поле: второй раз должно быть быстро
    uni = widget.fields["unicode_char"]
    t0 = time.perf_counter()
    uni.set_value_silent(chr(12345))
    t1 = time.perf_counter()
    print(f"  unicode_repeat   {chr(12345)!r:24s} {(t1 - t0) * 1000:7.1f} ms", flush=True)

    # Другой скрипт (хангыль) — сколько стоит следующий fallback
    t0 = time.perf_counter()
    uni.set_value_silent(chr(0xAC00))
    t1 = time.perf_counter()
    print(f"  unicode_hangul   '가' {(t1 - t0) * 1000:7.1f} ms", flush=True)

    QTimer.singleShot(200, app.quit)
    app.exec()
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
