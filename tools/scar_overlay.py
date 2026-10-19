# Make a burn-scar OVERLAY (2048 RGBA: white + transparent everywhere except the scar) for CC5's DiffuseBlend
# channel, so it sits on top of any character's own skin without needing that skin texture.
#   python tools\scar_overlay.py <out.png> [cx cy rx ry] [seed]
import sys
import numpy as np
from PIL import Image, ImageFilter

out = sys.argv[1]
cx, cy, rx, ry = (map(float, sys.argv[2:6]) if len(sys.argv) >= 6 else (600, 1130, 230, 300))
seed = int(sys.argv[6]) if len(sys.argv) >= 7 else 7
h = w = 2048
rng = np.random.default_rng(seed)


def noise(scale):
    n = rng.random((h // scale + 2, w // scale + 2)).astype(np.float32)
    return np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(np.float32) / 255


yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
d = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
edge = 1.0 - d + (noise(64) - 0.5) * 0.9 + (noise(16) - 0.5) * 0.15   # ragged outline
mask = np.clip(edge * 4, 0, 1)
mask = np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 255
rim = np.clip(1 - np.abs(edge) * 3.5, 0, 1) * (edge > -0.15)
mott = noise(56) * 0.75 + noise(14) * 0.25
pink = np.array([196, 120, 112], np.float32)   # multiply-friendly tones (white = no change)
pale = np.array([236, 196, 186], np.float32)
dark = np.array([150, 92, 84], np.float32)
scar = pink * (1 - mott[..., None]) + pale * mott[..., None]
scar = scar * (1 - 0.6 * rim[..., None]) + dark * 0.6 * rim[..., None]
rgb = 255 * (1 - mask[..., None]) + scar * mask[..., None]
rgba = np.dstack([rgb, mask * 235]).clip(0, 255).astype(np.uint8)
Image.fromarray(rgba, "RGBA").save(out)
print("saved", out)
