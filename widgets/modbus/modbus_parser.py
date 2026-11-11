# widgets/modbus/modbus_parser.py (добавлена очистка raw_hex)
# Python 3.11+, PyQt6

import re
import logging
from typing import Dict, Any, Optional
from widgets.modbus.parser_tcp import TCPParser
from widgets.modbus.parser_rtu import RTUParser
from widgets.modbus.parser_ascii import ASCIJParser
from widgets.modbus.parser_pdu import PDUParser, merge_pdu_result

logger = logging.getLogger(__name__)

# Регулярное выражение для извлечения HEX символов
HEX_PATTERN = re.compile(r'[0-9A-Fa-f]')


class ModbusParser:
    
    @classmethod
    def _clean_hex(cls, text: str) -> str:
        """Извлекает только HEX символы из строки (0-9, A-F, a-f)"""
        return ''.join(HEX_PATTERN.findall(text))

    @staticmethod
    def _empty_result() -> Dict[str, Any]:
        """Результат для пустого входа (после очистки)."""
        return {"valid": False, "errors": ["Empty input"], "warnings": []}

    @classmethod
    def _rtu_error(cls, result: Dict[str, Any], error: str,
                   include_slave: bool, include_crc: bool, clean: str) -> Dict[str, Any]:
        """Ранний выход из разбора RTU: фиксирует ошибку и стандартные поля."""
        result["errors"].append(error)
        result["settings"] = {"slave_id_included": include_slave, "crc_included": include_crc}
        result["original_raw"] = clean
        result["raw_hex_clean"] = clean
        result["structure_valid"] = False
        return result
    
    @classmethod
    def parse(cls, text: str, protocol: str, is_response: bool) -> Dict[str, Any]:
        # Очищаем входную строку от всех не-HEX символов
        clean = cls._clean_hex(text)
        if not clean:
            return cls._empty_result()

        protocol_upper = protocol.upper()
        
        try:
            if protocol_upper == "ASCII":
                # Для ASCII сохраняем оригинальный формат с ':' и \r\n
                # Но HEX часть очищаем
                result = ASCIJParser.parse(text, is_response)
            elif protocol_upper == "RTU":
                result = RTUParser.parse(bytes.fromhex(clean), is_response)
            elif protocol_upper == "TCP":
                result = TCPParser.parse(bytes.fromhex(clean), is_response)
            else:
                return {"valid": False, "errors": [f"Unknown protocol: {protocol}"], "warnings": []}
            
            if "warnings" not in result:
                result["warnings"] = []
            # Сохраняем очищенный HEX для отображения
            result["raw_hex_clean"] = clean
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
        # Очищаем входную строку от всех не-HEX символов
        clean = cls._clean_hex(text)
        if not clean:
            return cls._empty_result()

        try:
            data = bytes.fromhex(clean)
        except ValueError as e:
            return {"valid": False, "errors": [f"Invalid hex: {str(e)}"], "warnings": []}
        
        result = {"protocol": "RTU", "valid": False, "errors": [], "warnings": []}
        
        data_index = 0
        
        if include_slave:
            if len(data) < 1:
                return cls._rtu_error(result, "Data too short for Slave ID", include_slave, include_crc, clean)
            result["slave_address"] = data[0]
            data_index = 1
        else:
            result["slave_address"] = None
        
        if len(data) <= data_index:
            return cls._rtu_error(result, "No function code", include_slave, include_crc, clean)
        
        result["function_code"] = data[data_index]
        data_index += 1
        
        pdu = data[data_index:] if len(data) > data_index else b''
        
        if include_crc:
            if len(pdu) < 2:
                return cls._rtu_error(result, f"Data too short for CRC: need at least 2 bytes, got {len(pdu)}",
                                      include_slave, include_crc, clean)
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
        
        merge_pdu_result(result, pdu_result)
        
        result["settings"] = {
            "slave_id_included": include_slave,
            "crc_included": include_crc
        }
        
        result["original_raw"] = clean
        result["raw_hex_clean"] = clean

        crc_markers = ("CRC mismatch", "CRC cannot be verified")
        structure_valid = all(
            any(marker in err for marker in crc_markers) for err in result["errors"]
        )
        result["structure_valid"] = structure_valid
        result["valid"] = structure_valid
        
        return result