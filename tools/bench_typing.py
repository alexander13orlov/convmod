# bench_typing.py
# Замер времени обработки каждой клавиши в поле "Десятичный код":
# первый набор (сразу после запуска) vs повторный после очистки.
# Запуск: .venv\Scripts\python.exe tools\bench_typing.py
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication
from widgets.main_window import MainWindow

TYPED = "12345678"
PUMP_MS = 120  # как долго качаем события после клавиши (layout/paint/таймеры)


def pump(app, timeout_ms):
    """Прокачка событий, пока идёт отложенная работа Qt (layout, paint)."""
    deadline = time.perf_counter() + timeout_ms / 1000
    while time.perf_counter() < deadline:
        app.processEvents()
        time.sleep(0.001)


def type_phase(app, decimal, label):
    print(f"--- {label} ---", flush=True)
    max_handler_ms = 0.0
    for ch in TYPED:
        t0 = time.perf_counter()
        decimal.text_edit.insertPlainText(ch)  # синхронно: textChanged -> обработчики
        t1 = time.perf_counter()
        pump(app, PUMP_MS)
        t2 = time.perf_counter()
        max_handler_ms = max(max_handler_ms, 1000 * (t1 - t0))
        print(f"  '{ch}' handler={1000 * (t1 - t0):7.1f} ms  pump>={1000 * (t2 - t1):7.1f} ms", flush=True)
    return max_handler_ms


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    # Ждём завершения стартовых таймеров (10/50/60/100 мс) — как в реальном запуске
    pump(app, 500)
    time.sleep(0.5)
    pump(app, 200)

    visible = [f for f, v in window.converter_widget.visible_fields.items() if v]
    print(f"видимых полей: {len(visible)}: {visible}", flush=True)

    decimal = window.converter_widget.fields["decimal"]
    decimal.text_edit.setFocus()
    pump(app, 200)
    print(f"фокус в decimal: {decimal.text_edit.hasFocus()}", flush=True)

    first_max = type_phase(app, decimal, "ПЕРВЫЙ набор")

    decimal.text_edit.clear()
    pump(app, 300)

    type_phase(app, decimal, "ВТОРОЙ набор (после очистки)")

    LIMIT_MS = 100
    if first_max < LIMIT_MS:
        print(f"ИТОГ: подвисание при первом наборе отсутствует (макс. {first_max:.1f} ms < {LIMIT_MS} ms) — PASS", flush=True)
    else:
        print(f"ИТОГ: ОБНАРУЖЕНО подвисание при первом наборе (макс. {first_max:.1f} ms >= {LIMIT_MS} ms) — FAIL", flush=True)

    QTimer.singleShot(300, app.quit)
    app.exec()
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
