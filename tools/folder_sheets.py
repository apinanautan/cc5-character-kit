# One picture per story folder (sheet line): every .iAvatar in the folder (all ages / versions) side by side with its file name under it.
# The pictures come from the preview JPEG stored inside each .iAvatar (no CC5 needed).
#   python tools\folder_sheets.py <story> [drive|desktop]      -> runs\<story>_folder_sheets\<folder name>.jpg
import io, os, re, sys
from PIL import Image, ImageDraw, ImageFont

story = sys.argv[1]; where = sys.argv[2] if len(sys.argv) > 2 else "drive"
root = os.path.join(r"G:\ไดรฟ์ของฉัน", story, story + " ตัวละคร") if where == "drive" else os.path.join(os.path.expanduser("~"), "Desktop", story)
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runs", story + "_folder_sheets")
os.makedirs(out, exist_ok=True)


def font(sz):
    for f in ("C:/Windows/Fonts/tahoma.ttf", "C:/Windows/Fonts/segoeui.ttf"):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def render_for(folder, name):
    """clean front render made in CC5 (tools\...render_avatars.py) if there is one: runs/<story>_renders/<i>.png via list.json"""
    import json
    lst = os.path.join(os.path.dirname(out), story + "_renders", "list.json")
    if not os.path.exists(lst):
        return None
    for e in json.load(open(lst, encoding="utf-8")):
        if e["folder"] == folder and e["name"] == name:
            f = os.path.join(os.path.dirname(lst), "%03d.png" % e["i"])
            if os.path.exists(f):
                im = Image.open(f).convert("RGB")
                import numpy as np
                a = np.asarray(im).astype(int)
                bg = np.median(np.concatenate([a[:8, :8].reshape(-1, 3), a[:8, -8:].reshape(-1, 3), a[-8:, :8].reshape(-1, 3), a[-8:, -8:].reshape(-1, 3)]), axis=0)
                ys, xs = np.where(np.abs(a - bg).sum(2) > 60)
                if len(ys) > 200:
                    im = im.crop((max(0, xs.min() - 16), max(0, ys.min() - 16), min(im.width, xs.max() + 16), min(im.height, ys.max() + 16)))
                return im
    return None


def preview(path):
    b = open(path, "rb").read(6_000_000)
    for m in re.finditer(b"\xff\xd8\xff", b):
        try:
            t = Image.open(io.BytesIO(b[m.start():m.start() + 3_000_000])); t.load()
            if t.width >= 200 and t.height >= 200:
                return t.convert("RGB")
        except Exception:
            pass
    return None


made = []
for folder in sorted(os.listdir(root), key=lambda x: (int(re.match(r"\d+", x).group()) if re.match(r"\d+", x) else 99, x)):
    d = os.path.join(root, folder)
    if not os.path.isdir(d):
        continue
    files = sorted(f for dp, dn, fn in os.walk(d) for f in [os.path.join(dp, x) for x in fn] if f.lower().endswith(".iavatar"))
    tiles = []
    for f in files:
        im = render_for(folder, os.path.basename(f)[:-8]) or preview(f)
        if im is None:
            continue
        h = 620; im = im.resize((int(im.width * h / im.height), h))
        tile = Image.new("RGB", (max(im.width, 260), h + 54), (26, 27, 30)); tile.paste(im, ((tile.width - im.width) // 2, 0))
        ImageDraw.Draw(tile).text((8, h + 8), os.path.basename(f).replace(".iAvatar", ""), fill=(255, 255, 255), font=font(24))
        tiles.append(tile)
    if not tiles:
        continue
    W = sum(t.width for t in tiles) + 12 * (len(tiles) + 1)
    sheet = Image.new("RGB", (W, tiles[0].height + 96), (26, 27, 30))
    ImageDraw.Draw(sheet).text((14, 14), folder, fill=(255, 200, 90), font=font(34))
    x = 12
    for t in tiles:
        sheet.paste(t, (x, 80)); x += t.width + 12
    p = os.path.join(out, folder + ".jpg"); sheet.save(p, quality=88); made.append(p); print(p)
