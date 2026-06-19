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
    8: "MEMORY PARITY ERROR - Parity error in extended memory",
    10: "GATEWAY PATH UNAVAILABLE - Gateway path not available",
    11: "GATEWAY TARGET FAILED TO RESPOND - Target device did not respond",
}

REQUEST_STRUCTURE = {
    1: (4, 4, "Read Coils: Address(2) + Quantity(2)"),
    2: (4, 4, "Read Discrete Inputs: Address(2) + Quantity(2)"),
    3: (4, 4, "Read Holding Registers: Address(2) + Quantity(2)"),
    4: (4, 4, "Read Input Registers: Address(2) + Quantity(2)"),
    5: (4, 4, "Write Single Coil: Address(2) + Value(2)"),
    6: (4, 4, "Write Single Register: Address(2) + Value(2)"),
    7: (0, 0, "Read Exception Status: No PDU data"),
    8: (4, 4, "Diagnostics: Subfunction(2) + Data(2)"),
    15: (5, 256, "Write Multiple Coils: Address(2) + Quantity(2) + ByteCount(1) + Data"),
    16: (5, 256, "Write Multiple Registers: Address(2) + Quantity(2) + ByteCount(1) + Data"),
    17: (0, 0, "Report Server ID: No PDU data"),
    20: (6, 254, "Read File Record: ByteCount(1) + Subrequests"),
    21: (6, 254, "Write File Record: ByteCount(1) + Subrequests"),
    22: (6, 6, "Mask Write Register: Address(2) + AndMask(2) + OrMask(2)"),
    23: (9, 254, "Read/Write Multiple Registers: ReadAddress(2) + ReadQuantity(2) + WriteAddress(2) + WriteQuantity(2) + WriteByteCount(1) + Data"),
    24: (4, 4, "Read FIFO Queue: Address(2) + Quantity(2)"),
    43: (2, 254, "Read Device Identification: MEI(1) + ReadDeviceIdCode(1) + ObjectId(1)"),
}

RESPONSE_STRUCTURE = {
    1: (1, 256, "Read Coils: ByteCount(1) + Data"),
    2: (1, 256, "Read Discrete Inputs: ByteCount(1) + Data"),
    3: (1, 252, "Read Holding Registers: ByteCount(1) + Data"),
    4: (1, 252, "Read Input Registers: ByteCount(1) + Data"),
    5: (4, 4, "Write Single Coil: Address(2) + Value(2)"),
    6: (4, 4, "Write Single Register: Address(2) + Value(2)"),
    7: (1, 1, "Read Exception Status: ExceptionCode(1)"),
    8: (4, 4, "Diagnostics: Subfunction(2) + Data(2)"),
    15: (4, 4, "Write Multiple Coils: Address(2) + Quantity(2)"),
    16: (4, 4, "Write Multiple Registers: Address(2) + Quantity(2)"),
    17: (1, 256, "Report Server ID: ByteCount(1) + Data"),
    20: (2, 254, "Read File Record: ByteCount(1) + Subresponses"),
    21: (2, 254, "Write File Record: ByteCount(1) + Subresponses"),
    22: (6, 6, "Mask Write Register: Address(2) + AndMask(2) + OrMask(2)"),
    23: (4, 254, "Read/Write Multiple Registers: ReadByteCount(1) + Data"),
    24: (3, 256, "Read FIFO Queue: ByteCount(2) + Data"),
    43: (2, 254, "Read Device Identification: MEI(1) + ReadDeviceIdCode(1) + ConformityLevel(1) + MoreFollows(1) + NextObjectId(1) + Objects"),
}


def is_exception_response(function_code: int) -> bool:
    return (function_code & 0x80) != 0


def get_original_function(function_code: int) -> int:
    return function_code & 0x7F