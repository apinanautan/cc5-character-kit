# Make a new seamless fabric texture from a Thai description (through Tidmunz Studio's image generator).
#   path = fabric_ai.make("ผ้าถุงปาเต๊ะลายดอก สีกรมท่า")  -> data/fabrics/gen/<hash>.png (cached)
import hashlib, os, sys
from PIL import Image, ImageOps

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

OUT = os.path.join(kit.FABRICS, "gen")


def name_of(design):
    return "gen/" + hashlib.md5(design.encode("utf-8")).hexdigest()[:10]


def path_of(design):
    return os.path.join(kit.FABRICS, name_of(design) + ".png")


def make(design):
    out = path_of(design)
    if os.path.exists(out):
        return out
    os.makedirs(OUT, exist_ok=True)
    P = kit.PROGRAM
    sys.path[:0] = [P, os.path.join(P, "snapgen_modules")]
    from snapgen_image_gen import generate_image
    prompt = ("Create one production-ready seamless tileable PBR base-color texture. Material category: ผ้า. "
              f"Requested surface: {design} แบบเสื้อผ้าคนไทยต่างจังหวัดยุคปัจจุบัน. "
              "Muted natural colors like clothes washed many times, no cartoon, no logo, no neon, no plaid/tartan. "
              "Pattern scale realistic for clothing (small prints stay small). "
              "Perfectly flat orthographic fabric scan, square 1:1, evenly lit, visible weave, no perspective, no folds, "
              "no border, no frame, no text, no watermark, no shadow, no highlight hotspot. "
              "The left edge must continue exactly into the right edge and the top edge exactly into the bottom edge. Base Color only.")
    p = generate_image(prompt, output_dir=OUT, name_hint=os.path.basename(out)[:-4] + "_raw", aspect_ratio="1:1")
    src = Image.open(p).convert("RGB")
    w, h = src.size
    s = min(w, h)
    small = src.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2)).resize((512, 512))
    t = Image.new("RGB", (1024, 1024))  # mirror-tile -> always seamless
    t.paste(small, (0, 0)); t.paste(ImageOps.mirror(small), (512, 0))
    t.paste(ImageOps.flip(small), (0, 512)); t.paste(ImageOps.flip(ImageOps.mirror(small)), (512, 512))
    t.save(out)
    try:
        os.remove(p)
    except OSError:
        pass
    return out
