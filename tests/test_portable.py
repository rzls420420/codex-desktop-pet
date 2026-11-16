import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dragon_pet import app
from dragon_pet.dialogue import find_codex_executable


class PortableTests(unittest.TestCase):
    def test_frozen_assets_use_pyinstaller_extraction_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(app.sys, '_MEIPASS', folder, create=True):
                self.assertEqual(app.resource_root(), Path(folder))

    def test_windows_uses_discovered_codex_executable(self):
        with patch('dragon_pet.dialogue.os.name', 'nt'), \
             patch('dragon_pet.dialogue.shutil.which', return_value='C:/tools/codex.exe'):
            self.assertEqual(find_codex_executable(), 'C:/tools/codex.exe')

    def test_linux_uses_discovered_codex_when_bundled_path_missing(self):
        with patch('dragon_pet.dialogue.os.name', 'posix'), \
             patch('dragon_pet.dialogue.Path.is_file', return_value=False), \
             patch('dragon_pet.dialogue.shutil.which', return_value='/usr/bin/codex'):
            self.assertEqual(find_codex_executable(), '/usr/bin/codex')


if __name__ == '__main__':
    unittest.main()
