# validators.py
# project_root/validators.py
# Python 3.11+, PyQt6

import re
from typing import Dict, Optional

class Validator:
    _patterns: Dict[str, str] = {
        "decimal": r"^-?\d*([.,]\d*)?$",
        "bin_direct": r"^-?[01]+$",
        "bin_complement": r"^[01]+$",
        "hex_direct": r"^-?[0-9A-Fa-f]+$",
        "hex_complement": r"^[0-9A-Fa-f]+$",
        "ieee_bin": r"^[01]+$",
        "ieee_hex": r"^[0-9A-Fa-f]+$",
        "unicode_char": r"^.$",
        "utf8_char": r"^.$",
    }

    @classmethod
    def validate(cls, text: str, fmt: str) -> bool:
        if not text:
            return True
        pattern: Optional[str] = cls._patterns.get(fmt)
        if pattern is None:
            return False
        return re.fullmatch(pattern, text) is not None