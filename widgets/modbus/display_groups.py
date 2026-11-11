# widgets/modbus/display_groups.py
# Python 3.11+, PyQt6

from typing import Dict, Any, List


class DisplayGroups:
    """Формирует группы байтов для отображения в Raw Data (HEX).

    Каждая группа: {"label": str, "bytes": str, "color": str}.
    Байты PDU не зависят от протокола — для TCP/RTU/ASCII различается
    только обрамление кадра (MBAP, Slave/CRC, 3A/LRC/0D0A).
    """

    @classmethod
    def build(cls, result: Dict[str, Any], is_tcp: bool, is_response: bool) -> List[Dict[str, Any]]:
        """Возвращает список групп для отображения в Raw Data."""
        groups: List[Dict[str, Any]] = []
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

            groups.extend(cls._pdu_groups(result, is_response))

            if "lrc_received" in result:
                lrc_val = int(result["lrc_received"], 16)
                groups.append({"label": "LRC", "bytes": f"{lrc_val:02X}", "color": "lrc"})

            groups.append({"label": "End", "bytes": "0D0A", "color": "default"})

            return groups

        # ========== TCP (MBAP) ==========
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
            slave = result.get("slave_address")
            if slave is not None:
                groups = []
                groups.append({"label": "Slave ID", "bytes": f"{slave:02X}", "color": "unit"})
                groups.append({"label": "Function Code", "bytes": f"{func:02X}", "color": "function"})
            else:
                groups = [{"label": "Function Code", "bytes": f"{func:02X}", "color": "function"}]

            groups.extend(cls._pdu_groups(result, is_response))

            if "crc_received" in result:
                crc_val = int(result["crc_received"], 16)
                groups.append({"label": "CRC", "bytes": f"{crc_val:04X}", "color": "crc"})

            return groups

        # ========== TCP PDU ==========
        groups.extend(cls._pdu_groups(result, is_response))

        return groups

    @classmethod
    def _pdu_groups(cls, result: Dict[str, Any], is_response: bool) -> List[Dict[str, Any]]:
        """Общая для всех протоколов часть групп: байты PDU."""
        groups: List[Dict[str, Any]] = []
        func = result.get("function_code")

        if is_response:
            if func in [3, 4]:
                byte_count = result.get("byte_count", 0)
                groups.append({"label": "Byte Count", "bytes": f"{byte_count:02X}", "color": "byte_count"})
                for reg in result.get("registers", []):
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
                for db in result.get("data_bytes") or b"":
                    groups.append({"label": "Data", "bytes": f"{db:02X}", "color": "register"})
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
                for reg in result.get("registers", []):
                    groups.append({"label": "Register", "bytes": f"{reg:04X}", "color": "register"})
            elif func is not None and (func & 0x80):
                if "exception_code" in result:
                    groups.append({"label": "Exception Code", "bytes": f"{result['exception_code']:02X}", "color": "crc"})

        return groups
