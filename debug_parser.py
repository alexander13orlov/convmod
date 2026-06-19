# debug_parser.py
# Python 3.11+, PyQt6

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from widgets.modbus.modbus_parser import ModbusParser

parser = ModbusParser()

print("=" * 60)
print("RTU TESTS")
print("=" * 60)

# RTU Read Holding Registers Request с правильным CRC (C7 3D)
test_data = "01030FA00002C73D"
print(f"\nRTU Request: {test_data}")
result = parser.parse(test_data, "RTU", False)
print(f"Valid: {result.get('valid')}")
print(f"Errors: {result.get('errors')}")
if result.get('valid'):
    print(f"Start Address: {result.get('start_address')}")
    print(f"Quantity: {result.get('quantity')}")

# RTU Read Holding Registers Response с правильным CRC (0B F3)
test_data = "010304000700030BF3"
print(f"\nRTU Response: {test_data}")
result = parser.parse(test_data, "RTU", True)
print(f"Valid: {result.get('valid')}")
print(f"Errors: {result.get('errors')}")
if result.get('valid'):
    print(f"Registers: {result.get('registers')}")

# RTU Write Single Register Request с правильным CRC (19 CA)
test_data = "01060001000119CA"
print(f"\nRTU Write Request: {test_data}")
result = parser.parse(test_data, "RTU", False)
print(f"Valid: {result.get('valid')}")
print(f"Errors: {result.get('errors')}")
if result.get('valid'):
    print(f"Start Address: {result.get('start_address')}")
    print(f"Value: {result.get('value')}")

print("\n" + "=" * 60)
print("ASCII TESTS")
print("=" * 60)

# ASCII Read Holding Registers Request с правильным LRC (4B)
test_data = ":01030FA000024B\r\n"
print(f"\nASCII Request: {repr(test_data)}")
result = parser.parse(test_data, "ASCII", False)
print(f"Valid: {result.get('valid')}")
print(f"Errors: {result.get('errors')}")
if result.get('valid'):
    print(f"Start Address: {result.get('start_address')}")
    print(f"Quantity: {result.get('quantity')}")

# ASCII Read Holding Registers Response с правильным LRC (EE)
test_data = ":01030400070003EE\r\n"
print(f"\nASCII Response: {repr(test_data)}")
result = parser.parse(test_data, "ASCII", True)
print(f"Valid: {result.get('valid')}")
print(f"Errors: {result.get('errors')}")
if result.get('valid'):
    print(f"Registers: {result.get('registers')}")

# ASCII Exception с правильным LRC (7A)
test_data = ":0183027A\r\n"
print(f"\nASCII Exception: {repr(test_data)}")
result = parser.parse(test_data, "ASCII", True)
print(f"Valid: {result.get('valid')}")
print(f"Errors: {result.get('errors')}")
if result.get('valid'):
    print(f"Exception Code: {result.get('exception_code')}")
    print(f"Exception Description: {result.get('exception_description')}")

print("\n" + "=" * 60)
print("TCP TESTS")
print("=" * 60)

test_data = "03E50000000601030FA00002"
print(f"\nTCP Request: {test_data}")
result = parser.parse(test_data, "TCP", False)
print(f"Valid: {result.get('valid')}")
print(f"Errors: {result.get('errors')}")
if result.get('valid'):
    print(f"Start Address: {result.get('start_address')}")
    print(f"Quantity: {result.get('quantity')}")