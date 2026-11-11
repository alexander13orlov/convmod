# widgets/modbus/parser_pdu.py
# Python 3.11+, PyQt6

from typing import Dict, Any
from widgets.modbus.constants import FUNCTION_NAMES, EXCEPTION_CODES, get_original_function


def merge_pdu_result(result: Dict[str, Any], pdu_result: Dict[str, Any]) -> None:
    """Объединяет результат разбора PDU с result.

    errors и warnings дописываются к существующим спискам (чтобы
    протокольные ошибки, например CRC mismatch, не терялись),
    остальные поля записываются как есть.
    """
    for key, value in pdu_result.items():
        if key == "errors":
            result.setdefault("errors", []).extend(value)
        elif key == "warnings":
            result.setdefault("warnings", []).extend(value)
        else:
            result[key] = value


class PDUParser:
    """Парсер PDU (Protocol Data Unit) - общая часть для всех протоколов"""
    
    # Пояснения для полей
    FIELD_DESCRIPTIONS = {
        "function_code": "Modbus function code",
        "start_address": "Starting register/coil address (0-based)",
        "quantity": "Number of registers/coils to read/write",
        "byte_count": "Number of data bytes following",
        "value": "Value to write",
        "register": "Register value (16-bit)",
        "exception_code": "Exception code (see EXCEPTION_CODES)",
    }
    
    @classmethod
    def parse_request(cls, function_code: int, pdu: bytes) -> Dict[str, Any]:
        result = {
            "function_code": function_code,
            "function_name": FUNCTION_NAMES.get(function_code, f"Unknown (0x{function_code:02X})"),
            "is_exception": False,
            "errors": [],
            "warnings": []
        }
        
        result["function_code_desc"] = cls.FIELD_DESCRIPTIONS["function_code"]
        
        if function_code & 0x80:
            result["errors"].append(f"Invalid request: function code 0x{function_code:02X} has exception bit set")
            result["function_name"] = "INVALID"
            return result
        
        if function_code in (3, 4):  # Read Holding Registers / Read Input Registers
            if len(pdu) == 4:
                result["start_address"] = (pdu[0] << 8) | pdu[1]
                result["quantity"] = (pdu[2] << 8) | pdu[3]
                result["start_address_desc"] = cls.FIELD_DESCRIPTIONS["start_address"]
                result["quantity_desc"] = cls.FIELD_DESCRIPTIONS["quantity"]
                if result["quantity"] == 0:
                    result["warnings"].append("Quantity is 0 - no registers to read")
                if result["quantity"] > 125:
                    result["warnings"].append(f"Quantity {result['quantity']} exceeds typical maximum (125 registers)")
            else:
                result["errors"].append(f"Invalid PDU length for function {function_code:02X}: expected 4 bytes, got {len(pdu)}")

                
        elif function_code == 6:  # Write Single Register
            if len(pdu) == 4:
                result["start_address"] = (pdu[0] << 8) | pdu[1]
                result["value"] = (pdu[2] << 8) | pdu[3]
                result["start_address_desc"] = cls.FIELD_DESCRIPTIONS["start_address"]
                result["value_desc"] = cls.FIELD_DESCRIPTIONS["value"]
            else:
                result["errors"].append(f"Invalid PDU length for function 06: expected 4 bytes, got {len(pdu)}")
                
        elif function_code == 16:  # Write Multiple Registers
            if len(pdu) >= 5:
                result["start_address"] = (pdu[0] << 8) | pdu[1]
                result["quantity"] = (pdu[2] << 8) | pdu[3]
                result["byte_count"] = pdu[4]
                result["start_address_desc"] = cls.FIELD_DESCRIPTIONS["start_address"]
                result["quantity_desc"] = cls.FIELD_DESCRIPTIONS["quantity"]
                result["byte_count_desc"] = cls.FIELD_DESCRIPTIONS["byte_count"]
                expected_data_len = result["byte_count"]
                if result["quantity"] == 0:
                    result["warnings"].append("Quantity is 0 - no registers to write")
                if len(pdu) == 5 + expected_data_len:
                    result["data_bytes"] = pdu[5:5+expected_data_len]
                    result["registers"] = []
                    for i in range(0, expected_data_len, 2):
                        if i+1 < expected_data_len:
                            val = (result["data_bytes"][i] << 8) | result["data_bytes"][i+1]
                            result["registers"].append(val)
                    result["registers_desc"] = "Register values (16-bit each)"
                else:
                    result["errors"].append(f"Invalid PDU length for function 16: expected 5 + {expected_data_len} bytes, got {len(pdu)}")
            else:
                result["errors"].append(f"Invalid PDU length for function 16: need at least 5 bytes, got {len(pdu)}")
                
        elif function_code == 1 or function_code == 2:  # Read Coils / Read Discrete Inputs
            if len(pdu) == 4:
                result["start_address"] = (pdu[0] << 8) | pdu[1]
                result["quantity"] = (pdu[2] << 8) | pdu[3]
                result["start_address_desc"] = cls.FIELD_DESCRIPTIONS["start_address"]
                result["quantity_desc"] = cls.FIELD_DESCRIPTIONS["quantity"]
                if result["quantity"] == 0:
                    result["warnings"].append("Quantity is 0 - no coils to read")
                if result["quantity"] > 2000:
                    result["warnings"].append(f"Quantity {result['quantity']} exceeds typical maximum (2000 coils)")
            else:
                result["errors"].append(f"Invalid PDU length for function {function_code:02X}: expected 4 bytes, got {len(pdu)}")
                
        elif function_code == 5:  # Write Single Coil
            if len(pdu) == 4:
                result["start_address"] = (pdu[0] << 8) | pdu[1]
                result["value"] = (pdu[2] << 8) | pdu[3]
                result["start_address_desc"] = cls.FIELD_DESCRIPTIONS["start_address"]
                result["value_desc"] = cls.FIELD_DESCRIPTIONS["value"]
                if result["value"] not in [0x0000, 0xFF00]:
                    result["warnings"].append(f"Invalid coil value: 0x{result['value']:04X} (should be 0x0000 or 0xFF00)")
            else:
                result["errors"].append(f"Invalid PDU length for function 05: expected 4 bytes, got {len(pdu)}")
                
        elif function_code == 15:  # Write Multiple Coils
            if len(pdu) >= 5:
                result["start_address"] = (pdu[0] << 8) | pdu[1]
                result["quantity"] = (pdu[2] << 8) | pdu[3]
                result["byte_count"] = pdu[4]
                result["start_address_desc"] = cls.FIELD_DESCRIPTIONS["start_address"]
                result["quantity_desc"] = cls.FIELD_DESCRIPTIONS["quantity"]
                result["byte_count_desc"] = cls.FIELD_DESCRIPTIONS["byte_count"]
                if result["quantity"] == 0:
                    result["warnings"].append("Quantity is 0 - no coils to write")
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
            "errors": [],
            "warnings": []
        }
        
        result["function_code_desc"] = cls.FIELD_DESCRIPTIONS["function_code"]
        
        if function_code & 0x80:
            original = get_original_function(function_code)
            result["function_name"] = f"EXCEPTION RESPONSE (Function {original:02X}: {FUNCTION_NAMES.get(original, 'Unknown')})"
            result["is_exception"] = True
            result["original_function_code"] = original
            
            if len(pdu) == 1:
                result["exception_code"] = pdu[0]
                result["exception_description"] = EXCEPTION_CODES.get(pdu[0], f"Unknown: 0x{pdu[0]:02X}")
                result["exception_code_desc"] = "Exception code (see EXCEPTION_CODES)"
            else:
                result["errors"].append(f"Invalid exception response length: expected 1 byte, got {len(pdu)}")
            return result
        
        result["function_name"] = FUNCTION_NAMES.get(function_code, f"Unknown (0x{function_code:02X})")
        
        if function_code == 3 or function_code == 4:  # Read Holding Registers or Read Input Registers
            if len(pdu) >= 1:
                result["byte_count"] = pdu[0]
                result["byte_count_desc"] = cls.FIELD_DESCRIPTIONS["byte_count"]
                expected = result["byte_count"]
                if expected > 250:
                    result["warnings"].append(f"Byte count {expected} exceeds typical maximum (250 bytes = 125 registers)")
                if len(pdu) == 1 + expected:
                    result["data_bytes"] = pdu[1:1+expected]
                    result["registers"] = []
                    for i in range(0, expected, 2):
                        if i+1 < expected:
                            val = (result["data_bytes"][i] << 8) | result["data_bytes"][i+1]
                            result["registers"].append(val)
                    result["quantity"] = expected // 2
                    result["quantity_desc"] = "Number of registers returned"
                    result["registers_desc"] = "Register values (16-bit each)"
                else:
                    result["errors"].append(f"Invalid response length for function {function_code:02X}: expected 1 + {expected} bytes, got {len(pdu)}")
            else:
                result["errors"].append(f"Response too short for function {function_code:02X}: need at least 1 byte, got {len(pdu)}")
                
        elif function_code in (5, 6):
            if len(pdu) == 4:
                result["start_address"] = (pdu[0] << 8) | pdu[1]
                result["value"] = (pdu[2] << 8) | pdu[3]
                result["start_address_desc"] = cls.FIELD_DESCRIPTIONS["start_address"]
                result["value_desc"] = cls.FIELD_DESCRIPTIONS["value"]
            else:
                result["errors"].append(f"Invalid response length for function {function_code:02X}: expected 4 bytes, got {len(pdu)}")
                
        elif function_code in (15, 16):
            if len(pdu) == 4:
                result["start_address"] = (pdu[0] << 8) | pdu[1]
                result["quantity"] = (pdu[2] << 8) | pdu[3]
                result["start_address_desc"] = cls.FIELD_DESCRIPTIONS["start_address"]
                result["quantity_desc"] = cls.FIELD_DESCRIPTIONS["quantity"]
            else:
                result["errors"].append(f"Invalid response length for function {function_code:02X}: expected 4 bytes, got {len(pdu)}")
                
        elif function_code == 1 or function_code == 2:
            if len(pdu) >= 1:
                result["byte_count"] = pdu[0]
                result["byte_count_desc"] = cls.FIELD_DESCRIPTIONS["byte_count"]
                expected = result["byte_count"]
                if len(pdu) == 1 + expected:
                    result["data_bytes"] = pdu[1:1+expected]
                    result["bits"] = []
                    for byte in result["data_bytes"]:
                        for bit in range(8):
                            result["bits"].append((byte >> bit) & 1)
                    result["quantity"] = expected * 8
                    result["quantity_desc"] = "Number of coils returned"
                else:
                    result["errors"].append(f"Invalid response length for function {function_code:02X}: expected 1 + {expected} bytes, got {len(pdu)}")
            else:
                result["errors"].append(f"Response too short for function {function_code:02X}: need at least 1 byte, got {len(pdu)}")


                
        else:
            result["errors"].append(f"Unsupported function code: 0x{function_code:02X}")
        
        return result
