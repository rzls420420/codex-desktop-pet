import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('create_packages', ROOT / 'packaging/create_packages.py')
packager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packager)


class PackageTests(unittest.TestCase):
    def test_each_package_contains_only_current_runtime_assets(self):
        for platform in ('linux', 'windows'):
            files = dict(packager.collect_files(platform))
            names = set(files)
            with self.subTest(platform=platform):
                self.assertIn('assets/transparent-v2/sleep/06.png', names)
                self.assertIn('assets/transparent-v2/waving/00.png', names)
                self.assertIn('dragon_pet/speech.py', names)
                self.assertFalse(any('hd-v1' in name or '/source/' in name for name in names))
                self.assertFalse(any('storyboard' in name or 'spritesheet' in name for name in names))
                self.assertEqual(sum(name.startswith('assets/') for name in names), 65)

    def test_platform_launchers_are_separate(self):
        linux = dict(packager.collect_files('linux'))
        windows = dict(packager.collect_files('windows'))
        self.assertIn('start.sh', linux)
        self.assertIn('standalone.bat', windows)
        self.assertNotIn('standalone.bat', linux)
        self.assertNotIn('start.sh', windows)


if __name__ == '__main__':
    unittest.main()
