# widgets/modbus/parser_ascii.py
# Python 3.11+, PyQt6

from typing import Dict, Any
import re
from widgets.modbus.constants import FUNCTION_NAMES, EXCEPTION_CODES, get_original_function
from widgets.modbus.parser_pdu import PDUParser


class ASCIJParser:
    
    @classmethod
    def lrc(cls, data: bytes) -> int:
        total = sum(data) & 0xFF
        lrc = (~total + 1) & 0xFF
        return lrc
    
    @classmethod
    def parse(cls, text: str, is_response: bool) -> Dict[str, Any]:
        result = {"protocol": "ASCII", "valid": False, "errors": [], "warnings": [], "structure_valid": False}

        # Убираем пробелы и дефисы
        ascii_str = text.replace(' ', '').replace('-', '')
        
        # Проверка стартового символа: ':' или '3A'
        if ascii_str.startswith(':'):
            payload = ascii_str[1:]
            result["raw_hex_full"] = "3A" + ascii_str[1:]  # Сохраняем полный HEX для отображения
        elif ascii_str.startswith('3A'):
            payload = ascii_str[2:]
            if payload.startswith(':'):
                payload = payload[1:]
            result["raw_hex_full"] = ascii_str
        else:
            if ':' in ascii_str:
                payload = ascii_str[ascii_str.index(':') + 1:]
                result["raw_hex_full"] = "3A" + payload
            else:
                result["errors"].append("Missing start ':'")
                return result
        
        # Проверка завершающих символов
        if payload.endswith('\r\n'):
            payload = payload[:-2]
            if not result.get("raw_hex_full"):
                result["raw_hex_full"] = "3A" + payload + "0D0A"
            else:
                result["raw_hex_full"] = result["raw_hex_full"].replace('\r\n', '') + "0D0A"
        elif payload.endswith('\n'):
            payload = payload[:-1]
        elif payload.endswith('0D0A'):
            payload = payload[:-4]
            if not result.get("raw_hex_full"):
                result["raw_hex_full"] = "3A" + payload + "0D0A"
            else:
                result["raw_hex_full"] = result["raw_hex_full"].replace('0D0A', '') + "0D0A"
        elif payload.endswith('0d0a'):
            payload = payload[:-4]
        
        # Убираем все не-HEX символы
        payload = re.sub(r'[^0-9A-Fa-f]', '', payload)
        
        if len(payload) < 4:
            result["errors"].append("Payload too short")
            return result
        
        if len(payload) % 2 != 0:
            result["errors"].append(f"Odd number of hex characters: {len(payload)}")
            return result

        try:
            raw = bytes.fromhex(payload)
        except ValueError as e:
            result["errors"].append(f"Invalid hex characters: {str(e)}")
            return result

        if len(raw) < 2:
            result["errors"].append("Too short")
            return result

        # LRC проверка
        received_lrc = raw[-1]
        calculated_lrc = cls.lrc(raw[:-1])
        result["lrc_received"] = f"0x{received_lrc:02X}"
        result["lrc_calculated"] = f"0x{calculated_lrc:02X}"
        result["lrc_valid"] = received_lrc == calculated_lrc
        
        if not result["lrc_valid"]:
            result["errors"].append(f"LRC mismatch: received {result['lrc_received']}, calculated {result['lrc_calculated']}")

        result["slave_address"] = raw[0]
        result["slave_address_desc"] = "Slave address"
        function_code = raw[1]
        result["function_code"] = function_code
        result["function_code_desc"] = "Modbus function code"
        pdu = raw[2:-1] if len(raw) > 2 else b''
        
        if is_response:
            pdu_result = PDUParser.parse_response(function_code, pdu)
        else:
            pdu_result = PDUParser.parse_request(function_code, pdu)
        
        result.update(pdu_result)
        
        # Формируем raw_hex для отображения
        if not result.get("raw_hex_full"):
            result["raw_hex_full"] = payload
        
        if result.get("errors"):
            result["valid"] = False
            result["structure_valid"] = False
        else:
            result["valid"] = True
            result["structure_valid"] = True
        
        return result