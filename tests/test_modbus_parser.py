# tests/test_modbus_parser.py (добавлены тесты из примера ipc2u.ru для RTU)
# Python 3.11+, PyQt6

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from widgets.modbus.modbus_parser import ModbusParser


class TestModbusParser(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.parser = ModbusParser()
    
    # ==================== ТЕСТЫ ИЗ ПРИМЕРОВ IPC2U.RU ДЛЯ TCP ====================
    
    # Пример 1: Чтение аналоговых выходов (holding registers) - функция 0x03
    def test_example_tcp_read_holding_registers_request(self):
        result = self.parser.parse("0001000000061103006B0003", "TCP", False)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("transaction_id"), 1)
        self.assertEqual(result.get("unit_id"), 0x11)
        self.assertEqual(result.get("function_code"), 3)
        self.assertEqual(result.get("start_address"), 0x006B)
        self.assertEqual(result.get("quantity"), 3)
    
    def test_example_tcp_read_holding_registers_response(self):
        result = self.parser.parse("000100000009110306022B0064007F", "TCP", True)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("function_code"), 3)
        self.assertEqual(result.get("byte_count"), 6)
        self.assertEqual(result.get("registers"), [0x022B, 0x0064, 0x007F])
    
    # Пример 2: Чтение дискретных выходов - функция 0x01
    def test_example_tcp_read_coils_request(self):
        result = self.parser.parse("010200000006010100000002", "TCP", False)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("function_code"), 1)
        self.assertEqual(result.get("start_address"), 0)
        self.assertEqual(result.get("quantity"), 2)
    
    def test_example_tcp_read_coils_response(self):
        result = self.parser.parse("01020000000401010102", "TCP", True)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("function_code"), 1)
        self.assertEqual(result.get("byte_count"), 1)
        bits = result.get("bits")
        self.assertIsNotNone(bits)
        self.assertEqual(bits[:2], [0, 1])
    
    # Пример 3: Запись одного дискретного выхода - функция 0x05
    def test_example_tcp_write_single_coil_request(self):
        result = self.parser.parse("01020000000601050001FF00", "TCP", False)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("function_code"), 5)
        self.assertEqual(result.get("start_address"), 1)
        self.assertEqual(result.get("value"), 0xFF00)
    
    # Пример 4: Запись одного аналогового выхода - функция 0x06
    def test_example_tcp_write_single_register_request(self):
        result = self.parser.parse("0102000000060106000155FF", "TCP", False)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("function_code"), 6)
        self.assertEqual(result.get("start_address"), 1)
        self.assertEqual(result.get("value"), 0x55FF)
    
    # Пример 5: Запись нескольких аналоговых выходов - функция 0x10
    def test_example_tcp_write_multiple_registers_request(self):
        result = self.parser.parse("01020000000B01100000000204000A0102", "TCP", False)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("function_code"), 16)
        self.assertEqual(result.get("start_address"), 0)
        self.assertEqual(result.get("quantity"), 2)
        self.assertEqual(result.get("byte_count"), 4)
        self.assertEqual(result.get("registers"), [0x000A, 0x0102])
    
    # Пример 6: Исключение
    def test_example_tcp_exception_response(self):
        result = self.parser.parse("0102000000030A8102", "TCP", True)
        self.assertTrue(result.get("valid"))
        self.assertTrue(result.get("is_exception"))
        self.assertEqual(result.get("function_code"), 0x81)
        self.assertEqual(result.get("exception_code"), 2)
    
    # ==================== ТЕСТЫ ИЗ ПРИМЕРОВ IPC2U.RU ДЛЯ RTU ====================
    
    # Пример 1: Чтение аналоговых выходов - функция 0x03
    # Запрос: 11 03 006B 0003 7687
    # Ответ:   11 03 06 AE41 5652 4340 49AD
    def test_example_rtu_read_holding_registers_request(self):
        result = self.parser.parse_rtu_with_options("1103006B00037687", False, True, True)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("slave_address"), 0x11)
        self.assertEqual(result.get("function_code"), 3)
        self.assertEqual(result.get("start_address"), 0x006B)
        self.assertEqual(result.get("quantity"), 3)
    
    def test_example_rtu_read_holding_registers_response(self):
        result = self.parser.parse_rtu_with_options("110306AE415652434049AD", True, True, True)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("slave_address"), 0x11)
        self.assertEqual(result.get("function_code"), 3)
        self.assertEqual(result.get("byte_count"), 6)
        self.assertEqual(result.get("registers"), [0xAE41, 0x5652, 0x4340])
    
    # Пример 2: Чтение дискретных выходов DO с 20 по 56 - функция 0x01
    # Запрос: 11 01 0013 0025 0E84
    # Ответ:   11 01 05 CD6BB20E1B45E6
    def test_example_rtu_read_coils_request(self):
        result = self.parser.parse_rtu_with_options("1101001300250E84", False, True, True)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("slave_address"), 0x11)
        self.assertEqual(result.get("function_code"), 1)
        self.assertEqual(result.get("start_address"), 0x0013)
        self.assertEqual(result.get("quantity"), 0x0025)
    
    def test_example_rtu_read_coils_response(self):
        result = self.parser.parse_rtu_with_options("110105CD6BB20E1B45E6", True, True, True)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("slave_address"), 0x11)
        self.assertEqual(result.get("function_code"), 1)
        self.assertEqual(result.get("byte_count"), 5)
        bits = result.get("bits")
        self.assertIsNotNone(bits)
        self.assertEqual(len(bits), 40)  # 5 bytes * 8 bits
    
    # Пример 3: Чтение дискретных входов DI - функция 0x02
    # Запрос: 11 02 00C4 0016 BAA9
    # Ответ:   11 02 03 ACDB352018
    def test_example_rtu_read_discrete_inputs_request(self):
        result = self.parser.parse_rtu_with_options("110200C40016BAA9", False, True, True)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("slave_address"), 0x11)
        self.assertEqual(result.get("function_code"), 2)
        self.assertEqual(result.get("start_address"), 0x00C4)
        self.assertEqual(result.get("quantity"), 0x0016)
    
    def test_example_rtu_read_discrete_inputs_response(self):
        result = self.parser.parse_rtu_with_options("110203ACDB352018", True, True, True)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("slave_address"), 0x11)
        self.assertEqual(result.get("function_code"), 2)
        self.assertEqual(result.get("byte_count"), 3)
    
    # Пример 4: Чтение аналоговых входов AI - функция 0x04
    # Запрос: 11 04 0008 0001 B298
    # Ответ:   11 04 02 000A F8F4
    def test_example_rtu_read_input_registers_request(self):
        result = self.parser.parse_rtu_with_options("110400080001B298", False, True, True)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("slave_address"), 0x11)
        self.assertEqual(result.get("function_code"), 4)
        self.assertEqual(result.get("start_address"), 0x0008)
        self.assertEqual(result.get("quantity"), 1)
    
    def test_example_rtu_read_input_registers_response(self):
        result = self.parser.parse_rtu_with_options("110402000AF8F4", True, True, True)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("slave_address"), 0x11)
        self.assertEqual(result.get("function_code"), 4)
        self.assertEqual(result.get("byte_count"), 2)
        self.assertEqual(result.get("registers"), [0x000A])
    
    # Пример 5: Запись одного дискретного выхода DO - функция 0x05
    # Запрос: 11 05 00AC FF00 4E8B
    # Ответ:   11 05 00AC FF00 4E8B
    def test_example_rtu_write_single_coil_request(self):
        result = self.parser.parse_rtu_with_options("110500ACFF004E8B", False, True, True)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("slave_address"), 0x11)
        self.assertEqual(result.get("function_code"), 5)
        self.assertEqual(result.get("start_address"), 0x00AC)
        self.assertEqual(result.get("value"), 0xFF00)
    
    def test_example_rtu_write_single_coil_response(self):
        result = self.parser.parse_rtu_with_options("110500ACFF004E8B", True, True, True)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("slave_address"), 0x11)
        self.assertEqual(result.get("function_code"), 5)
        self.assertEqual(result.get("start_address"), 0x00AC)
        self.assertEqual(result.get("value"), 0xFF00)
    
    # Пример 6: Запись одного аналогового выхода AO - функция 0x06
    # Запрос: 11 06 0001 0003 9A9B
    # Ответ:   11 06 0001 0003 9A9B
    def test_example_rtu_write_single_register_request(self):
        result = self.parser.parse_rtu_with_options("1106000100039A9B", False, True, True)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("slave_address"), 0x11)
        self.assertEqual(result.get("function_code"), 6)
        self.assertEqual(result.get("start_address"), 1)
        self.assertEqual(result.get("value"), 3)
    
    def test_example_rtu_write_single_register_response(self):
        result = self.parser.parse_rtu_with_options("1106000100039A9B", True, True, True)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("slave_address"), 0x11)
        self.assertEqual(result.get("function_code"), 6)
        self.assertEqual(result.get("start_address"), 1)
        self.assertEqual(result.get("value"), 3)
    
    # Пример 7: Запись нескольких дискретных выводов DO - функция 0x0F
    # Запрос: 11 0F 0013 000A 02 CD01 BF0B
    # Ответ:   11 0F 0013 000A 2699
    def test_example_rtu_write_multiple_coils_request(self):
        result = self.parser.parse_rtu_with_options("110F0013000A02CD01BF0B", False, True, True)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("slave_address"), 0x11)
        self.assertEqual(result.get("function_code"), 15)
        self.assertEqual(result.get("start_address"), 0x0013)
        self.assertEqual(result.get("quantity"), 0x000A)
        self.assertEqual(result.get("byte_count"), 2)
    
    def test_example_rtu_write_multiple_coils_response(self):
        result = self.parser.parse_rtu_with_options("110F0013000A2699", True, True, True)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("slave_address"), 0x11)
        self.assertEqual(result.get("function_code"), 15)
        self.assertEqual(result.get("start_address"), 0x0013)
        self.assertEqual(result.get("quantity"), 0x000A)
    
    # Пример 8: Запись нескольких аналоговых выходов AO - функция 0x10
    # Запрос: 11 10 0001 0002 04 000A 0102 C6F0
    # Ответ:   11 10 0001 0002 1298
    def test_example_rtu_write_multiple_registers_request(self):
        result = self.parser.parse_rtu_with_options("11100001000204000A0102C6F0", False, True, True)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("slave_address"), 0x11)
        self.assertEqual(result.get("function_code"), 16)
        self.assertEqual(result.get("start_address"), 1)
        self.assertEqual(result.get("quantity"), 2)
        self.assertEqual(result.get("byte_count"), 4)
        self.assertEqual(result.get("registers"), [0x000A, 0x0102])
    
    def test_example_rtu_write_multiple_registers_response(self):
        result = self.parser.parse_rtu_with_options("1110000100021298", True, True, True)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("slave_address"), 0x11)
        self.assertEqual(result.get("function_code"), 16)
        self.assertEqual(result.get("start_address"), 1)
        self.assertEqual(result.get("quantity"), 2)
    
    # Пример 9: Исключение Modbus RTU
    # Запрос: 0A 01 04A1 0001 AC63
    # Ответ:   0A 81 02 B053
    def test_example_rtu_exception_response(self):
        result = self.parser.parse_rtu_with_options("0A8102B053", True, True, True)
        self.assertTrue(result.get("valid"))
        self.assertTrue(result.get("is_exception"))
        self.assertEqual(result.get("slave_address"), 0x0A)
        self.assertEqual(result.get("function_code"), 0x81)
        self.assertEqual(result.get("exception_code"), 2)
    
    # ==================== TCP TESTS ====================
    
    def test_tcp_valid_request_read_holding_registers(self):
        result = self.parser.parse("03E50000000601030FA00002", "TCP", False)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("function_code"), 3)
        self.assertEqual(result.get("start_address"), 0x0FA0)
        self.assertEqual(result.get("quantity"), 2)
    
    def test_tcp_valid_request_write_single_register(self):
        result = self.parser.parse("03E700000006010600010001", "TCP", False)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("function_code"), 6)
        self.assertEqual(result.get("start_address"), 1)
        self.assertEqual(result.get("value"), 1)
    
    def test_tcp_valid_request_write_multiple_registers(self):
        result = self.parser.parse("03E80000000D0110000A00020400010002", "TCP", False)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("function_code"), 16)
        self.assertEqual(result.get("start_address"), 10)
        self.assertEqual(result.get("quantity"), 2)
        self.assertEqual(result.get("byte_count"), 4)
    
    def test_tcp_valid_response_read_holding_registers(self):
        result = self.parser.parse("03E60000000701030400070003", "TCP", True)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("function_code"), 3)
        self.assertEqual(result.get("byte_count"), 4)
        self.assertEqual(result.get("registers"), [7, 3])
    
    def test_tcp_valid_response_write_single_register(self):
        result = self.parser.parse("03E700000006010600010001", "TCP", True)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("function_code"), 6)
        self.assertEqual(result.get("start_address"), 1)
        self.assertEqual(result.get("value"), 1)
    
    def test_tcp_valid_response_write_multiple_registers(self):
        result = self.parser.parse("03E8000000060110000A0002", "TCP", True)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("function_code"), 16)
        self.assertEqual(result.get("start_address"), 10)
        self.assertEqual(result.get("quantity"), 2)
    
    def test_tcp_exception_illegal_function(self):
        result = self.parser.parse("03FC00000003018301", "TCP", True)
        self.assertTrue(result.get("valid"))
        self.assertTrue(result.get("is_exception"))
        self.assertEqual(result.get("exception_code"), 1)
    
    def test_tcp_exception_illegal_data_address(self):
        result = self.parser.parse("03FC00000003018302", "TCP", True)
        self.assertTrue(result.get("valid"))
        self.assertTrue(result.get("is_exception"))
        self.assertEqual(result.get("exception_code"), 2)
    
    def test_tcp_exception_illegal_data_value(self):
        result = self.parser.parse("03FC00000003018303", "TCP", True)
        self.assertTrue(result.get("valid"))
        self.assertTrue(result.get("is_exception"))
        self.assertEqual(result.get("exception_code"), 3)
    
    def test_tcp_exception_slave_device_failure(self):
        result = self.parser.parse("03FC00000003018304", "TCP", True)
        self.assertTrue(result.get("valid"))
        self.assertTrue(result.get("is_exception"))
        self.assertEqual(result.get("exception_code"), 4)
    
    def test_tcp_invalid_request_too_short_pdu(self):
        result = self.parser.parse("03E500000004010302", "TCP", False)
        self.assertFalse(result.get("valid"))
    
    def test_tcp_invalid_request_exception_bit_set(self):
        result = self.parser.parse("03E5000000060183020002", "TCP", False)
        self.assertFalse(result.get("valid"))
    
    def test_tcp_invalid_frame_too_short(self):
        result = self.parser.parse("03E500", "TCP", False)
        self.assertFalse(result.get("valid"))
    
    def test_tcp_invalid_protocol_id(self):
        result = self.parser.parse("03E50001000601030FA00002", "TCP", False)
        self.assertFalse(result.get("valid"))
        self.assertIn("Protocol ID not zero", " ".join(result.get("errors", [])))
    
    # ==================== RTU TESTS (с опциями) ====================
    
    def test_rtu_valid_request_read_holding_registers_slave_crc_yes(self):
        result = self.parser.parse_rtu_with_options("01034E20000192E8", False, True, True)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("slave_address"), 1)
        self.assertEqual(result.get("function_code"), 3)
        self.assertEqual(result.get("start_address"), 0x4E20)
        self.assertEqual(result.get("quantity"), 1)
    
    def test_rtu_valid_request_read_holding_registers_slave_yes_crc_no(self):
        result = self.parser.parse_rtu_with_options("01034E200001", False, True, False)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("slave_address"), 1)
        self.assertEqual(result.get("function_code"), 3)
        self.assertEqual(result.get("start_address"), 0x4E20)
        self.assertEqual(result.get("quantity"), 1)
    
    def test_rtu_valid_request_read_holding_registers_slave_no_crc_yes(self):
        result = self.parser.parse_rtu_with_options("034E20000192E8", False, False, True)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("slave_address"), None)
        self.assertEqual(result.get("function_code"), 3)
        self.assertEqual(result.get("start_address"), 0x4E20)
        self.assertEqual(result.get("quantity"), 1)
    
    def test_rtu_valid_request_read_holding_registers_slave_no_crc_no(self):
        result = self.parser.parse_rtu_with_options("034E200001", False, False, False)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("slave_address"), None)
        self.assertEqual(result.get("function_code"), 3)
        self.assertEqual(result.get("start_address"), 0x4E20)
        self.assertEqual(result.get("quantity"), 1)
    
    def test_rtu_valid_response_read_holding_registers(self):
        result = self.parser.parse_rtu_with_options("01030400070003F30B", True, True, True)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("function_code"), 3)
        self.assertEqual(result.get("registers"), [7, 3])
    
    def test_rtu_exception_illegal_data_address(self):
        result = self.parser.parse_rtu_with_options("01830230F1", True, True, True)
        self.assertTrue(result.get("valid"))
        self.assertTrue(result.get("is_exception"))
        self.assertEqual(result.get("exception_code"), 2)
    
    # ==================== ASCII TESTS ====================
    
    def test_ascii_valid_request_read_holding_registers(self):
        result = self.parser.parse(":01030FA000024B\r\n", "ASCII", False)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("function_code"), 3)
        self.assertEqual(result.get("start_address"), 0x0FA0)
        self.assertEqual(result.get("quantity"), 2)
    
    def test_ascii_valid_response_read_holding_registers(self):
        result = self.parser.parse(":01030400070003EE\r\n", "ASCII", True)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("function_code"), 3)
        self.assertEqual(result.get("registers"), [7, 3])
    
    def test_ascii_exception_illegal_data_address(self):
        result = self.parser.parse(":0183027A\r\n", "ASCII", True)
        self.assertTrue(result.get("valid"))
        self.assertTrue(result.get("is_exception"))
        self.assertEqual(result.get("exception_code"), 2)
    
    def test_ascii_lrc_invalid(self):
        result = self.parser.parse(":01030FA00002FF\r\n", "ASCII", False)
        self.assertFalse(result.get("valid"))
        self.assertIn("LRC mismatch", " ".join(result.get("errors", [])))
    
    def test_ascii_invalid_missing_start_char(self):
        result = self.parser.parse("01030FA00002FA\r\n", "ASCII", False)
        self.assertFalse(result.get("valid"))
    
    def test_ascii_invalid_missing_crlf(self):
        result = self.parser.parse(":01030FA00002FA", "ASCII", False)
        self.assertFalse(result.get("valid"))
    
    def test_ascii_invalid_hex_characters(self):
        result = self.parser.parse(":0103GFA00002FA\r\n", "ASCII", False)
        self.assertFalse(result.get("valid"))
    
    # ==================== EDGE CASES ====================
    
    def test_empty_input(self):
        result = self.parser.parse("", "TCP", False)
        self.assertFalse(result.get("valid"))
    
    def test_spaces_ignored(self):
        result = self.parser.parse("03 E5 00 00 00 06 01 03 0F A0 00 02", "TCP", False)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("function_code"), 3)
    
    def test_newlines_ignored(self):
        result = self.parser.parse("03E5\n0000\n0006\n0103\n0FA0\n0002", "TCP", False)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("function_code"), 3)
    
    def test_unknown_protocol(self):
        result = self.parser.parse("01030FA00002", "UNKNOWN", False)
        self.assertFalse(result.get("valid"))
    
    def test_invalid_hex(self):
        result = self.parser.parse("ZZZZZZ", "TCP", False)
        self.assertFalse(result.get("valid"))


