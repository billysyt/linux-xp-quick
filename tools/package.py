#!/usr/bin/env python3
"""Create a reproducible source/install archive with dictionaries and licenses."""
import gzip
import hashlib
import io
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ['rime', 'data', 'licenses', 'tools', 'tests', '.github']
FILES = ['README.md', 'LICENSE', 'THIRD_PARTY.md', 'CHANGELOG.md', 'CONTRIBUTING.md',
         'VERSION', '.gitignore', 'install.sh', 'uninstall.sh']


def main():
    subprocess.run(['python3', str(ROOT / 'tools/build_data.py'), '--check'], check=True)
    version = (ROOT / 'VERSION').read_text().strip()
    prefix = f'linux-xp-quick-{version}'
    files = [ROOT / name for name in FILES]
    files += [p for name in DIRECTORIES for p in (ROOT / name).rglob('*')
              if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc']
    output = ROOT / 'dist'
    output.mkdir(exist_ok=True)
    archive = output / f'{prefix}.tar.gz'
    with archive.open('wb') as raw, gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode='w') as tar:
            for file in sorted(files):
                data = file.read_bytes()
                entry = tarfile.TarInfo(prefix + '/' + str(file.relative_to(ROOT)))
                entry.size = len(data)
                entry.mode = 0o755 if file.suffix == '.sh' else 0o644
                entry.mtime = 0
                tar.addfile(entry, io.BytesIO(data))
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / 'SHA256SUMS').write_text(f'{checksum}  {archive.name}\n')
    print(archive)


if __name__ == '__main__':
    main()
