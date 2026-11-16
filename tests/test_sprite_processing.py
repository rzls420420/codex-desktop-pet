import unittest

from PIL import Image

from dragon_pet.sprite_processing import remove_green, fit_frame


class SpriteProcessingTests(unittest.TestCase):
    def test_green_is_transparent_and_purple_remains(self):
        image = Image.new('RGB', (3, 1))
        image.putdata([(0, 255, 0), (120, 170, 110), (200, 180, 220)])
        out = remove_green(image)
        self.assertEqual(out.getpixel((0, 0))[3], 0)
        self.assertLessEqual(out.getpixel((1, 0))[1], max(out.getpixel((1, 0))[0], out.getpixel((1, 0))[2]))
        self.assertEqual(out.getpixel((2, 0)), (200, 180, 220, 255))

    def test_fit_preserves_transparency_and_dimensions(self):
        image = Image.new('RGBA', (20, 40), (200, 180, 220, 255))
        frame = fit_frame(image, (384, 416))
        self.assertEqual(frame.size, (384, 416))
        self.assertEqual(frame.getpixel((0, 0))[3], 0)


if __name__ == '__main__':
    unittest.main()
