# validators.py
# project_root/validators.py
# Python 3.11+, PyQt6
# Валидация ввода в полях конвертера. Поле не отклоняет ввод: валидатор
# лишь определяет, валидный ли текст, и если нет — какая это ошибка ввода
# (запрещённый символ или запрещённая последовательность). Ошибка
# показывается в статус-баре, остальные поля обнуляет ConverterWidget.

import re
from typing import Dict, List, Optional


class Validator:
    # Допустимые символы формата: цифры формата + операторы калькулятора
    # (+ - * / ^ ( ) и пробел).
    _allowed: Dict[str, str] = {
        "decimal": "0123456789.,+-*/^() ",
        "bin_direct": "01+-*/^() ",
        "bin_complement": "01+-*/^() ",
        "hex_direct": "0123456789ABCDEFabcdef+-*/^() ",
        "hex_complement": "0123456789ABCDEFabcdef+-*/^() ",
        "ieee_bin": "01+-*/^() ",
        "ieee_hex": "0123456789ABCDEFabcdef+-*/^() ",
    }
    # Символьные поля принимают любой символ (кириллица, эмодзи)
    _CHAR_FORMATS = ("unicode_char", "utf8_char")
    _CONTROL = ("\n", "\t", "\r")

    @classmethod
    def validate(cls, text: str, fmt: str) -> bool:
        """Валидный ли текст (значение или неоконченное выражение)."""
        return cls.input_error(text, fmt) is None

    @classmethod
    def input_error(cls, text: str, fmt: str) -> Optional[str]:
        """Ошибка ввода: запрещённый символ или запрещённая последовательность.

        None — ошибки нет: текст — валидное значение либо неоконченное
        выражение, которое ещё можно дополнить (5+, 10--, 3.) — это процесс
        набора, а не ошибка ввода.
        """
        if not text:
            return None
        if fmt in cls._CHAR_FORMATS:
            if len(text) > 1:
                return "Запрещённая последовательность: в поле символа ожидается один символ"
            if text in cls._CONTROL:
                return "Запрещённый символ: управляющий символ (перенос, табуляция)"
            return None
        allowed: Optional[str] = cls._allowed.get(fmt)
        if allowed is None:
            return None
        for ch in text:
            if ch not in allowed:
                return f"Запрещённый символ: «{ch}»"
        return cls._sequence_error(text, fmt)

    @classmethod
    def _sequence_error(cls, text: str, fmt: str) -> Optional[str]:
        """Запрещённые последовательности в тексте только из допустимых символов.

        Автомат: за значением (числом или группой в скобках) ожидается
        оператор или закрывающая скобка, за оператором — число (со знаком).
        Не более двух знаков + и - подряд без числа: первый — действие,
        второй — знак числа.
        """
        if fmt == "decimal":
            number_re = r"(?:\d+(?:[.,]\d+)?|[.,]\d+)"
        elif fmt in ("hex_direct", "hex_complement", "ieee_hex"):
            number_re = r"[0-9A-Fa-f]+"
        else:  # bin_direct, bin_complement, ieee_bin
            number_re = r"[01]+"
        pattern: "re.Pattern[str]" = re.compile(number_re)

        state: str = "EV"       # ожидается значение (число)
        sign_count: int = 0     # знаков +/− подряд на текущей позиции
        context_start: int = 0  # начало текущего контекста оператор/знак
        group_stack: List[int] = []  # позиции открывающих скобок
        i: int = 0
        n: int = len(text)
        while i < n:
            ch: str = text[i]
            if ch.isspace():
                i += 1
                continue
            m: Optional["re.Match[str]"] = pattern.match(text, i)
            if m is not None:
                if state == "EO":
                    return ("Запрещённая последовательность: числа подряд без "
                            "оператора (пробел не делит число)")
                state = "EO"
                sign_count = 0
                i = m.end()
                continue
            if ch in "+-":
                if state == "EV":
                    if sign_count == 0:
                        context_start = i
                    sign_count += 1
                    if sign_count > 2:
                        run: str = re.sub(r"\s+", "", text[context_start:i + 1])
                        return (f"Запрещённая последовательность: «{run}» — три и более "
                                f"знаков + и - подряд (допустимо: оператор и знак числа)")
                else:  # знак после значения — действие для следующего числа
                    sign_count = 1
                    context_start = i
                    state = "EV"
                i += 1
                continue
            if ch in "*/^":
                if state == "EV":
                    seq: str = re.sub(r"\s+", "", text[context_start:i + 1])
                    return (f"Запрещённая последовательность: «{seq}» — "
                            f"оператор без числа перед ним")
                sign_count = 0
                context_start = i
                state = "EV"
                i += 1
                continue
            if ch == "(":
                if state == "EO":
                    return ("Запрещённая последовательность: открывающая скобка "
                            "сразу после числа или закрывающей скобки — нужен оператор")
                group_stack.append(i)
                state = "EV"
                sign_count = 0
                context_start = i + 1
                i += 1
                continue
            if ch == ")":
                if not group_stack:
                    return "Запрещённая последовательность: лишняя закрывающая скобка без открывающей"
                group_start: int = group_stack.pop()
                if text[group_start + 1:i].strip() == "":
                    return "Запрещённая последовательность: пустые скобки"
                state = "EO"
                sign_count = 0
                i += 1
                continue
            if ch in ".,":
                # Разделитель без цифр. В конце текста — число ещё набирают (3.)
                if text[i + 1:].strip() == "":
                    i += 1
                    continue
                return "Запрещённая последовательность: разделитель . или , без цифр"
            return "Запрещённая последовательность: недопустимые символы в выражении"
        return None