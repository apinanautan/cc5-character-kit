# Make a garment-specific fabric texture that keeps the garment's own folds/seams/shading.
# make(garment_path, fabric_png) -> png path. Garments whose diffuse is a plain tile just get the fabric as-is.
import hashlib, io, os, re
from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageStat

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit
CACHE = os.path.join(kit.DATA, "fabric_cache")


def _diffuse(path):
    data = open(path, "rb").read()
    best = None
    for i, m in enumerate(re.finditer(rb"\x89PNG\r\n\x1a\n|\xff\xd8\xff", data)):
        if i == 0:
            continue  # first image is the preview thumbnail
        try:
            im = Image.open(io.BytesIO(data[m.start():])); im.load()
        except Exception:
            continue
        if im.size[0] < 256:
            continue
        r, g, b = ImageStat.Stat(im.convert("RGB").resize((64, 64))).mean
        if b > 200 and r < 160 and g < 160:
            continue  # normal map
        if best is None or im.size[0] * im.size[1] > best.size[0] * best.size[1]:
            best = im.convert("RGB")
    return best


def make(garment, fabric):
    os.makedirs(CACHE, exist_ok=True)
    key = hashlib.md5((garment + "|" + fabric).encode("utf-8")).hexdigest()[:12]
    out = os.path.join(CACHE, key + ".png")
    if os.path.exists(out):
        return out
    d = _diffuse(garment)
    if d is None:
        return fabric
    lum = ImageOps.grayscale(d)
    detail = ImageStat.Stat(lum.filter(ImageFilter.GaussianBlur(8)).resize((128, 128))).stddev[0]
    if detail < 6:
        return fabric  # plain tiling cloth: fabric works directly
    w, h = d.size
    fab = Image.open(fabric).convert("RGB")
    tile = fab.resize((w // 3, w // 3))
    big = Image.new("RGB", (w, h))
    for y in range(0, h, tile.size[1]):
        for x in range(0, w, tile.size[0]):
            big.paste(tile, (x, y))
    mean = ImageStat.Stat(lum).mean[0] or 1
    shade = lum.point(lambda v: min(255, int(v * 200 / mean)))  # keep folds, seams, stitching
    res = ImageChops.multiply(big, Image.merge("RGB", (shade, shade, shade)))
    res = Image.eval(res, lambda v: min(255, int(v * 1.25)))
    res.save(out)
    return out
