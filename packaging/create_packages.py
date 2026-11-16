"""Create platform-specific runtime archives without development assets."""
import sys
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from dragon_pet.animation import ANIMATIONS


def collect_files(platform):
    if platform not in ('linux', 'windows'):
        raise ValueError(platform)
    template = ROOT / 'packaging' / platform
    for path in sorted(template.iterdir()):
        if path.is_file():
            yield path.name, path
    for path in sorted((ROOT / 'dragon_pet').glob('*.py')):
        if path.name == 'sprite_processing.py' or (platform == 'windows' and path.name == 'monitor.py'):
            continue
        yield f'dragon_pet/{path.name}', path
    counts = {name: data[0] for name, data in ANIMATIONS.items()}
    counts['sleep'] = 8
    for state, count in counts.items():
        for i in range(count):
            name = f'assets/transparent-v2/{state}/{i:02}.png'
            path = ROOT / name
            if not path.is_file():
                raise FileNotFoundError(path)
            yield name, path


def main():
    dest = ROOT / 'dist'
    dest.mkdir(exist_ok=True)
    linux = dest / 'white-dragon-linux.tar.gz'
    windows = dest / 'white-dragon-win11.zip'
    with tarfile.open(linux, 'w:gz') as archive:
        for name, path in collect_files('linux'):
            info = archive.gettarinfo(str(path), arcname=f'white-dragon-linux/{name}')
            info.mode = 0o755 if name.endswith('.sh') else 0o644
            with path.open('rb') as data:
                archive.addfile(info, data)
    with zipfile.ZipFile(windows, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, path in collect_files('windows'):
            archive.write(path, arcname=f'white-dragon-win11/{name}')
    print(linux)
    print(windows)


if __name__ == '__main__':
    main()
