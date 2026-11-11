# widgets/modbus/constants.py
# Python 3.11+, PyQt6

FUNCTION_NAMES = {
    1: "Read Coils",
    2: "Read Discrete Inputs",
    3: "Read Holding Registers",
    4: "Read Input Registers",
    5: "Write Single Coil",
    6: "Write Single Register",
    7: "Read Exception Status",
    8: "Diagnostics",
    11: "Get Comm Event Counter",
    12: "Get Comm Event Log",
    15: "Write Multiple Coils",
    16: "Write Multiple Registers",
    17: "Report Server ID",
    20: "Read File Record",
    21: "Write File Record",
    22: "Mask Write Register",
    23: "Read/Write Multiple Registers",
    24: "Read FIFO Queue",
    43: "Read Device Identification",
}

EXCEPTION_CODES = {
    1: "ILLEGAL FUNCTION - Function code not supported by device",
    2: "ILLEGAL DATA ADDRESS - Address range exceeds device capacity or invalid address",
    3: "ILLEGAL DATA VALUE - Value written is invalid for this register",
    4: "SLAVE DEVICE FAILURE - Unrecoverable error occurred during execution",
    5: "ACKNOWLEDGE - Device accepted request but processing is pending",
    6: "SLAVE DEVICE BUSY - Device is busy processing another command",
    7: "NEGATIVE ACKNOWLEDGE - Programming error in the device",
    8: "MEMORY PARITY ERROR - Parity error in extended memory",
    10: "GATEWAY PATH UNAVAILABLE - Gateway path not available",
    11: "GATEWAY TARGET FAILED TO RESPOND - Target device did not respond",
}

def get_original_function(function_code: int) -> int:
    return function_code & 0x7F