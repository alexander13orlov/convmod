# tests/test_big_numbers.py
# Точность конвертера чисел для больших значений
# Python 3.11+, PyQt6

import unittest

from converters import Converter


class TestBigNumbers(unittest.TestCase):
    """Десятичный ввод должен парситься точно (bignum), а не через float."""

    def test_decimal_exact_up_to_2_53_minus_1(self) -> None:
        v = 2 ** 53 - 1
        self.assertEqual(Converter.parse(str(v), "decimal", 8), v)

    def test_decimal_exact_beyond_2_53(self) -> None:
        # float (53-битная мантисса) теряет младшие биты начиная с 2**53
        for v in (2 ** 53 + 1, 2 ** 54 - 1, 2 ** 56 - 1, 2 ** 64 - 1):
            with self.subTest(value=v):
                self.assertEqual(Converter.parse(str(v), "decimal", 8), v)

    def test_decimal_negative_2_56_minus_1_from_bug_report(self) -> None:
        # -72057594037927935 не должно округляться до -2**56
        self.assertEqual(
            Converter.parse("-72057594037927935", "decimal", 8), -(2 ** 56 - 1)
        )

    def test_decimal_to_hex_exact(self) -> None:
        # 2**56 - 1 = 14 hex F's (even length -> no zero-padding)
        value = Converter.parse("-72057594037927935", "decimal", 8)
        self.assertEqual(Converter.convert(value, "hex_direct", 8), "-" + "F" * 14)

    def test_screenshot_case_16_nines(self) -> None:
        # 9999999999999999 не должно превращаться в 10**16 = 0x2386F26FC10000
        value = Converter.parse("9999999999999999", "decimal", 8)
        self.assertEqual(Converter.convert(value, "hex_direct", 8), "2386F26FC0FFFF")

    def test_hex_to_decimal_exact_2_64_minus_1(self) -> None:
        value = Converter.parse("FFFFFFFFFFFFFFFF", "hex_direct", 8)
        self.assertEqual(Converter.convert(value, "decimal", 8), "18446744073709551615")

    def test_round_trip_decimal_hex_odd_large(self) -> None:
        for s in ("9007199254740993", "9999999999999999", "72057594037927935"):
            with self.subTest(value=s):
                h = Converter.convert(Converter.parse(s, "decimal", 8), "hex_direct", 8)
                back = Converter.convert(Converter.parse(h, "hex_direct", 8), "decimal", 8)
                self.assertEqual(back, s)

    def test_round_trip_decimal_hex_powers_of_ten(self) -> None:
        for k in range(1, 19):
            with self.subTest(k=k):
                s = str(10 ** k)
                h = Converter.convert(Converter.parse(s, "decimal", 8), "hex_direct", 8)
                back = Converter.convert(Converter.parse(h, "hex_direct", 8), "decimal", 8)
                self.assertEqual(back, s)

    def test_fractional_decimal_unchanged(self) -> None:
        self.assertEqual(Converter.parse("25.75", "decimal", 8), 25.75)
        self.assertEqual(Converter.parse("25,75", "decimal", 8), 25.75)

    def test_small_integers_unchanged(self) -> None:
        self.assertEqual(Converter.parse("-42", "decimal", 8), -42)
        self.assertEqual(Converter.parse("0", "decimal", 8), 0)

    def test_ieee_single_precision_boundary(self) -> None:
        # IEEE754 single (nb=4): 2**24-1 представимо точно, 2**24+1 — уже нет
        for s, expected in (
            (str(2 ** 24 - 1), "4B7FFFFF"),
            (str(2 ** 24), "4B800000"),
            (str(2 ** 24 + 1), "4B800000"),
        ):
            with self.subTest(value=s):
                value = Converter.parse(s, "decimal", 8)
                self.assertEqual(Converter.convert(value, "ieee_hex", 4), expected)
