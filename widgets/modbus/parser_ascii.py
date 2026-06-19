# widgets/modbus/parser_ascii.py (исправлен - добавлена structure_valid)
# Python 3.11+, PyQt6

from typing import Dict, Any
from widgets.modbus.constants import FUNCTION_NAMES, EXCEPTION_CODES, get_original_function
from widgets.modbus.parser_pdu import PDUParser


class ASCIJParser:
    
    @classmethod
    def lrc(cls, data: bytes) -> int:
        total = sum(data) & 0xFF
        lrc = (~total + 1) & 0xFF
        return lrc
    
    @classmethod
    def parse(cls, data: bytes, is_response: bool) -> Dict[str, Any]:
        result = {"protocol": "ASCII", "valid": False, "errors": [], "structure_valid": False}

        try:
            ascii_str = data.decode('ascii', errors='ignore')
        except:
            result["errors"].append("Invalid ASCII")
            return result

        ascii_str = ascii_str.strip()
        
        if not ascii_str.startswith(':'):
            result["errors"].append("Missing start ':'")
            return result
        
        payload = ascii_str[1:]
        
        while payload and (payload.endswith('\r') or payload.endswith('\n')):
            payload = payload[:-1]

        payload = payload.replace(' ', '')
        
        if len(payload) % 2 != 0:
            result["errors"].append("Odd number of hex characters")
            return result

        try:
            raw = bytes.fromhex(payload)
        except ValueError:
            result["errors"].append("Invalid hex characters")
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
            return result

        result["slave_address"] = raw[0]
        function_code = raw[1]
        pdu = raw[2:-1] if len(raw) > 2 else b''
        
        if is_response:
            pdu_result = PDUParser.parse_response(function_code, pdu)
        else:
            pdu_result = PDUParser.parse_request(function_code, pdu)
        
        result.update(pdu_result)
        
        if result.get("errors"):
            result["valid"] = False
            result["structure_valid"] = False
        else:
            result["valid"] = True
            result["structure_valid"] = True
        
        return result