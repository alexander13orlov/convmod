# converters.py
# project_root/converters.py
# Python 3.11+, PyQt6

import struct
from typing import Optional, Union


class Converter:
    @staticmethod
    def parse(value_str: str, fmt: str, nb: int) -> Optional[Union[int, float]]:
        try:
            value_str = value_str.replace(',', '.')
            if fmt == 'decimal':
                # Парсим как float всегда, потом преобразуем если целое
                num = float(value_str)
                if num.is_integer():
                    return int(num)
                return num
            elif fmt == 'bin_direct':
                if not value_str:
                    return None
                sign: int = -1 if value_str.startswith('-') else 1
                num_str: str = value_str.lstrip('-')
                return sign * int(num_str, 2) if num_str else None
            elif fmt == 'bin_complement':
                actual_bits = len(value_str)
                if actual_bits % 8 != 0 or actual_bits == 0:
                    return None
                val: int = int(value_str, 2)
                if val & (1 << (actual_bits - 1)):
                    val -= 1 << actual_bits
                return val
            elif fmt == 'hex_direct':
                if not value_str:
                    return None
                sign = -1 if value_str.startswith('-') else 1
                num_str = value_str.lstrip('-')
                return sign * int(num_str, 16) if num_str else None
            elif fmt == 'hex_complement':
                actual_hex_len = len(value_str)
                if actual_hex_len % 2 != 0 or actual_hex_len == 0:
                    return None
                actual_bits = actual_hex_len * 4
                val = int(value_str, 16)
                if val & (1 << (actual_bits - 1)):
                    val -= 1 << actual_bits
                return val
            elif fmt == 'ieee_bin':
                if nb not in (4, 8) or len(value_str) != nb * 8:
                    return None
                b: bytes = int(value_str, 2).to_bytes(nb, 'big')
                result = struct.unpack('>f' if nb == 4 else '>d', b)[0]
                if result.is_integer():
                    return int(result)
                return result
            elif fmt == 'ieee_hex':
                if nb not in (4, 8) or len(value_str) != nb * 2:
                    return None
                b = bytes.fromhex(value_str)
                result = struct.unpack('>f' if nb == 4 else '>d', b)[0]
                if result.is_integer():
                    return int(result)
                return result
            elif fmt == 'unicode_char':
                return ord(value_str) if len(value_str) == 1 else None
            elif fmt == 'utf8_char':
                return int.from_bytes(value_str.encode('utf-8'), 'big') if len(value_str) == 1 else None
        except Exception:
            return None
        return None

    @staticmethod
    def convert(value: Union[int, float], target_fmt: str, nb: int) -> Optional[str]:
        try:
            if target_fmt == 'decimal':
                if isinstance(value, float):
                    # Убираем незначащие нули в дробной части
                    return f"{value:.10f}".rstrip('0').rstrip('.') if '.' in f"{value:.10f}" else str(int(value))
                return str(value)
            elif target_fmt == 'bin_direct':
                if not isinstance(value, int):
                    # Если float с нулевой дробной частью, преобразуем в int
                    if isinstance(value, float) and value.is_integer():
                        value = int(value)
                    else:
                        return None
                if value >= 0:
                    result: str = bin(value)[2:]
                    if len(result) % 8 != 0:
                        result = '0' * (8 - len(result) % 8) + result
                    return result
                abs_result: str = bin(abs(value))[2:]
                if len(abs_result) % 8 != 0:
                    abs_result = '0' * (8 - len(abs_result) % 8) + abs_result
                return '-' + abs_result
            elif target_fmt == 'bin_complement':
                if not isinstance(value, int):
                    if isinstance(value, float) and value.is_integer():
                        value = int(value)
                    else:
                        return None
                if value >= 0:
                    bits = max(8, (value.bit_length() + 7) // 8 * 8)
                else:
                    bits = max(8, (abs(value).bit_length() + 7) // 8 * 8)
                mask: int = (1 << bits) - 1
                return f"{value & mask:0{bits}b}"
            elif target_fmt == 'hex_direct':
                if not isinstance(value, int):
                    if isinstance(value, float) and value.is_integer():
                        value = int(value)
                    else:
                        return None
                if value >= 0:
                    result = hex(value)[2:].upper()
                    if len(result) % 2 != 0:
                        result = '0' + result
                    return result
                abs_result = hex(abs(value))[2:].upper()
                if len(abs_result) % 2 != 0:
                    abs_result = '0' + abs_result
                return '-' + abs_result
            elif target_fmt == 'hex_complement':
                if not isinstance(value, int):
                    if isinstance(value, float) and value.is_integer():
                        value = int(value)
                    else:
                        return None
                if value >= 0:
                    bits = max(8, (value.bit_length() + 7) // 8 * 8)
                else:
                    bits = max(8, (abs(value).bit_length() + 7) // 8 * 8)
                mask = (1 << bits) - 1
                hex_digits = bits // 4
                return f"{value & mask:0{hex_digits}X}"
            elif target_fmt == 'ieee_bin':
                if nb not in (4, 8):
                    return None
                # Всегда преобразуем в float для IEEE754
                float_val = float(value)
                packed: bytes = struct.pack('>f' if nb == 4 else '>d', float_val)
                return ''.join(f"{b:08b}" for b in packed)
            elif target_fmt == 'ieee_hex':
                if nb not in (4, 8):
                    return None
                float_val = float(value)
                packed = struct.pack('>f' if nb == 4 else '>d', float_val)
                return packed.hex().upper()
            elif target_fmt == 'unicode_char':
                if isinstance(value, float) and value.is_integer():
                    value = int(value)
                if not isinstance(value, int):
                    return None
                try:
                    return chr(value)
                except (ValueError, OverflowError):
                    return None
            elif target_fmt == 'utf8_char':
                if isinstance(value, float) and value.is_integer():
                    value = int(value)
                if not isinstance(value, int):
                    return None
                try:
                    byte_len: int = (value.bit_length() + 7) // 8 if value >= 0 else 1
                    return value.to_bytes(byte_len, 'big').decode('utf-8')
                except (OverflowError, UnicodeDecodeError):
                    return None
        except Exception:
            return None
        return None