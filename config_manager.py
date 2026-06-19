# config_manager.py (обновлен default_config)
# Python 3.11+, PyQt6

import os
import yaml
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self):
        self.config_file = "settings.yaml"
        self.default_config = {
            "converter": {
                "visible_fields": {
                    "decimal": True,
                    "hex_direct": True,
                    "bin_direct": True,
                    "bin_complement": False,
                    "hex_complement": False,
                    "ieee_bin": False,
                    "ieee_hex": False,
                    "unicode_char": False,
                    "utf8_char": False
                }
            },
            "modbus": {
                "protocol": "TCP",
                "direction": "Request",
                "rtu_slave_id_enabled": True,
                "rtu_crc_enabled": True
            }
        }
    
    def load(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_file):
            logger.info("Config file not found, using defaults")
            return self.default_config.copy()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                result = self.default_config.copy()
                if config and isinstance(config, dict):
                    self._deep_merge(result, config)
                return result
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self.default_config.copy()
    
    def save(self, config: Dict[str, Any]) -> bool:
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
            logger.info(f"Config saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value