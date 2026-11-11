# tests/test_config_manager.py
# project_root/tests/test_config_manager.py
# Python 3.11+, PyQt6

import os
import tempfile
import unittest

import yaml

from config_manager import ConfigManager


class TestConfigManager(unittest.TestCase):
    """Регрессия: load() не должен мутировать default_config."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._old_cwd = os.getcwd()
        os.chdir(self._tmp.name)

    def tearDown(self) -> None:
        os.chdir(self._old_cwd)
        self._tmp.cleanup()

    def _write_config(self, config: dict) -> None:
        with open("settings.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f, allow_unicode=True)

    def test_defaults_not_mutated_after_load(self) -> None:
        manager = ConfigManager()
        self._write_config({"modbus": {"protocol": "ASCII"}})
        first = manager.load()
        self.assertEqual(first["modbus"]["protocol"], "ASCII")

        # Удаляем файл: повторная load() должна вернуть исходные дефолты,
        # а не накопленные значения из первой загрузки
        os.remove("settings.yaml")
        second = manager.load()
        self.assertEqual(second["modbus"]["protocol"], "TCP")

    def test_load_missing_file_returns_defaults(self) -> None:
        manager = ConfigManager()
        config = manager.load()
        self.assertEqual(config["modbus"]["protocol"], "TCP")
        self.assertTrue(config["converter"]["visible_fields"]["decimal"])


if __name__ == "__main__":
    unittest.main()
