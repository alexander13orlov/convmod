# debug_crc.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from widgets.modbus.parser_rtu import RTUParser

# Данные без CRC: 01 83 02
data = bytes.fromhex("018302")
crc = RTUParser.crc16(data)
print(f"CRC for 018302: 0x{crc:04X}")
print(f"CRC bytes (low-high): {crc & 0xFF:02X} {(crc >> 8) & 0xFF:02X}")
