from PIL import Image
import numpy as np


def remove_green(image):
    rgba = np.asarray(image.convert('RGBA'), dtype=np.uint8).copy()
    rgb = rgba[:, :, :3].astype(np.int16)
    excess = np.maximum(0, rgb[:, :, 1] - np.maximum(rgb[:, :, 0], rgb[:, :, 2]))
    alpha = np.minimum(rgba[:, :, 3].astype(np.int16), 255 - excess)
    alpha[alpha < 12] = 0
    rgb[:, :, 1] = np.minimum(rgb[:, :, 1], np.maximum(rgb[:, :, 0], rgb[:, :, 2]))
    rgba[:, :, :3] = rgb.astype(np.uint8)
    rgba[:, :, 3] = alpha.astype(np.uint8)
    rgba[alpha == 0] = 0
    return Image.fromarray(rgba, 'RGBA')


def fit_frame(image, size):
    sprite = image.copy()
    sprite.thumbnail((size[0] - 20, size[1] - 20), Image.Resampling.LANCZOS)
    output = Image.new('RGBA', size)
    output.alpha_composite(sprite, ((size[0] - sprite.width) // 2, (size[1] - sprite.height) // 2))
    return output


def despill_green(image):
    rgba = np.asarray(image.convert('RGBA'), dtype=np.uint8).copy()
    rgba[:, :, 1] = np.minimum(rgba[:, :, 1], np.maximum(rgba[:, :, 0], rgba[:, :, 2]))
    rgba[rgba[:, :, 3] == 0] = 0
    return Image.fromarray(rgba, 'RGBA')
