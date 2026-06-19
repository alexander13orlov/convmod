# widgets/modbus/parser_tcp.py
# Python 3.11+, PyQt6

from typing import Dict, Any
from widgets.modbus.parser_pdu import PDUParser


class TCPParser:
    
    @classmethod
    def parse(cls, data: bytes, is_response: bool) -> Dict[str, Any]:
        result = {"protocol": "TCP", "valid": False, "errors": []}

        if len(data) < 8:
            result["errors"].append(f"Too short: {len(data)} bytes (min 8)")
            result["structure_valid"] = False
            return result

        result["transaction_id"] = (data[0] << 8) | data[1]
        result["protocol_id"] = (data[2] << 8) | data[3]
        result["length"] = (data[4] << 8) | data[5]
        result["unit_id"] = data[6]

        if result["protocol_id"] != 0:
            result["errors"].append(f"Protocol ID not zero: {result['protocol_id']}")
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
        
        result.update(pdu_result)
        
        if result.get("errors"):
            result["valid"] = False
            result["structure_valid"] = False
        else:
            result["valid"] = True
            result["structure_valid"] = True
        
        return result