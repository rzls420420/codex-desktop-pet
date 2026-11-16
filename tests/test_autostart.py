import tempfile
import unittest
import types
from pathlib import Path
from unittest.mock import patch

from dragon_pet import autostart


class AutostartTests(unittest.TestCase):
    def test_linux_toggle_creates_and_removes_user_entry(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict('os.environ', {'XDG_CONFIG_HOME': tmp}):
            self.assertFalse(autostart.is_enabled('linux'))
            autostart.set_enabled(True, 'linux')
            entry = Path(tmp) / 'autostart' / 'white-dragon-pet.desktop'
            self.assertTrue(autostart.is_enabled('linux'))
            self.assertIn('dragon_pet.app', entry.read_text())
            autostart.set_enabled(False, 'linux')
            self.assertFalse(autostart.is_enabled('linux'))

    def test_linux_exec_quotes_spaces_and_percent_signs(self):
        self.assertEqual(autostart.desktop_quote('/a b/100%/x'), '"/a b/100%%/x"')

    def test_monitor_suppresses_codex_transitions_when_enabled(self):
        from dragon_pet.monitor import next_action
        self.assertIsNone(next_action(False, True, False, True))
        self.assertIsNone(next_action(True, False, True, True))
        self.assertEqual(next_action(True, False, True, False), 'stop')
        self.assertIsNone(next_action(False, True, True, False))

    def test_windows_toggle_uses_current_user_registry(self):
        values = {}
        class Key:
            def __enter__(self): return self
            def __exit__(self, *args): pass
        def query(key, name):
            if name not in values:
                raise FileNotFoundError(name)
            return values[name], 1
        def delete(key, name):
            if name not in values:
                raise FileNotFoundError(name)
            del values[name]
        registry = types.SimpleNamespace(HKEY_CURRENT_USER=1, KEY_SET_VALUE=2, REG_SZ=1,
            CreateKeyEx=lambda *args: Key(), OpenKey=lambda *args: Key(), QueryValueEx=query,
            SetValueEx=lambda key, name, reserved, kind, value: values.update({name: value}),
            DeleteValue=delete)
        with patch.dict('sys.modules', {'winreg': registry}):
            self.assertFalse(autostart.is_enabled('win32'))
            autostart.set_enabled(True, 'win32')
            self.assertTrue(autostart.is_enabled('win32'))
            self.assertIn('--pet', values[autostart.NAME])
            autostart.set_enabled(False, 'win32')
            self.assertFalse(autostart.is_enabled('win32'))


if __name__ == '__main__':
    unittest.main()
