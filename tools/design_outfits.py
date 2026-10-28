# AI outfit designs (2D, for choosing) for a story's characters -> data/designs/<story>/<job>.png + contact sheet.
#   python tools\design_outfits.py <story.json> [job ...]
# Uses Tidmunz Studio's image generator (ChatGPT). Pick the ones you like, then make them 3D (tools\garment_3d.py).
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

P = kit.PROGRAM
sys.path[:0] = [P, os.path.join(P, "snapgen_modules")]
generate_image = kit.image_gen()
from PIL import Image, ImageDraw, ImageFont

story = json.load(open(sys.argv[1], encoding="utf-8-sig"))
only = set(sys.argv[2:])
out = os.path.join(kit.REPO, "data", "designs", story.get("slug", "story"))
os.makedirs(out, exist_ok=True)
done = []
for job, c in story["characters"].items():
    if only and job not in only:
        continue
    who = "%s, %s, %d years old, %s" % (c["name"], ("boy" if c["age"] < 13 else "man") if c["sex"] == "male" else ("girl" if c["age"] < 13 else "woman"), c["age"],
                                        c.get("design", c.get("face", {}).get("บทบาท", "")))
    if "โบราณ" in story.get("era", ""):  # old-Thai folk tale: chong kraben / pha sin, handwoven cotton
        prompt = ("Costume design sheet of ONE complete outfit for a character in an old Thai folk tale "
                  f"(village life in old Siam, about 150-200 years ago): {who}. "
                  "Men wear a chong kraben (โจงกระเบน) wrapped and tucked between the legs, with a plain collarless "
                  "cotton shirt or mor hom style shirt with Chinese knot buttons, or bare chest with a pha khao ma sash; "
                  "women wear a pha sin / pha thung tube skirt with a modest blouse (sleeved, covered). "
                  "Handwoven natural-dyed cotton, muted earthy colors, simple and beautiful, believable for village folk, "
                  "NOT royal, NOT dance costume, no gold unless the character is rich. Barefoot or simple sandals. "
                  "Ghost-mannequin product photo, clothes only, no person, front view, plain light-grey background, "
                  "realistic fabric.")
    else:
        prompt = ("Fashion design sheet of ONE everyday outfit (top + bottom + footwear) for a character in a modern Thai "
                  f"countryside drama: {who}. Real clothes Thai rural people wear today: simple, practical, a bit worn, "
                  "NOT fashion, NOT traditional costume, NO button-up dress shirt, no plaid skirt, no logos. "
                  "Ghost-mannequin product photo, clothes only, no person, front view, plain light-grey background, "
                  "realistic fabric with a real Thai print or plain cotton.")
    try:
        p = generate_image(prompt, output_dir=out, name_hint=job, aspect_ratio="3:4")
        done.append((c["name"], p))
        print("OK", c["name"], p, flush=True)
    except Exception as e:
        print("FAIL", c["name"], str(e)[:120], flush=True)
if done:
    tiles = [Image.open(p).convert("RGB").resize((360, 480)) for _, p in done]
    sheet = Image.new("RGB", (360 * len(tiles), 520), (245, 245, 242))
    d = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(r"C:\Windows\Fonts\leelawui.ttf", 22)
    for i, ((n, _), t) in enumerate(zip(done, tiles)):
        sheet.paste(t, (360 * i, 0))
        d.text((360 * i + 12, 486), n, font=font, fill=(30, 30, 30))
    sheet.save(os.path.join(out, "_sheet.png"))
    print("SHEET", os.path.join(out, "_sheet.png"))
