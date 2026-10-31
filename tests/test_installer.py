"""Install/uninstall against temporary user directories, never the real desktop."""
import argparse
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('installer', ROOT / 'tools/install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.args = argparse.Namespace(
            rime_dir=self.base / 'rime', state_dir=self.base / 'state',
            shared_data_dir=Path('/usr/share/rime-data'),
            install_deps=False, no_deploy=True, configure_gnome=False, dry_run=False)

    def write_config(self, data):
        self.args.rime_dir.mkdir(parents=True, exist_ok=True)
        (self.args.rime_dir / 'default.custom.yaml').write_bytes(data)

    def test_fresh_install_upgrade_uninstall(self):
        installer.install(self.args)
        config = self.args.rime_dir / 'default.custom.yaml'
        first = config.read_bytes()
        installer.install(self.args)
        self.assertEqual(config.read_bytes(), first)
        installer.uninstall(self.args)
        self.assertFalse(config.exists())
        self.assertFalse((self.args.rime_dir / 'linux_xp_quick.schema.yaml').exists())

    def test_existing_config_is_restored_byte_for_byte(self):
        original = b'# custom comment\npatch:\n  schema_list:\n    - schema: luna_pinyin\n  menu/page_size: 7\n'
        self.write_config(original)
        installer.install(self.args)
        self.assertIn(b'luna_pinyin', (self.args.rime_dir / 'default.custom.yaml').read_bytes())
        installer.uninstall(self.args)
        self.assertEqual((self.args.rime_dir / 'default.custom.yaml').read_bytes(), original)

    def test_existing_append_patch_and_later_user_edit_survive(self):
        original = b'patch:\n  schema_list/+:\n    - schema: luna_pinyin\n'
        self.write_config(original)
        installer.install(self.args)
        config = self.args.rime_dir / 'default.custom.yaml'
        config.write_bytes(config.read_bytes() + b'  menu/page_size: 6\n')
        installer.uninstall(self.args)
        result = config.read_bytes()
        self.assertIn(b'luna_pinyin', result)
        self.assertIn(b'menu/page_size: 6', result)
        self.assertNotIn(b'linux_xp_quick', result)

    def test_existing_custom_file_is_backed_up(self):
        self.write_config(b'patch: {}\n')
        file = self.args.rime_dir / 'linux_xp_quick.schema.yaml'
        file.write_bytes(b'original\n')
        installer.install(self.args)
        installer.uninstall(self.args)
        self.assertEqual(file.read_bytes(), b'original\n')

    def test_user_config_edits_survive_reinstall_then_uninstall(self):
        self.write_config(b'patch:\n  schema_list:\n    - schema: luna_pinyin\n')
        installer.install(self.args)
        config = self.args.rime_dir / 'default.custom.yaml'
        config.write_bytes(config.read_bytes() + b'  menu/page_size: 6\n')
        installer.install(self.args)
        installer.install(self.args)
        installer.uninstall(self.args)
        result = config.read_bytes()
        self.assertIn(b'luna_pinyin', result)
        self.assertIn(b'menu/page_size: 6', result)
        self.assertNotIn(b'linux_xp_quick', result)

    def test_gnome_settings_restore_and_keep_later_edits(self):
        # A separate process with an in-memory backend cannot touch the desktop.
        script = '''
import sys
sys.path.insert(0, 'tools')
import install
from gi.repository import Gio, GLib
sources = Gio.Settings.new('org.gnome.desktop.input-sources')
keys = Gio.Settings.new('org.gnome.desktop.wm.keybindings')
sources.set_value('sources', GLib.Variant('a(ss)', [('xkb', 'us')]))
sources.set_strv('xkb-options', ['caps:escape', 'grp:alt_shift_toggle'])
keys.set_strv('switch-input-source', ['<Super>space'])
state = {'desktop': []}
install.apply_desktop(install.desktop_plan(), state)
assert sources.get_value('sources').unpack() == [('xkb', 'us'), ('ibus', 'rime')]
assert sources.get_strv('xkb-options') == ['caps:escape', 'grp:ctrl_shift_toggle']
assert '<Control>space' in keys.get_strv('switch-input-source')
install.apply_desktop(install.desktop_plan(), state)
assert len(state['desktop']) == 4
keys.set_strv('switch-input-source', ['<Alt>space'])
install.restore_desktop(state['desktop'])
assert sources.get_value('sources').unpack() == [('xkb', 'us')]
assert sources.get_strv('xkb-options') == ['caps:escape', 'grp:alt_shift_toggle']
assert keys.get_strv('switch-input-source') == ['<Alt>space']
assert keys.get_user_value('switch-input-source-backward') is None
'''
        result = subprocess.run([sys.executable, '-c', script], cwd=ROOT,
                                env={**os.environ, 'GSETTINGS_BACKEND': 'memory',
                                     'XDG_CURRENT_DESKTOP': 'GNOME'},
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_modified_package_file_blocks_upgrade_and_uninstall(self):
        installer.install(self.args)
        file = self.args.rime_dir / 'lua/linux_xp_quick_processor.lua'
        file.write_bytes(file.read_bytes() + b'-- my modification\n')
        with self.assertRaises(RuntimeError): installer.install(self.args)
        with self.assertRaises(RuntimeError): installer.uninstall(self.args)
        self.assertTrue(file.read_bytes().endswith(b'-- my modification\n'))

    def test_failure_rolls_back_sources_and_compiled_files(self):
        original = b'patch: {}\n'
        self.write_config(original)
        self.args.no_deploy = False
        with patch.object(installer, 'dependency_check'), patch.object(installer, 'deploy', side_effect=RuntimeError('failed')):
            with self.assertRaises(RuntimeError): installer.install(self.args)
        self.assertEqual((self.args.rime_dir / 'default.custom.yaml').read_bytes(), original)
        self.assertFalse((self.args.rime_dir / 'linux_xp_quick.schema.yaml').exists())
        self.assertFalse(installer.manifest_path(self.args.rime_dir, self.args.state_dir).exists())

    def test_dry_run_writes_nothing(self):
        self.args.dry_run = True
        installer.install(self.args)
        self.assertFalse(self.args.rime_dir.exists())
        self.assertFalse(self.args.state_dir.exists())

    def test_symlink_target_is_not_overwritten(self):
        self.args.rime_dir.mkdir()
        other = self.base / 'other'
        other.write_bytes(b'patch: {}\n')
        (self.args.rime_dir / 'default.custom.yaml').symlink_to(other)
        with self.assertRaises(ValueError): installer.install(self.args)
        self.assertEqual(other.read_bytes(), b'patch: {}\n')


if __name__ == '__main__':
    unittest.main()
