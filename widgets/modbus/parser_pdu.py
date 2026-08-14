# widgets/modbus/parser_pdu.py
# Python 3.11+, PyQt6

from typing import Dict, Any, List, Optional
from widgets.modbus.constants import FUNCTION_NAMES, EXCEPTION_CODES, get_original_function


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
        
        if function_code == 3:  # Read Holding Registers
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
                result["errors"].append(f"Invalid PDU length for function 03: expected 4 bytes, got {len(pdu)}")
        
        elif function_code == 4:  # Read Input Registers
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
                result["errors"].append(f"Invalid PDU length for function 04: expected 4 bytes, got {len(pdu)}")
                
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
                
        elif function_code == 6:
            if len(pdu) == 4:
                result["start_address"] = (pdu[0] << 8) | pdu[1]
                result["value"] = (pdu[2] << 8) | pdu[3]
                result["start_address_desc"] = cls.FIELD_DESCRIPTIONS["start_address"]
                result["value_desc"] = cls.FIELD_DESCRIPTIONS["value"]
            else:
                result["errors"].append(f"Invalid response length for function 06: expected 4 bytes, got {len(pdu)}")
                
        elif function_code == 16:
            if len(pdu) == 4:
                result["start_address"] = (pdu[0] << 8) | pdu[1]
                result["quantity"] = (pdu[2] << 8) | pdu[3]
                result["start_address_desc"] = cls.FIELD_DESCRIPTIONS["start_address"]
                result["quantity_desc"] = cls.FIELD_DESCRIPTIONS["quantity"]
            else:
                result["errors"].append(f"Invalid response length for function 16: expected 4 bytes, got {len(pdu)}")
                
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
                
        elif function_code == 5:
            if len(pdu) == 4:
                result["start_address"] = (pdu[0] << 8) | pdu[1]
                result["value"] = (pdu[2] << 8) | pdu[3]
                result["start_address_desc"] = cls.FIELD_DESCRIPTIONS["start_address"]
                result["value_desc"] = cls.FIELD_DESCRIPTIONS["value"]
            else:
                result["errors"].append(f"Invalid response length for function 05: expected 4 bytes, got {len(pdu)}")
                
        elif function_code == 15:
            if len(pdu) == 4:
                result["start_address"] = (pdu[0] << 8) | pdu[1]
                result["quantity"] = (pdu[2] << 8) | pdu[3]
                result["start_address_desc"] = cls.FIELD_DESCRIPTIONS["start_address"]
                result["quantity_desc"] = cls.FIELD_DESCRIPTIONS["quantity"]
            else:
                result["errors"].append(f"Invalid response length for function 15: expected 4 bytes, got {len(pdu)}")
                
        else:
            result["errors"].append(f"Unsupported function code: 0x{function_code:02X}")
        
        return result


    @classmethod
    def get_display_groups(cls, result: Dict[str, Any], is_tcp: bool, is_response: bool) -> List[Dict[str, Any]]:
        """
        Возвращает список групп для отображения в Raw Data.
        Каждая группа: {"label": str, "bytes": str, "color": str}
        """
        groups = []
        func = result.get("function_code")
        protocol = result.get("protocol", "")
        
        # ========== ASCII ==========
        if protocol == "ASCII":
            groups.append({"label": "Start", "bytes": "3A", "color": "header"})
            
            slave = result.get("slave_address")
            if slave is not None:
                groups.append({"label": "Slave ID", "bytes": f"{slave:02X}", "color": "unit"})
            
            if func is not None:
                groups.append({"label": "Function Code", "bytes": f"{func:02X}", "color": "function"})
            
            # PDU часть
            if is_response:
                if func in [3, 4]:
                    byte_count = result.get("byte_count", 0)
                    groups.append({"label": "Byte Count", "bytes": f"{byte_count:02X}", "color": "byte_count"})
                    registers = result.get("registers", [])
                    for reg in registers:
                        groups.append({"label": "Register", "bytes": f"{reg:04X}", "color": "register"})
                elif func == 6:
                    addr = result.get("start_address", 0)
                    groups.append({"label": "Start Address", "bytes": f"{addr:04X}", "color": "address"})
                    val = result.get("value", 0)
                    groups.append({"label": "Value", "bytes": f"{val:04X}", "color": "register"})
                elif func == 16:
                    addr = result.get("start_address", 0)
                    groups.append({"label": "Start Address", "bytes": f"{addr:04X}", "color": "address"})
                    qty = result.get("quantity", 0)
                    groups.append({"label": "Quantity", "bytes": f"{qty:04X}", "color": "quantity"})
                elif func in [1, 2]:
                    byte_count = result.get("byte_count", 0)
                    groups.append({"label": "Byte Count", "bytes": f"{byte_count:02X}", "color": "byte_count"})
                    if result.get("bits"):
                        bits_str = "".join([str(b) for b in result["bits"][:8]])
                        groups.append({"label": "Bits", "bytes": bits_str, "color": "default"})
                elif func == 5:
                    addr = result.get("start_address", 0)
                    groups.append({"label": "Start Address", "bytes": f"{addr:04X}", "color": "address"})
                    val = result.get("value", 0)
                    groups.append({"label": "Value", "bytes": f"{val:04X}", "color": "register"})
                elif func == 15:
                    addr = result.get("start_address", 0)
                    groups.append({"label": "Start Address", "bytes": f"{addr:04X}", "color": "address"})
                    qty = result.get("quantity", 0)
                    groups.append({"label": "Quantity", "bytes": f"{qty:04X}", "color": "quantity"})
                elif func is not None and (func & 0x80):
                    if "exception_code" in result:
                        groups.append({"label": "Exception Code", "bytes": f"{result['exception_code']:02X}", "color": "crc"})
            else:
                if func in [3, 4, 1, 2]:
                    addr = result.get("start_address", 0)
                    groups.append({"label": "Start Address", "bytes": f"{addr:04X}", "color": "address"})
                    qty = result.get("quantity", 0)
                    groups.append({"label": "Quantity", "bytes": f"{qty:04X}", "color": "quantity"})
                elif func in [6, 5]:
                    addr = result.get("start_address", 0)
                    groups.append({"label": "Start Address", "bytes": f"{addr:04X}", "color": "address"})
                    val = result.get("value", 0)
                    groups.append({"label": "Value", "bytes": f"{val:04X}", "color": "register"})
                elif func in [16, 15]:
                    addr = result.get("start_address", 0)
                    groups.append({"label": "Start Address", "bytes": f"{addr:04X}", "color": "address"})
                    qty = result.get("quantity", 0)
                    groups.append({"label": "Quantity", "bytes": f"{qty:04X}", "color": "quantity"})
                    byte_count = result.get("byte_count", 0)
                    groups.append({"label": "Byte Count", "bytes": f"{byte_count:02X}", "color": "byte_count"})
                    registers = result.get("registers", [])
                    for reg in registers:
                        groups.append({"label": "Register", "bytes": f"{reg:04X}", "color": "register"})
                elif func is not None and (func & 0x80):
                    if "exception_code" in result:
                        groups.append({"label": "Exception Code", "bytes": f"{result['exception_code']:02X}", "color": "crc"})
            
            if "lrc_received" in result:
                lrc_val = int(result["lrc_received"], 16)
                groups.append({"label": "LRC", "bytes": f"{lrc_val:02X}", "color": "lrc"})
            
            groups.append({"label": "End", "bytes": "0D0A", "color": "default"})
            
            return groups
        
        # ========== TCP ==========
        if is_tcp:
            tid = result.get("transaction_id", 0)
            groups.append({"label": "Transaction ID", "bytes": f"{tid:04X}", "color": "transaction"})
            groups.append({"label": "Protocol ID", "bytes": "0000", "color": "protocol"})
            length = result.get("length", 0)
            groups.append({"label": "Length", "bytes": f"{length:04X}", "color": "length"})
            unit = result.get("unit_id", 0)
            groups.append({"label": "Unit ID", "bytes": f"{unit:02X}", "color": "unit"})
        
        # ========== Function Code ==========
        if func is not None:
            groups.append({"label": "Function Code", "bytes": f"{func:02X}", "color": "function"})
        else:
            return groups
        
        # ========== RTU ==========
        if protocol == "RTU":
            # 1. Slave Address (уже добавлен выше, но его нет, т.к. RTU отдельно)
            slave = result.get("slave_address")
            if slave is not None:
                # Вставляем Slave Address перед Function Code
                # Так как groups уже содержит Function Code, нужно переставить
                # Проще собрать заново
                groups = []
                groups.append({"label": "Slave ID", "bytes": f"{slave:02X}", "color": "unit"})
                if func is not None:
                    groups.append({"label": "Function Code", "bytes": f"{func:02X}", "color": "function"})
            else:
                if func is not None:
                    groups = [{"label": "Function Code", "bytes": f"{func:02X}", "color": "function"}]
            
            # PDU
            if is_response:
                if func in [3, 4]:
                    byte_count = result.get("byte_count", 0)
                    groups.append({"label": "Byte Count", "bytes": f"{byte_count:02X}", "color": "byte_count"})
                    registers = result.get("registers", [])
                    for reg in registers:
                        groups.append({"label": "Register", "bytes": f"{reg:04X}", "color": "register"})
                elif func == 6:
                    addr = result.get("start_address", 0)
                    groups.append({"label": "Start Address", "bytes": f"{addr:04X}", "color": "address"})
                    val = result.get("value", 0)
                    groups.append({"label": "Value", "bytes": f"{val:04X}", "color": "register"})
                elif func == 16:
                    addr = result.get("start_address", 0)
                    groups.append({"label": "Start Address", "bytes": f"{addr:04X}", "color": "address"})
                    qty = result.get("quantity", 0)
                    groups.append({"label": "Quantity", "bytes": f"{qty:04X}", "color": "quantity"})
                elif func in [1, 2]:
                    byte_count = result.get("byte_count", 0)
                    groups.append({"label": "Byte Count", "bytes": f"{byte_count:02X}", "color": "byte_count"})
                    if result.get("bits"):
                        bits_str = "".join([str(b) for b in result["bits"][:8]])
                        groups.append({"label": "Bits", "bytes": bits_str, "color": "default"})
                elif func == 5:
                    addr = result.get("start_address", 0)
                    groups.append({"label": "Start Address", "bytes": f"{addr:04X}", "color": "address"})
                    val = result.get("value", 0)
                    groups.append({"label": "Value", "bytes": f"{val:04X}", "color": "register"})
                elif func == 15:
                    addr = result.get("start_address", 0)
                    groups.append({"label": "Start Address", "bytes": f"{addr:04X}", "color": "address"})
                    qty = result.get("quantity", 0)
                    groups.append({"label": "Quantity", "bytes": f"{qty:04X}", "color": "quantity"})
                elif func is not None and (func & 0x80):
                    if "exception_code" in result:
                        groups.append({"label": "Exception Code", "bytes": f"{result['exception_code']:02X}", "color": "crc"})
            else:
                if func in [3, 4, 1, 2]:
                    addr = result.get("start_address", 0)
                    groups.append({"label": "Start Address", "bytes": f"{addr:04X}", "color": "address"})
                    qty = result.get("quantity", 0)
                    groups.append({"label": "Quantity", "bytes": f"{qty:04X}", "color": "quantity"})
                elif func in [6, 5]:
                    addr = result.get("start_address", 0)
                    groups.append({"label": "Start Address", "bytes": f"{addr:04X}", "color": "address"})
                    val = result.get("value", 0)
                    groups.append({"label": "Value", "bytes": f"{val:04X}", "color": "register"})
                elif func in [16, 15]:
                    addr = result.get("start_address", 0)
                    groups.append({"label": "Start Address", "bytes": f"{addr:04X}", "color": "address"})
                    qty = result.get("quantity", 0)
                    groups.append({"label": "Quantity", "bytes": f"{qty:04X}", "color": "quantity"})
                    byte_count = result.get("byte_count", 0)
                    groups.append({"label": "Byte Count", "bytes": f"{byte_count:02X}", "color": "byte_count"})
                    registers = result.get("registers", [])
                    for reg in registers:
                        groups.append({"label": "Register", "bytes": f"{reg:04X}", "color": "register"})
                elif func is not None and (func & 0x80):
                    if "exception_code" in result:
                        groups.append({"label": "Exception Code", "bytes": f"{result['exception_code']:02X}", "color": "crc"})
            
            # CRC
            if "crc_received" in result:
                crc_val = int(result["crc_received"], 16)
                groups.append({"label": "CRC", "bytes": f"{crc_val:04X}", "color": "crc"})
            
            return groups
        
        # ========== TCP PDU ==========
        if is_response:
            if func in [3, 4]:
                byte_count = result.get("byte_count", 0)
                groups.append({"label": "Byte Count", "bytes": f"{byte_count:02X}", "color": "byte_count"})
                registers = result.get("registers", [])
                for reg in registers:
                    groups.append({"label": "Register", "bytes": f"{reg:04X}", "color": "register"})
            elif func == 6:
                addr = result.get("start_address", 0)
                groups.append({"label": "Start Address", "bytes": f"{addr:04X}", "color": "address"})
                val = result.get("value", 0)
                groups.append({"label": "Value", "bytes": f"{val:04X}", "color": "register"})
            elif func == 16:
                addr = result.get("start_address", 0)
                groups.append({"label": "Start Address", "bytes": f"{addr:04X}", "color": "address"})
                qty = result.get("quantity", 0)
                groups.append({"label": "Quantity", "bytes": f"{qty:04X}", "color": "quantity"})
            elif func in [1, 2]:
                byte_count = result.get("byte_count", 0)
                groups.append({"label": "Byte Count", "bytes": f"{byte_count:02X}", "color": "byte_count"})
                if result.get("bits"):
                    bits_str = "".join([str(b) for b in result["bits"][:8]])
                    groups.append({"label": "Bits", "bytes": bits_str, "color": "default"})
            elif func == 5:
                addr = result.get("start_address", 0)
                groups.append({"label": "Start Address", "bytes": f"{addr:04X}", "color": "address"})
                val = result.get("value", 0)
                groups.append({"label": "Value", "bytes": f"{val:04X}", "color": "register"})
            elif func == 15:
                addr = result.get("start_address", 0)
                groups.append({"label": "Start Address", "bytes": f"{addr:04X}", "color": "address"})
                qty = result.get("quantity", 0)
                groups.append({"label": "Quantity", "bytes": f"{qty:04X}", "color": "quantity"})
            elif func is not None and (func & 0x80):
                if "exception_code" in result:
                    groups.append({"label": "Exception Code", "bytes": f"{result['exception_code']:02X}", "color": "crc"})
        else:
            if func in [3, 4, 1, 2]:
                addr = result.get("start_address", 0)
                groups.append({"label": "Start Address", "bytes": f"{addr:04X}", "color": "address"})
                qty = result.get("quantity", 0)
                groups.append({"label": "Quantity", "bytes": f"{qty:04X}", "color": "quantity"})
            elif func in [6, 5]:
                addr = result.get("start_address", 0)
                groups.append({"label": "Start Address", "bytes": f"{addr:04X}", "color": "address"})
                val = result.get("value", 0)
                groups.append({"label": "Value", "bytes": f"{val:04X}", "color": "register"})
            elif func in [16, 15]:
                addr = result.get("start_address", 0)
                groups.append({"label": "Start Address", "bytes": f"{addr:04X}", "color": "address"})
                qty = result.get("quantity", 0)
                groups.append({"label": "Quantity", "bytes": f"{qty:04X}", "color": "quantity"})
                byte_count = result.get("byte_count", 0)
                groups.append({"label": "Byte Count", "bytes": f"{byte_count:02X}", "color": "byte_count"})
                registers = result.get("registers", [])
                for reg in registers:
                    groups.append({"label": "Register", "bytes": f"{reg:04X}", "color": "register"})
            elif func is not None and (func & 0x80):
                if "exception_code" in result:
                    groups.append({"label": "Exception Code", "bytes": f"{result['exception_code']:02X}", "color": "crc"})
        
        return groups





