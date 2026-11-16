import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from build_transparent_sprites import prepare_frame
from dragon_pet.animation import ANIMATIONS


class TransparentSpriteTests(unittest.TestCase):
    def test_frame_keeps_artwork_and_uses_common_scale(self):
        source = Image.new('RGBA', (200, 200))
        for x in range(30, 170):
            for y in range(20, 180):
                source.putpixel((x, y), (200, 180, 220, 255))
        result = prepare_frame(source, baseline=180, scale=1.0, size=(240, 240), ground=200)
        self.assertEqual(result.getchannel('A').getbbox(), (50, 40, 190, 200))

    def test_refuses_to_crop_artwork_at_cell_boundary(self):
        source = Image.new('RGBA', (10, 10))
        source.putpixel((0, 5), (255, 255, 255, 255))
        with self.assertRaises(ValueError):
            prepare_frame(source, baseline=9)

    def test_faint_transparency_noise_is_removed(self):
        source = Image.new('RGBA', (10, 10), (255, 0, 255, 4))
        source.putpixel((5, 5), (200, 180, 220, 255))
        result = prepare_frame(source, baseline=9)
        self.assertEqual(result.getpixel((0, 0))[3], 0)

    def test_all_generated_frames_are_visible_and_not_cut_off(self):
        root = Path(__file__).resolve().parent.parent / 'assets/transparent-v2'
        counts = {name: count for name, (count, _) in ANIMATIONS.items()}
        counts['sleep'] = 8
        for state, count in counts.items():
            for index in range(count):
                with self.subTest(state=state, frame=index):
                    image = Image.open(root / state / f'{index:02d}.png').convert('RGBA')
                    self.assertEqual(image.size, (768, 832))
                    pixels = np.asarray(image)
                    alpha = pixels[:, :, 3]
                    self.assertGreater(np.count_nonzero(alpha > 32), 1000)
                    self.assertFalse((alpha[:10, :] > 32).any())
                    self.assertFalse((alpha[-10:, :] > 32).any())
                    self.assertFalse((alpha[:, :10] > 32).any())
                    self.assertFalse((alpha[:, -10:] > 32).any())
                    rgb = pixels[:, :, :3].astype(np.int16)
                    spill = rgb[:, :, 1] - np.maximum(rgb[:, :, 0], rgb[:, :, 2])
                    self.assertLess(int(((alpha > 64) & (spill > 20)).sum()), 10)
