# Paint an old burn scar on the forearm of a CC5 arm diffuse texture (2048, both arms side by side).
# usage: python paint_burn_scar.py <arm_diffuse.png> <out.png> [cx cy rx ry]  (pixels, default = left strip forearm)
import sys
import numpy as np
from PIL import Image, ImageFilter

src, dst = sys.argv[1], sys.argv[2]
cx, cy, rx, ry = (map(float, sys.argv[3:7]) if len(sys.argv) >= 7 else (600, 1130, 230, 300))
im = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
h, w, _ = im.shape
rng = np.random.default_rng(7)


def noise(scale):
    n = rng.random((h // scale + 2, w // scale + 2)).astype(np.float32)
    return np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(np.float32) / 255


yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
d = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
edge = 1.0 - d + (noise(64) - 0.5) * 0.9 + (noise(16) - 0.5) * 0.15   # ragged outline
mask = np.clip(edge * 4, 0, 1)
mask = np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 255
rim = np.clip(1 - np.abs(edge) * 3.5, 0, 1) * (edge > -0.15)            # darker band at the border

mott = noise(56) * 0.75 + noise(14) * 0.25                                # uneven scar tissue
pink = np.array([168, 86, 74], np.float32)
pale = np.array([214, 150, 132], np.float32)
dark = np.array([96, 52, 42], np.float32)
scar = pink[None, None] * (1 - mott[..., None]) + pale[None, None] * mott[..., None]
scar = scar * (1 - 0.6 * rim[..., None]) + dark[None, None] * 0.6 * rim[..., None]
lum = im.mean(axis=2, keepdims=True) / max(im.mean(), 1)               # keep pores / folds from the skin
scar = np.clip(scar * (0.75 + 0.25 * lum), 0, 255)
out = im * (1 - mask[..., None] * 0.92) + scar * mask[..., None] * 0.92
Image.fromarray(out.astype(np.uint8)).save(dst)
print("saved", dst)
