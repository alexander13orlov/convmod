# widgets/modbus/parser_rtu.py (полностью исправленный - добавлен метод parse без опций)
# Python 3.11+, PyQt6

from typing import Dict, Any
from widgets.modbus.parser_pdu import PDUParser, merge_pdu_result


class RTUParser:
    
    @classmethod
    def crc16(cls, data: bytes) -> int:
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc
    
    @classmethod
    def parse(cls, data: bytes, is_response: bool) -> Dict[str, Any]:
        result = {"protocol": "RTU", "valid": False, "errors": [], "warnings": []}
        
        if len(data) < 4:
            result["errors"].append(f"Too short: {len(data)} bytes (min 4)")
            result["structure_valid"] = False
            return result

        result["slave_address"] = data[0]
        function_code = data[1]
        result["function_code"] = function_code
        
        pdu = data[2:-2]
        msg_crc = (data[-1] << 8) | data[-2]
        calc_crc = cls.crc16(data[:-2])
        result["crc_received"] = f"0x{msg_crc:04X}"
        result["crc_calculated"] = f"0x{calc_crc:04X}"
        result["crc_valid"] = msg_crc == calc_crc
        
        if not result["crc_valid"]:
            result["errors"].append("CRC mismatch")
        
        if is_response:
            pdu_result = PDUParser.parse_response(function_code, pdu)
        else:
            pdu_result = PDUParser.parse_request(function_code, pdu)
        
        merge_pdu_result(result, pdu_result)
        
        # structure_valid: кадр соответствует структуре, за исключением ошибки CRC
        # (те же семантики, что в parse_rtu_with_options)
        crc_markers = ("CRC mismatch",)
        result["structure_valid"] = all(
            any(marker in err for marker in crc_markers) for err in result["errors"]
        )
        result["valid"] = not result.get("errors")
        
        return result