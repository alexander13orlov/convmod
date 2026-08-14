# widgets/modbus/modbus_parser.py
# Python 3.11+, PyQt6

import logging
from typing import Dict, Any, Optional
from widgets.modbus.parser_tcp import TCPParser
from widgets.modbus.parser_rtu import RTUParser
from widgets.modbus.parser_ascii import ASCIJParser
from widgets.modbus.parser_pdu import PDUParser

logger = logging.getLogger(__name__)


class ModbusParser:
    
    @classmethod
    def parse(cls, text: str, protocol: str, is_response: bool) -> Dict[str, Any]:
        clean = text.strip().replace(' ', '').replace('\n', '').replace('\r', '')
        if not clean:
            return {"valid": False, "errors": ["Empty input"], "warnings": []}

        protocol_upper = protocol.upper()
        
        try:
            if protocol_upper == "ASCII":
                result = ASCIJParser.parse(clean.encode('ascii'), is_response)
            elif protocol_upper == "RTU":
                result = RTUParser.parse(bytes.fromhex(clean), is_response)
            elif protocol_upper == "TCP":
                result = TCPParser.parse(bytes.fromhex(clean), is_response)
            else:
                return {"valid": False, "errors": [f"Unknown protocol: {protocol}"], "warnings": []}
            
            if "warnings" not in result:
                result["warnings"] = []
            return result
            
        except ValueError as e:
            return {"valid": False, "errors": [f"Invalid hex: {str(e)}"], "warnings": []}
        except Exception as e:
            logger.exception("Parse error")
            return {"valid": False, "errors": [f"Parse error: {str(e)}"], "warnings": []}
    
    @classmethod
    def parse_rtu_with_options(cls, text: str, is_response: bool, 
                                include_slave: bool = True, 
                                include_crc: bool = True) -> Dict[str, Any]:
        clean = text.strip().replace(' ', '').replace('\n', '').replace('\r', '')
        if not clean:
            return {"valid": False, "errors": ["Empty input"], "warnings": []}
        
        try:
            data = bytes.fromhex(clean)
        except ValueError as e:
            return {"valid": False, "errors": [f"Invalid hex: {str(e)}"], "warnings": []}
        
        original_data = clean
        result = {"protocol": "RTU", "valid": False, "errors": [], "warnings": []}
        
        data_index = 0
        
        if include_slave:
            if len(data) < 1:
                result["errors"].append("Data too short for Slave ID")
                result["settings"] = {"slave_id_included": include_slave, "crc_included": include_crc}
                result["original_raw"] = original_data
                result["structure_valid"] = False
                return result
            result["slave_address"] = data[0]
            data_index = 1
        else:
            result["slave_address"] = None
        
        if len(data) <= data_index:
            result["errors"].append("No function code")
            result["settings"] = {"slave_id_included": include_slave, "crc_included": include_crc}
            result["original_raw"] = original_data
            result["structure_valid"] = False
            return result
        
        result["function_code"] = data[data_index]
        data_index += 1
        
        pdu = data[data_index:] if len(data) > data_index else b''
        
        if include_crc:
            if len(pdu) < 2:
                result["errors"].append(f"Data too short for CRC: need at least 2 bytes, got {len(pdu)}")
                result["settings"] = {"slave_id_included": include_slave, "crc_included": include_crc}
                result["original_raw"] = original_data
                result["structure_valid"] = False
                return result
            pdu_without_crc = pdu[:-2]
            msg_crc = (pdu[-1] << 8) | pdu[-2]
            result["crc_received"] = f"0x{msg_crc:04X}"
            
            if include_slave:
                bytes_for_crc = data[:data_index] + pdu_without_crc
                calc_crc = RTUParser.crc16(bytes_for_crc)
                result["crc_calculated"] = f"0x{calc_crc:04X}"
                result["crc_valid"] = msg_crc == calc_crc
                if not result["crc_valid"]:
                    result["errors"].append("CRC mismatch")
            else:
                result["crc_calculated"] = "Unknown (Slave ID missing)"
                result["crc_valid"] = None
                result["errors"].append("CRC cannot be verified: Slave ID not provided")
            
            pdu = pdu_without_crc
        
        if is_response:
            pdu_result = PDUParser.parse_response(result["function_code"], pdu)
        else:
            pdu_result = PDUParser.parse_request(result["function_code"], pdu)
        
        result.update(pdu_result)
        
        if pdu_result.get("errors"):
            result["errors"].extend(pdu_result["errors"])
        
        # Добавляем предупреждения из PDU
        if pdu_result.get("warnings"):
            if "warnings" not in result:
                result["warnings"] = []
            result["warnings"].extend(pdu_result["warnings"])
        
        result["settings"] = {
            "slave_id_included": include_slave,
            "crc_included": include_crc
        }
        
        result["original_raw"] = original_data
        
        structure_valid = len([e for e in result["errors"] if "CRC" not in e]) == 0
        result["structure_valid"] = structure_valid
        result["valid"] = structure_valid
        
        return result