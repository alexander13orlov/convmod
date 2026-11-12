# math_eval.py
# project_root/math_eval.py
# Python 3.11+
# Калькулятор в полях конвертера: арифметические выражения.
# Поддерживаются +, -, *, /, степень ^ (правая ассоциативность),
# скобки, унарный знак. Числа — в системе счисления поля.

import math
import re
from typing import List, Optional, Tuple, Union

# Форматы, в которых поддерживаются выражения
EXPR_FORMATS = (
    'decimal', 'hex_direct', 'hex_complement',
    'bin_direct', 'bin_complement', 'ieee_bin', 'ieee_hex',
)

# Ограничение размера целого результата (в битах): защита от 9^9^9
_MAX_INT_BITS = 4096


def is_expression(text: str) -> bool:
    """Есть ли в тексте оператор (а не просто число со знаком)."""
    t: str = text.strip()
    for i, ch in enumerate(t):
        if ch in '*/^()+' or (ch == '-' and i > 0):
            return True
    return False


def _base(fmt: str) -> int:
    if fmt == 'decimal':
        return 10
    if fmt in ('hex_direct', 'hex_complement', 'ieee_hex'):
        return 16
    return 2


def _digit_pattern(fmt: str) -> str:
    if fmt == 'decimal':
        return r'\d+(?:[.,]\d+)?'
    if _base(fmt) == 16:
        return r'[0-9A-Fa-f]+'
    return r'[01]+'


def _tokenize(text: str, fmt: str) -> Optional[List[Tuple[str, str]]]:
    """Токены: ('num', текст) и односимвольные операторы.
    None — встретился недопустимый символ."""
    if fmt == 'decimal':
        text = text.replace(',', '.')
    pattern: "re.Pattern[str]" = re.compile(_digit_pattern(fmt))
    tokens: List[Tuple[str, str]] = []
    i: int = 0
    n: int = len(text)
    sign_run: int = 0
    while i < n:
        ch: str = text[i]
        if ch.isspace():
            i += 1
            continue
        m: Optional["re.Match[str]"] = pattern.match(text, i)
        if m is not None:
            tokens.append(('num', m.group(0)))
            sign_run = 0
            i = m.end()
            continue
        if ch in '+-*/^()':
            # Не более двух знаков +/− подряд без числа: первый знак —
            # действие, второй — знак числа; другие операторы обрывают цепочку
            if ch in '+-':
                sign_run += 1
                if sign_run > 2:
                    return None
            else:
                sign_run = 0
            tokens.append((ch, ch))
            i += 1
            continue
        return None
    return tokens


def _int_size_ok(value: int) -> bool:
    return abs(value).bit_length() <= _MAX_INT_BITS


def _to_float(value: Union[int, float]) -> Optional[float]:
    try:
        result: float = float(value)
    except OverflowError:
        return None
    return result if math.isfinite(result) else None


def _power(base: Union[int, float], exp: Union[int, float]) -> Optional[Union[int, float]]:
    if isinstance(base, float) or isinstance(exp, float):
        try:
            result: float = float(base) ** float(exp)
        except (OverflowError, ValueError, ZeroDivisionError):
            return None
        return result if math.isfinite(result) else None
    if exp < 0:
        try:
            result = float(base) ** exp
        except (OverflowError, ValueError, ZeroDivisionError):
            return None
        return result if math.isfinite(result) else None
    if base in (1, -1):
        return 1 if exp % 2 == 0 else base
    if base == 0:
        return 0
    # Оценка размера ДО вычисления: 9**387420489 считать не пытаемся
    est_bits: int = int(exp * math.log2(abs(base))) + 1
    if est_bits > _MAX_INT_BITS:
        return None
    result_int: int = base ** exp
    return result_int if _int_size_ok(result_int) else None


class _Parser:
    """Рекурсивный спуск:
    expression := term (('+'|'-') term)*
    term       := factor (('*'|'/') factor)*
    factor     := unary ('^' factor)?      (правая ассоциативность)
    unary      := ('+'|'-') unary | atom
    atom       := num | '(' expression ')'
    """

    def __init__(self, tokens: List[Tuple[str, str]], base: int) -> None:
        self.tokens: List[Tuple[str, str]] = tokens
        self.base: int = base
        self.pos: int = 0

    def peek(self) -> Tuple[Optional[str], str]:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return (None, '')

    def take(self) -> Tuple[Optional[str], str]:
        tok: Tuple[Optional[str], str] = self.peek()
        self.pos += 1
        return tok

    def parse(self) -> Optional[Union[int, float]]:
        value: Optional[Union[int, float]] = self.expr()
        if value is None or self.pos != len(self.tokens):
            return None
        return value

    def expr(self) -> Optional[Union[int, float]]:
        value: Optional[Union[int, float]] = self.term()
        while value is not None:
            kind: Optional[str] = self.peek()[0]
            if kind not in ('+', '-'):
                break
            self.take()
            rhs: Optional[Union[int, float]] = self.term()
            if rhs is None:
                return None
            value = value + rhs if kind == '+' else value - rhs
            if isinstance(value, int) and not _int_size_ok(value):
                return None
        return value

    def term(self) -> Optional[Union[int, float]]:
        value: Optional[Union[int, float]] = self.factor()
        while value is not None:
            kind: Optional[str] = self.peek()[0]
            if kind not in ('*', '/'):
                break
            self.take()
            rhs: Optional[Union[int, float]] = self.factor()
            if rhs is None:
                return None
            if kind == '*':
                value = value * rhs
                if isinstance(value, int) and not _int_size_ok(value):
                    return None
            else:
                if rhs == 0:
                    return None
                num: Optional[float] = _to_float(value)
                den: Optional[float] = _to_float(rhs)
                if num is None or den is None:
                    return None
                value = num / den
        return value

    def factor(self) -> Optional[Union[int, float]]:
        value: Optional[Union[int, float]] = self.unary()
        if value is None:
            return None
        if self.peek()[0] == '^':
            self.take()
            exp: Optional[Union[int, float]] = self.factor()  # правая ассоциативность
            if exp is None:
                return None
            return _power(value, exp)
        return value

    def unary(self) -> Optional[Union[int, float]]:
        kind: Optional[str] = self.peek()[0]
        if kind in ('+', '-'):
            self.take()
            value: Optional[Union[int, float]] = self.unary()
            if value is None:
                return None
            return -value if kind == '-' else value
        return self.atom()

    def atom(self) -> Optional[Union[int, float]]:
        kind, text = self.take()
        if kind == 'num':
            if self.base == 10:
                return int(text) if re.fullmatch(r'\d+', text) else float(text)
            return int(text, self.base)
        if kind == '(':
            value: Optional[Union[int, float]] = self.expr()
            if value is None or self.peek()[0] != ')':
                return None
            self.take()
            return value
        return None


def evaluate(text: str, fmt: str) -> Optional[Union[int, float]]:
    """Вычисляет арифметическое выражение в системе счисления формата.

    Возвращает int (если результат целый) или float; None — выражение
    некорректно, деление на ноль или результат не представляем.
    """
    if fmt not in EXPR_FORMATS or not text or not text.strip():
        return None
    tokens: Optional[List[Tuple[str, str]]] = _tokenize(text, fmt)
    if tokens is None:
        return None
    value: Optional[Union[int, float]] = _Parser(tokens, _base(fmt)).parse()
    if value is None:
        return None
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return value if _int_size_ok(value) else None
