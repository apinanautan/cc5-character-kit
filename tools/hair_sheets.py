# Contact sheets of the rendered Custom hair files (head close-ups) with "#index + file name" on every tile, for choosing hair by eye.
#   python tools\hair_sheets.py <first index> <last index> [per sheet=20]     -> runs\wardrobe_scan\hair_sheets\hair_<a>_<b>.jpg
import glob, json, os, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, "runs", "wardrobe_scan")
L = json.load(open(os.path.join(S, "cand_custom_hair.json"), encoding="utf-8"))
a, b = int(sys.argv[1]), int(sys.argv[2]); per = int(sys.argv[3]) if len(sys.argv) > 3 else 20
out = os.path.join(S, "hair_sheets"); os.makedirs(out, exist_ok=True)
font = ImageFont.truetype("C:/Windows/Fonts/tahoma.ttf", 16)


def png(i):
    fs = glob.glob(os.path.join(S, "custhair_batch_*", "%03d.png" % i))
    return fs[0] if fs else None


idx = [i for i in range(a, b + 1) if png(i)]
for k in range(0, len(idx), per):
    chunk = idx[k:k + per]; cols = 6; w, h = 300, 410
    rows = (len(chunk) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w, rows * (h + 26)), (24, 25, 28))
    for n, i in enumerate(chunk):
        im = Image.open(png(i)).convert("RGB")
        W, H = im.size
        im = im.crop((W // 2 - 260, 0, W // 2 + 260, H)).resize((w, int(H * w / 520)))   # the whole face (beards / hair over the eyes must show)
        x, y = (n % cols) * w, (n // cols) * (h + 26)
        sheet.paste(im.crop((0, 0, w, h)), (x, y + 26))
        ImageDraw.Draw(sheet).text((x + 4, y + 3), "#%d %s" % (i, os.path.basename(L[i]["rel"])[:30]), fill=(255, 220, 90), font=font)
    p = os.path.join(out, "hair_%03d_%03d.jpg" % (chunk[0], chunk[-1])); sheet.save(p, quality=86); print(p)
