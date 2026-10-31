#!/usr/bin/env python3
"""每位使用者獨立安裝、備份及移除 linux-xp-quick。"""
import argparse
import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 'linux_xp_quick'
VERSION = (ROOT / 'VERSION').read_text().strip()
PACKAGES = ['ibus-rime', 'librime-plugin-lua', 'librime-bin', 'rime-prelude',
            'python3-yaml', 'python3-gi']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_optional(path):
    if path.is_symlink():
        raise ValueError(f'目標是符號連結，請先自行處理：{path}')
    return path.read_bytes() if path.exists() else None


def write_atomic(path, data, mode=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
        os.chmod(temporary, mode if mode is not None else 0o644)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def restore(path, data, mode=0o644):
    if data is None:
        path.unlink(missing_ok=True)
    else:
        write_atomic(path, data, mode)


def yaml_load(raw):
    import yaml
    document = yaml.safe_load(raw) if raw else {}
    if document is None:
        document = {}
    if not isinstance(document, dict):
        raise ValueError('default.custom.yaml 必須是 YAML mapping。')
    patch = document.setdefault('patch', {})
    if not isinstance(patch, dict):
        raise ValueError('default.custom.yaml 的 patch 必須是 mapping。')
    # Deep index patches cannot be reliably reordered while retaining meaning.
    for key in patch:
        if key.startswith('schema_list/') and key != 'schema_list/+':
            raise ValueError(f'請先整合複雜的方案清單修補：{key}')
    for key in ('schema_list', 'schema_list/+'):
        if key in patch and not isinstance(patch[key], list):
            raise ValueError(f'{key} 必須是清單。')
    return document


def contains_schema(raw):
    patch = yaml_load(raw)['patch']
    return any(isinstance(item, dict) and item.get('schema') == SCHEMA
               for key in ('schema_list', 'schema_list/+') for item in patch.get(key, []))


def register_schema(raw):
    import yaml
    if raw and contains_schema(raw):
        return raw
    document = yaml_load(raw)
    patch = document['patch']
    # A new installation needs no unavailable default schemas. Existing users
    # keep their schema list; append to the system list when no explicit list exists.
    key = 'schema_list' if not raw or 'schema_list' in patch else 'schema_list/+'
    patch.setdefault(key, []).append({'schema': SCHEMA})
    return yaml.safe_dump(document, allow_unicode=True, sort_keys=False).encode()


def unregister_schema(raw):
    import yaml
    document = yaml_load(raw)
    patch = document['patch']
    for key in ('schema_list', 'schema_list/+'):
        if key in patch:
            patch[key] = [item for item in patch[key]
                          if not (isinstance(item, dict) and item.get('schema') == SCHEMA)]
            if not patch[key]:
                del patch[key]
    return yaml.safe_dump(document, allow_unicode=True, sort_keys=False).encode()


def manifest_path(rime_dir, state_dir):
    return state_dir / (sha(str(rime_dir).encode())[:16] + '.json')


def load_manifest(path, rime_dir):
    if not path.exists():
        return {'format': 1, 'rime_dir': str(rime_dir), 'files': {}, 'desktop': []}
    state = json.loads(path.read_text())
    if state.get('format') != 1 or state.get('rime_dir') != str(rime_dir):
        raise ValueError('安裝紀錄不相容。')
    return state


def encode(data):
    return base64.b64encode(data).decode() if data is not None else None


def decode(data):
    return base64.b64decode(data) if data is not None else None


def deploy(rime_dir, shared_dir):
    result = subprocess.run(['rime_deployer', '--build', str(rime_dir), str(shared_dir)],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if result.returncode:
        raise RuntimeError('Rime 編譯失敗：\n' + result.stdout[-6000:])
    if not (rime_dir / 'build' / (SCHEMA + '.table.bin')).exists():
        raise RuntimeError('Rime 沒有產生預期字典；請檢查 rime_deployer 日誌。')


def dependency_check(shared_dir):
    missing = []
    for binary in ['rime_deployer', 'ibus']:
        if not shutil.which(binary):
            missing.append(binary)
    try:
        import yaml  # noqa: F401
    except ImportError:
        missing.append('python3-yaml')
    if not list(Path('/usr/lib').glob('**/rime-plugins/librime-lua.so')):
        missing.append('librime-plugin-lua')
    if not (shared_dir / 'default.yaml').exists():
        missing.append(f'rime-prelude ({shared_dir})')
    if missing:
        raise RuntimeError('缺少依賴：' + ', '.join(missing) + '\n請使用 ./install.sh --install-deps')


def desktop_plan():
    from gi.repository import Gio, GLib
    desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
    if 'gnome' not in desktop:
        raise RuntimeError('--configure-gnome 只適用於目前的 GNOME 桌面工作階段。')
    sources = Gio.Settings.new('org.gnome.desktop.input-sources')
    configured = sources.get_value('sources').unpack()
    if ('ibus', 'rime') not in configured:
        configured.append(('ibus', 'rime'))
    options = sources.get_strv('xkb-options')
    options = [value for value in options if not value.startswith('grp:')]
    options.append('grp:ctrl_shift_toggle')
    return [
        (sources, 'sources', GLib.Variant('a(ss)', configured)),
        (sources, 'xkb-options', GLib.Variant('as', options)),
        (Gio.Settings.new('org.gnome.desktop.wm.keybindings'), 'switch-input-source',
         GLib.Variant('as', ['<Control>space', 'XF86Keyboard'])),
        (Gio.Settings.new('org.gnome.desktop.wm.keybindings'), 'switch-input-source-backward',
         GLib.Variant('as', ['<Shift><Control>space', '<Shift>XF86Keyboard'])),
    ]


def apply_desktop(plan, state):
    from gi.repository import Gio
    for settings, key, value in plan:
        schema = settings.props.schema_id
        entry = next((x for x in state['desktop'] if x['schema'] == schema and x['key'] == key), None)
        if entry is None:
            original = settings.get_user_value(key)
            entry = {'schema': schema, 'key': key,
                     'before': original.print_(True) if original is not None else None}
            state['desktop'].append(entry)
        if not settings.set_value(key, value):
            raise RuntimeError(f'無法寫入 GNOME 設定：{key}')
        entry['installed'] = value.print_(True)
    Gio.Settings.sync()


def restore_desktop(entries):
    if not entries:
        return
    from gi.repository import Gio, GLib
    for entry in entries:
        settings = Gio.Settings.new(entry['schema'])
        if settings.get_value(entry['key']).print_(True) != entry.get('installed'):
            print(f'保留安裝後自行修改的桌面設定：{entry["key"]}')
            continue
        if entry['before'] is None:
            settings.reset(entry['key'])
        else:
            settings.set_value(entry['key'], GLib.Variant.parse(None, entry['before'], None, None))
    Gio.Settings.sync()


def install(args):
    if args.install_deps and not args.dry_run:
        if not shutil.which('apt-get'):
            raise RuntimeError('自動安裝依賴只支援 apt；請先手動安裝 Rime、Lua 插件及 PyYAML。')
        subprocess.run(['sudo', 'apt-get', 'install', '-y', '--no-install-recommends', *PACKAGES], check=True)
    if not args.no_deploy and not args.dry_run:
        dependency_check(args.shared_data_dir)
    path = manifest_path(args.rime_dir, args.state_dir)
    previous_manifest = read_optional(path)
    state = load_manifest(path, args.rime_dir)
    files = {str(p.relative_to(ROOT / 'rime')): p.read_bytes()
             for p in sorted((ROOT / 'rime').rglob('*')) if p.is_file()}
    config = args.rime_dir / 'default.custom.yaml'
    current_config = read_optional(config)
    files['default.custom.yaml'] = register_schema(current_config)
    desktop = desktop_plan() if args.configure_gnome else []
    print(f'linux-xp-quick {VERSION} → {args.rime_dir}')
    for name in files:
        print('  ' + name)
    if args.dry_run:
        print('預覽完成，沒有修改任何檔案或設定。')
        return

    before = {}
    for name, data in files.items():
        target = args.rime_dir / name
        raw = read_optional(target)
        mode = target.stat().st_mode & 0o777 if target.exists() else 0o644
        entry = state['files'].get(name)
        if entry and raw is not None and sha(raw) != entry['installed'] and name != 'default.custom.yaml':
            raise RuntimeError(f'保留你修改過的檔案：{target}\n請先另存修改，然後重新安裝。')
        before[name] = (raw, mode)
        if not entry:
            state['files'][name] = {'before': encode(raw), 'mode': mode}
        elif name == 'default.custom.yaml' and (raw is None or sha(raw) != entry['installed']):
            # An update must not make later uninstall erase edits made since
            # the first installation, even when our schema was already present.
            entry['shared_modified'] = True
        state['files'][name]['installed'] = sha(data)
    compiled_before = {p: read_optional(p) for p in [
        args.rime_dir / 'build/default.yaml',
        *[args.rime_dir / 'build' / (SCHEMA + suffix)
          for suffix in ['.schema.yaml', '.table.bin', '.reverse.bin', '.prism.bin']],
    ]}
    desktop_before = []
    for settings, key, value in desktop:
        old = settings.get_user_value(key)
        desktop_before.append({'schema': settings.props.schema_id, 'key': key,
                               'before': old.print_(True) if old is not None else None,
                               'installed': value.print_(True)})
    try:
        for name, data in files.items():
            write_atomic(args.rime_dir / name, data, before[name][1])
        if not args.no_deploy:
            deploy(args.rime_dir, args.shared_data_dir)
        # Save recoverable state before making optional desktop changes.
        state['version'] = VERSION
        write_atomic(path, json.dumps(state, ensure_ascii=False, indent=2).encode(), 0o600)
        if desktop:
            apply_desktop(desktop, state)
            write_atomic(path, json.dumps(state, ensure_ascii=False, indent=2).encode(), 0o600)
    except Exception:
        for name, (data, mode) in before.items():
            restore(args.rime_dir / name, data, mode)
        for compiled, data in compiled_before.items():
            restore(compiled, data)
        restore(path, previous_manifest, 0o600)
        restore_desktop(desktop_before)
        raise
    print(f'安裝完成。備份及安裝紀錄：{path}')
    print('請在 Rime 選單按「部署」，再按 F4 選擇「XP 速成」。')
    print('首次安裝 IBus Rime 後，如輸入來源仍未出現，請登出再登入。')


def uninstall(args):
    path = manifest_path(args.rime_dir, args.state_dir)
    if not path.exists():
        raise RuntimeError('找不到安裝紀錄，沒有移除任何檔案。')
    state = load_manifest(path, args.rime_dir)
    plan = {}
    for name, entry in state['files'].items():
        target = args.rime_dir / name
        raw = read_optional(target)
        original = decode(entry['before'])
        if name == 'default.custom.yaml' and entry.get('shared_modified'):
            plan[name] = raw if raw is None or contains_schema(original) else unregister_schema(raw)
            continue
        if raw is not None and sha(raw) != entry['installed']:
            if name == 'default.custom.yaml':
                plan[name] = raw if contains_schema(original) else unregister_schema(raw)
                continue
            raise RuntimeError(f'檔案在安裝後被修改，暫停移除以保留修改：{target}')
        plan[name] = original
    if args.dry_run:
        print('將還原／移除：\n' + '\n'.join(plan))
        return
    for name, data in plan.items():
        restore(args.rime_dir / name, data, state['files'][name]['mode'])
    for file in (args.rime_dir / 'build').glob(SCHEMA + '.*'):
        file.unlink()
    restore_desktop(state['desktop'])
    path.unlink()
    print('已移除 XP 速成並還原備份；Rime 引擎及其他方案保留。請重新部署 Rime。')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['install', 'uninstall', 'doctor'])
    parser.add_argument('--rime-dir', type=Path, default=Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'ibus/rime')
    parser.add_argument('--state-dir', type=Path, default=Path(os.environ.get('XDG_STATE_HOME', Path.home() / '.local/state')) / 'linux-xp-quick')
    parser.add_argument('--shared-data-dir', type=Path, default=Path('/usr/share/rime-data'))
    parser.add_argument('--install-deps', action='store_true', help='使用 apt 安裝依賴（需要 sudo）')
    parser.add_argument('--configure-gnome', action='store_true', help='加入 Rime 輸入來源並設定 Ctrl+Space／Ctrl+Shift')
    parser.add_argument('--dry-run', action='store_true', help='只預覽，不修改檔案')
    parser.add_argument('--no-deploy', action='store_true', help='只複製設定；稍後自行部署 Rime')
    args = parser.parse_args()
    args.rime_dir = args.rime_dir.expanduser().resolve()
    args.state_dir = args.state_dir.expanduser().resolve()
    try:
        if os.geteuid() == 0 and args.command != 'doctor':
            raise RuntimeError('請以一般使用者執行，不要 sudo ./install.sh。只有安裝依賴需要 sudo。')
        if args.command == 'doctor':
            dependency_check(args.shared_data_dir)
            print(f'依賴檢查通過。Rime 目錄：{args.rime_dir}')
            print(f'方案已安裝：{(args.rime_dir / (SCHEMA + ".schema.yaml")).exists()}')
        elif args.command == 'install':
            install(args)
        else:
            uninstall(args)
    except (ValueError, OSError, RuntimeError, ImportError, subprocess.CalledProcessError) as error:
        print(f'錯誤：{error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
