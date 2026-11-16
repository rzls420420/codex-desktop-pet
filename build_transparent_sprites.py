"""Build registered desktop-pet frames from transparent generated sheets."""
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent / 'assets/transparent-v2'
SIZE = (768, 832)
SCALE = 1.7
GROUND = 782


def prepare_frame(cell, baseline, scale=SCALE, size=SIZE, ground=GROUND):
    pixels = np.array(cell.convert('RGBA'))
    alpha = pixels[:, :, 3]
    if any((edge > 32).any() for edge in (alpha[0, :], alpha[-1, :], alpha[:, 0], alpha[:, -1])):
        raise ValueError('Artwork touches the source cell boundary')
    pixels[alpha < 16] = 0
    ys, xs = np.where(pixels[:, :, 3] > 32)
    if not len(xs):
        raise ValueError('Empty sprite frame')
    left = max(0, int(xs.min()) - 8)
    top = max(0, int(ys.min()) - 8)
    right = min(cell.width, int(xs.max()) + 9)
    bottom = min(cell.height, int(ys.max()) + 9)
    crop = Image.fromarray(pixels, 'RGBA').crop((left, top, right, bottom))
    crop = crop.resize((round(crop.width * scale), round(crop.height * scale)), Image.Resampling.LANCZOS)
    x = (size[0] - crop.width) // 2
    y = round(ground + (top - baseline) * scale)
    bounds = crop.getchannel('A').getbbox()
    if bounds and (x + bounds[0] < 0 or y + bounds[1] < 0 or
                   x + bounds[2] > size[0] or y + bounds[3] > size[1]):
        raise ValueError('Artwork would be cropped on the output canvas')
    result = Image.new('RGBA', size)
    result.alpha_composite(crop, (x, y))
    return result


def load_cells(name, sleep=False):
    sheet = Image.open(ROOT / 'source' / name).convert('RGBA')
    if sheet.size != (1774, 887):
        raise ValueError(f'Unexpected sheet dimensions: {name}: {sheet.size}')
    rows = []
    for row, (top, bottom) in enumerate(((0, 443), (443, 887))):
        edges = (0, 443, 860, 1330, 1774) if sleep and row == 1 else (0, 443, 887, 1330, 1774)
        rows.append([sheet.crop((edges[i], top, edges[i + 1], bottom)) for i in range(4)])
    return rows


def main():
    idle, waving = load_cells('idle-waving.png')
    right, left = load_cells('running.png')
    jumping, failed = load_cells('jump-sulk.png')
    waiting, review = load_cells('wait-review.png')
    working, _ = load_cells('working.png')
    sleep = sum(load_cells('sleep.png', sleep=True), [])
    specs = {
        'idle': (idle, 403, (0, 1, 1, 2, 2, 3)),
        'waving': (waving, 404, (0, 1, 2, 3)),
        'running-right': (right, 416, (0, 1, 2, 3, 0, 1, 2, 3)),
        'running-left': (left, 416, (0, 1, 2, 3, 0, 1, 2, 3)),
        'jumping': (jumping, 413, (0, 1, 2, 1, 3)),
        'failed': (failed, 413, (0, 1, 2, 3, 3, 2, 1, 0)),
        'waiting': (waiting, 417, (0, 1, 2, 2, 1, 3)),
        'running': (working, 421, (0, 1, 2, 3, 2, 1)),
        'review': (review, 417, (0, 1, 2, 3, 2, 1)),
        'sleep': (sleep, 405, tuple(range(8))),
    }
    for state, (cells, baseline, order) in specs.items():
        destination = ROOT / state
        destination.mkdir(parents=True, exist_ok=True)
        frames = [prepare_frame(cell, baseline) for cell in cells]
        for index, source in enumerate(order):
            frames[source].save(destination / f'{index:02d}.png')
        print(f'{state}: {len(order)} frames')


if __name__ == '__main__':
    main()