class TestModbusIntegration(unittest.TestCase):
    
    def test_tcp_request_response_pair_read_registers(self):
        parser = ModbusParser()
        request = parser.parse("0001000000061103006B0003", "TCP", False)
        response = parser.parse("000100000009110306022B0064007F", "TCP", True)
        
        self.assertTrue(request.get("valid"))
        self.assertTrue(response.get("valid"))
        self.assertEqual(request.get("start_address"), 0x006B)
        self.assertEqual(request.get("quantity"), 3)
        self.assertEqual(response.get("registers"), [0x022B, 0x0064, 0x007F])
    
    def test_tcp_request_response_pair_write_multiple_registers(self):
        parser = ModbusParser()
        request = parser.parse("01020000000B01100000000204000A0102", "TCP", False)
        response = parser.parse("010200000006011000000002", "TCP", True)
        
        self.assertTrue(request.get("valid"))
        self.assertTrue(response.get("valid"))
        self.assertEqual(request.get("start_address"), 0)
        self.assertEqual(request.get("quantity"), 2)
        self.assertEqual(request.get("registers"), [0x000A, 0x0102])
    
    def test_rtu_request_response_pair_read_holding_registers(self):
        parser = ModbusParser()
        request = parser.parse_rtu_with_options("1103006B00037687", False, True, True)
        response = parser.parse_rtu_with_options("110306AE415652434049AD", True, True, True)
        
        self.assertTrue(request.get("valid"))
        self.assertTrue(response.get("valid"))
        self.assertEqual(request.get("start_address"), 0x006B)
        self.assertEqual(request.get("quantity"), 3)
        self.assertEqual(response.get("registers"), [0xAE41, 0x5652, 0x4340])
    
    def test_rtu_request_response_pair_write_multiple_registers(self):
        parser = ModbusParser()
        request = parser.parse_rtu_with_options("11100001000204000A0102C6F0", False, True, True)
        response = parser.parse_rtu_with_options("1110000100021298", True, True, True)
        
        self.assertTrue(request.get("valid"))
        self.assertTrue(response.get("valid"))
        self.assertEqual(request.get("start_address"), 1)
        self.assertEqual(request.get("quantity"), 2)
        self.assertEqual(request.get("registers"), [0x000A, 0x0102])
    
    def test_rtu_different_slave_crc_combinations_same_data(self):
        parser = ModbusParser()
        data = "034E200001"
        
        result_slave_no_crc_no = parser.parse_rtu_with_options(data, False, False, False)
        result_slave_yes_crc_no = parser.parse_rtu_with_options("01" + data, False, True, False)
        result_slave_no_crc_yes = parser.parse_rtu_with_options(data + "92E8", False, False, True)
        result_slave_yes_crc_yes = parser.parse_rtu_with_options("01" + data + "92E8", False, True, True)
        
        self.assertTrue(result_slave_no_crc_no.get("valid"))
        self.assertTrue(result_slave_yes_crc_no.get("valid"))
        self.assertTrue(result_slave_no_crc_yes.get("valid"))
        self.assertTrue(result_slave_yes_crc_yes.get("valid"))
        
        self.assertEqual(result_slave_no_crc_no.get("start_address"), 0x4E20)
        self.assertEqual(result_slave_yes_crc_no.get("start_address"), 0x4E20)
        self.assertEqual(result_slave_no_crc_yes.get("start_address"), 0x4E20)
        self.assertEqual(result_slave_yes_crc_yes.get("start_address"), 0x4E20)


if __name__ == "__main__":
    unittest.main()