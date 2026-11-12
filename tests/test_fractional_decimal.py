# tests/test_fractional_decimal.py
# Дробные десятичные числа: float64 не должен «съедать» дробную часть
# больших чисел и выдавать целое (иначе HEX/bin строятся от него).

import unittest

from converters import Converter


class TestFractionalDecimal(unittest.TestCase):
    # --- dробная часть теряется float64 (x в [2**52, 2**53) и выше) ---

    def test_huge_fraction_not_lost_to_integer(self) -> None:
        # Баг-репорт: 5665666666666644.56565565 конвертировался в HEX
        self.assertIsNone(Converter.parse("5665666666666644.56565565", "decimal", 8))

    def test_huge_fraction_negative(self) -> None:
        self.assertIsNone(Converter.parse("-5665666666666644.56565565", "decimal", 8))

    def test_huge_fraction_comma(self) -> None:
        self.assertIsNone(Converter.parse("5665666666666644,56565565", "decimal", 8))

    def test_2_53_plus_half(self) -> None:
        self.assertIsNone(Converter.parse("9007199254740992.5", "decimal", 8))

    # --- малые дроби работают как раньше ---

    def test_small_fraction_still_works(self) -> None:
        v = Converter.parse("42.5", "decimal", 8)
        self.assertIsInstance(v, float)
        self.assertAlmostEqual(v, 42.5)
        # Целочисленные форматы для дроби — пусты
        self.assertIsNone(Converter.convert(v, "hex_direct", 8))
        self.assertIsNone(Converter.convert(v, "bin_direct", 8))
        # IEEE754 для дроби работает
        self.assertIsNotNone(Converter.convert(v, "ieee_hex", 4))

    def test_small_nonzero_fraction_not_integer(self) -> None:
        v = Converter.parse("5.0000001", "decimal", 8)
        self.assertIsInstance(v, float)
        self.assertFalse(v.is_integer())

    # --- нулевая дробная часть = целое ---

    def test_zero_fraction_is_integer(self) -> None:
        v = Converter.parse("5.0", "decimal", 8)
        self.assertEqual(v, 5)
        self.assertEqual(Converter.convert(v, "hex_direct", 8), "05")
        v2 = Converter.parse("5.000", "decimal", 8)
        self.assertEqual(v2, 5)

    def test_scientific_integer(self) -> None:
        # 1.5e3 = 1500 — целое, несмотря на точку в записи
        v = Converter.parse("1.5e3", "decimal", 8)
        self.assertEqual(v, 1500)

    def test_scientific_fraction(self) -> None:
        v = Converter.parse("1.5e2", "decimal", 8)  # 150.0 — целое
        self.assertEqual(v, 150)
        v2 = Converter.parse("1.25e2", "decimal", 8)  # 125.0
        self.assertEqual(v2, 125)
        v3 = Converter.parse("1.25e1", "decimal", 8)  # 12.5 — дробь
        self.assertIsInstance(v3, float)
        self.assertFalse(v3.is_integer())

    # --- переполнение ---

    def test_inf_not_parsed(self) -> None:
        self.assertIsNone(Converter.parse("1e400", "decimal", 8))


if __name__ == "__main__":
    unittest.main()
