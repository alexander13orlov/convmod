# widgets/modbus/validator.py
# Python 3.11+, PyQt6

from typing import Tuple, List
from widgets.modbus.constants import REQUEST_STRUCTURE, RESPONSE_STRUCTURE


class ModbusValidator:
    
    @classmethod
    def validate_request_pdu(cls, function_code: int, pdu_length: int) -> Tuple[bool, str]:
        if function_code not in REQUEST_STRUCTURE:
            return False, f"Unsupported function code: 0x{function_code:02X}"
        
        min_len, max_len, desc = REQUEST_STRUCTURE[function_code]
        
        if pdu_length < min_len:
            return False, f"Request PDU too short: expected >= {min_len} bytes, got {pdu_length} bytes"
        
        if pdu_length > max_len:
            return False, f"Request PDU too long: expected <= {max_len} bytes, got {pdu_length} bytes"
        
        return True, ""
    
    @classmethod
    def validate_response_pdu(cls, function_code: int, pdu_length: int) -> Tuple[bool, str]:
        if function_code not in RESPONSE_STRUCTURE:
            return False, f"Unsupported function code: 0x{function_code:02X}"
        
        min_len, max_len, desc = RESPONSE_STRUCTURE[function_code]
        
        if pdu_length < min_len:
            return False, f"Response PDU too short: expected >= {min_len} bytes, got {pdu_length} bytes"
        
        if pdu_length > max_len:
            return False, f"Response PDU too long: expected <= {max_len} bytes, got {pdu_length} bytes"
        
        return True, ""
    
    @classmethod
    def validate_exception_pdu(cls, pdu_length: int) -> Tuple[bool, str]:
        if pdu_length != 1:
            return False, f"Exception PDU should be 1 byte (exception code), got {pdu_length} bytes"
        return True, ""
    
    @classmethod
    def validate_tcp(cls, data: bytes, is_response: bool) -> Tuple[bool, List[str]]:
        errors = []
        
        if len(data) < 8:
            errors.append(f"Frame too short: {len(data)} bytes (min 8)")
            return False, errors
        
        length = (data[4] << 8) | data[5]
        pdu_size = len(data) - 7
        expected_length = 1 + pdu_size
        
        if length != expected_length:
            errors.append(f"Length mismatch: declared {length}, expected {expected_length}")
        
        if len(data) <= 7:
            errors.append("No PDU data")
            return False, errors
        
        return len(errors) == 0, errors