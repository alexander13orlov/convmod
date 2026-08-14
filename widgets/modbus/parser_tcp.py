# widgets/modbus/parser_tcp.py (исправлен - добавлены пояснения)
# Python 3.11+, PyQt6

from typing import Dict, Any
from widgets.modbus.parser_pdu import PDUParser


class TCPParser:
    
    @classmethod
    def parse(cls, data: bytes, is_response: bool) -> Dict[str, Any]:
        result = {"protocol": "TCP", "valid": False, "errors": [], "warnings": []}

        if len(data) < 8:
            result["errors"].append(f"Too short: {len(data)} bytes (min 8)")
            result["structure_valid"] = False
            return result

        result["transaction_id"] = (data[0] << 8) | data[1]
        result["protocol_id"] = (data[2] << 8) | data[3]
        result["length"] = (data[4] << 8) | data[5]
        result["unit_id"] = data[6]

        # Добавляем пояснения
        result["transaction_id_desc"] = "Unique transaction identifier (echoed in response)"
        result["protocol_id_desc"] = "Protocol identifier (always 0x0000 for Modbus)"
        result["length_desc"] = "Number of bytes following (Unit ID + PDU)"
        result["unit_id_desc"] = "Unit identifier (slave address)"

        if result["protocol_id"] != 0:
            result["errors"].append(f"Protocol ID not zero: {result['protocol_id']}")
            result["warnings"].append("Invalid protocol ID (should be 0x0000 for Modbus TCP)")
            result["structure_valid"] = False
            return result

        # Проверка соответствия Length фактической длине данных
        actual_length = len(data) - 6
        if result["length"] != actual_length:
            warning = f"Length field mismatch: declared {result['length']} bytes, actual {actual_length} bytes"
            result["warnings"].append(warning)

        if result["length"] == 0:
            result["warnings"].append("Length field is 0 - empty Modbus TCP frame (no PDU data)")
            result["structure_valid"] = False
            return result

        if len(data) <= 7:
            result["structure_valid"] = False
            return result

        function_code = data[7]
        pdu = data[8:] if len(data) > 8 else b''
        
        if is_response:
            pdu_result = PDUParser.parse_response(function_code, pdu)
        else:
            pdu_result = PDUParser.parse_request(function_code, pdu)
        
        # Сохраняем существующие предупреждения перед обновлением
        existing_warnings = result.get("warnings", []).copy()
        
        # Обновляем результат
        result.update(pdu_result)
        
        # Восстанавливаем предупреждения из TCP-заголовка
        if existing_warnings:
            if "warnings" not in result:
                result["warnings"] = []
            result["warnings"].extend(existing_warnings)
        
        if result.get("errors"):
            result["valid"] = False
            result["structure_valid"] = False
        else:
            result["valid"] = True
            result["structure_valid"] = True
        
        return result