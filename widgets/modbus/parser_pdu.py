# widgets/modbus/parser_pdu.py (исправлен - добавлена функция 04)
# Python 3.11+, PyQt6

from typing import Dict, Any
from widgets.modbus.constants import FUNCTION_NAMES, EXCEPTION_CODES, get_original_function


class PDUParser:
    """Парсер PDU (Protocol Data Unit) - общая часть для всех протоколов"""
    
    @classmethod
    def parse_request(cls, function_code: int, pdu: bytes) -> Dict[str, Any]:
        result = {
            "function_code": function_code,
            "function_name": FUNCTION_NAMES.get(function_code, f"Unknown (0x{function_code:02X})"),
            "is_exception": False,
            "errors": []
        }
        
        if function_code & 0x80:
            result["errors"].append(f"Invalid request: function code 0x{function_code:02X} has exception bit set")
            result["function_name"] = "INVALID"
            return result
        
        if function_code == 3:  # Read Holding Registers
            if len(pdu) == 4:
                result["start_address"] = (pdu[0] << 8) | pdu[1]
                result["quantity"] = (pdu[2] << 8) | pdu[3]
            else:
                result["errors"].append(f"Invalid PDU length for function 03: expected 4 bytes, got {len(pdu)}")
        
        elif function_code == 4:  # Read Input Registers
            if len(pdu) == 4:
                result["start_address"] = (pdu[0] << 8) | pdu[1]
                result["quantity"] = (pdu[2] << 8) | pdu[3]
            else:
                result["errors"].append(f"Invalid PDU length for function 04: expected 4 bytes, got {len(pdu)}")
                
        elif function_code == 6:  # Write Single Register
            if len(pdu) == 4:
                result["start_address"] = (pdu[0] << 8) | pdu[1]
                result["value"] = (pdu[2] << 8) | pdu[3]
            else:
                result["errors"].append(f"Invalid PDU length for function 06: expected 4 bytes, got {len(pdu)}")
                
        elif function_code == 16:  # Write Multiple Registers
            if len(pdu) >= 5:
                result["start_address"] = (pdu[0] << 8) | pdu[1]
                result["quantity"] = (pdu[2] << 8) | pdu[3]
                result["byte_count"] = pdu[4]
                expected_data_len = result["byte_count"]
                if len(pdu) == 5 + expected_data_len:
                    result["data_bytes"] = pdu[5:5+expected_data_len]
                    result["registers"] = []
                    for i in range(0, expected_data_len, 2):
                        if i+1 < expected_data_len:
                            val = (result["data_bytes"][i] << 8) | result["data_bytes"][i+1]
                            result["registers"].append(val)
                else:
                    result["errors"].append(f"Invalid PDU length for function 16: expected 5 + {expected_data_len} bytes, got {len(pdu)}")
            else:
                result["errors"].append(f"Invalid PDU length for function 16: need at least 5 bytes, got {len(pdu)}")
                
        elif function_code == 1 or function_code == 2:  # Read Coils / Read Discrete Inputs
            if len(pdu) == 4:
                result["start_address"] = (pdu[0] << 8) | pdu[1]
                result["quantity"] = (pdu[2] << 8) | pdu[3]
            else:
                result["errors"].append(f"Invalid PDU length for function {function_code:02X}: expected 4 bytes, got {len(pdu)}")
                
        elif function_code == 5:  # Write Single Coil
            if len(pdu) == 4:
                result["start_address"] = (pdu[0] << 8) | pdu[1]
                result["value"] = (pdu[2] << 8) | pdu[3]
            else:
                result["errors"].append(f"Invalid PDU length for function 05: expected 4 bytes, got {len(pdu)}")
                
        elif function_code == 15:  # Write Multiple Coils
            if len(pdu) >= 5:
                result["start_address"] = (pdu[0] << 8) | pdu[1]
                result["quantity"] = (pdu[2] << 8) | pdu[3]
                result["byte_count"] = pdu[4]
            else:
                result["errors"].append(f"Invalid PDU length for function 15: need at least 5 bytes, got {len(pdu)}")
                
        else:
            result["errors"].append(f"Unsupported function code: 0x{function_code:02X}")
        
        return result
    
    @classmethod
    def parse_response(cls, function_code: int, pdu: bytes) -> Dict[str, Any]:
        result = {
            "function_code": function_code,
            "is_exception": False,
            "errors": []
        }
        
        if function_code & 0x80:
            original = get_original_function(function_code)
            result["function_name"] = f"EXCEPTION RESPONSE (Function {original:02X}: {FUNCTION_NAMES.get(original, 'Unknown')})"
            result["is_exception"] = True
            result["original_function_code"] = original
            
            if len(pdu) == 1:
                result["exception_code"] = pdu[0]
                result["exception_description"] = EXCEPTION_CODES.get(pdu[0], f"Unknown: 0x{pdu[0]:02X}")
            else:
                result["errors"].append(f"Invalid exception response length: expected 1 byte, got {len(pdu)}")
            return result
        
        result["function_name"] = FUNCTION_NAMES.get(function_code, f"Unknown (0x{function_code:02X})")
        
        if function_code == 3 or function_code == 4:  # Read Holding Registers or Read Input Registers
            if len(pdu) >= 1:
                result["byte_count"] = pdu[0]
                expected = result["byte_count"]
                if len(pdu) == 1 + expected:
                    result["data_bytes"] = pdu[1:1+expected]
                    result["registers"] = []
                    for i in range(0, expected, 2):
                        if i+1 < expected:
                            val = (result["data_bytes"][i] << 8) | result["data_bytes"][i+1]
                            result["registers"].append(val)
                    result["quantity"] = expected // 2
                else:
                    result["errors"].append(f"Invalid response length for function {function_code:02X}: expected 1 + {expected} bytes, got {len(pdu)}")
            else:
                result["errors"].append(f"Response too short for function {function_code:02X}: need at least 1 byte, got {len(pdu)}")
                
        elif function_code == 6:
            if len(pdu) == 4:
                result["start_address"] = (pdu[0] << 8) | pdu[1]
                result["value"] = (pdu[2] << 8) | pdu[3]
            else:
                result["errors"].append(f"Invalid response length for function 06: expected 4 bytes, got {len(pdu)}")
                
        elif function_code == 16:
            if len(pdu) == 4:
                result["start_address"] = (pdu[0] << 8) | pdu[1]
                result["quantity"] = (pdu[2] << 8) | pdu[3]
            else:
                result["errors"].append(f"Invalid response length for function 16: expected 4 bytes, got {len(pdu)}")
                
        elif function_code == 1 or function_code == 2:
            if len(pdu) >= 1:
                result["byte_count"] = pdu[0]
                expected = result["byte_count"]
                if len(pdu) == 1 + expected:
                    result["data_bytes"] = pdu[1:1+expected]
                    result["bits"] = []
                    for byte in result["data_bytes"]:
                        for bit in range(8):
                            result["bits"].append((byte >> bit) & 1)
                    result["quantity"] = expected * 8
                else:
                    result["errors"].append(f"Invalid response length for function {function_code:02X}: expected 1 + {expected} bytes, got {len(pdu)}")
            else:
                result["errors"].append(f"Response too short for function {function_code:02X}: need at least 1 byte, got {len(pdu)}")
                
        elif function_code == 5:
            if len(pdu) == 4:
                result["start_address"] = (pdu[0] << 8) | pdu[1]
                result["value"] = (pdu[2] << 8) | pdu[3]
            else:
                result["errors"].append(f"Invalid response length for function 05: expected 4 bytes, got {len(pdu)}")
                
        elif function_code == 15:
            if len(pdu) == 4:
                result["start_address"] = (pdu[0] << 8) | pdu[1]
                result["quantity"] = (pdu[2] << 8) | pdu[3]
            else:
                result["errors"].append(f"Invalid response length for function 15: expected 4 bytes, got {len(pdu)}")
                
        else:
            result["errors"].append(f"Unsupported function code: 0x{function_code:02X}")
        
        return result