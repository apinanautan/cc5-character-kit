# Thai folk fabric textures via the program's Prop-page seamless texture prompt.
import os, sys
from PIL import Image, ImageOps
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit
P = kit.PROGRAM; sys.path[:0] = [P, os.path.join(P, "snapgen_modules")]  # image generation = Tidmunz Studio
from snapgen_image_gen import generate_image
OUT = kit.FABRICS  # data/fabrics in the repo
F = {
 "floral_brown": "ผ้าฝ้ายพิมพ์ลายดอกไม้เล็กสีน้ำตาลบนพื้นครีม แบบเสื้อหญิงชาวบ้านไทยสมัยก่อน",
 "floral_red": "ผ้าฝ้ายพิมพ์ลายดอกไม้เล็กสีแดงหม่นบนพื้นขาวนวล แบบผ้าชาวบ้านไทยยุค 80",
 "floral_green": "ผ้าฝ้ายลายดอกไม้เล็กสีเขียวขี้ม้าบนพื้นครีม สีซีดเล็กน้อย",
 "floral_blue_faded": "ผ้าฝ้ายลายดอกไม้เล็กสีฟ้าหม่นซีดบนพื้นขาว",
 "floral_maroon": "ผ้าพิมพ์ลายดอกไม้สีเลือดหมูบนพื้นชมพูอ่อนหม่น",
 "plaid_brown": "ผ้าขาวม้าลายตารางสีน้ำตาลกับครีม ทอมือ",
 "plaid_red": "ผ้าขาวม้าลายตารางสีแดงเข้มกับเขียว ทอมือ สีหม่น",
 "plaid_blue": "ผ้าลายตารางสก๊อตสีน้ำเงินหม่นกับเทา แบบเสื้อเชิ้ตชายชาวบ้าน",
 "mohom": "ผ้าหม้อห้อมสีน้ำเงินคราม ย้อมคราม เนื้อฝ้ายหยาบ",
 "cotton_khaki": "ผ้าฝ้ายเรียบสีกากีหม่น เนื้อหยาบเล็กน้อย",
 "cotton_cream": "ผ้าฝ้ายเรียบสีขาวนวลครีม เนื้อผ้าทอ",
 "cotton_olive": "ผ้าฝ้ายเรียบสีเขียวขี้ม้า",
 "cotton_rust": "ผ้าฝ้ายเรียบสีส้มอิฐหม่น",
 "pha_sin_stripe": "ผ้าซิ่นทอมือลายขวางสีน้ำตาลแดงกับดำ แบบผ้าถุงหญิงไทย",
 "pha_thung_batik": "ผ้าถุงปาเต๊ะลายดอกสีน้ำตาลเข้มกับครีม",
 "pha_thung_green": "ผ้าถุงลายดอกสีเขียวเข้มกับดำ แบบผ้าถุงชาวบ้าน",
 "silk_mudmee": "ผ้าไหมมัดหมี่ลายไทยสีม่วงหม่นกับทอง สำหรับหญิงมีฐานะ",
 "stripe_grey": "ผ้าฝ้ายลายทางเล็กสีเทากับขาว แบบเสื้อเชิ้ตชาย",
}
for name, detail in F.items():
    if os.path.exists(os.path.join(OUT, name + ".png")):
        continue
    prompt = (f"Create one production-ready seamless tileable PBR base-color texture. Material category: ผ้า. Requested surface: {detail}. "
              "Muted natural colors, rural Thailand 1980s, no cartoon, no neon, no bright saturated colors. "
              "Perfectly flat orthographic surface scan, square 1:1, evenly lit, high-frequency material detail, no perspective, no object silhouette, "
              "no folds caused by an object shape, no border, no frame, no text, no watermark, no directional shadow, no highlight hotspot. "
              "The left edge must continue exactly into the right edge and the top edge exactly into the bottom edge. "
              "It must tile repeatedly in all directions without visible seams or dark lines. Base Color only.")
    try:
        p = generate_image(prompt, output_dir=OUT, name_hint=name + "_raw", aspect_ratio="1:1")
        src = Image.open(p).convert("RGB"); w, h = src.size; s = min(w, h)
        small = src.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2)).resize((512, 512))
        t = Image.new("RGB", (1024, 1024)); t.paste(small, (0, 0)); t.paste(ImageOps.mirror(small), (512, 0))
        t.paste(ImageOps.flip(small), (0, 512)); t.paste(ImageOps.flip(ImageOps.mirror(small)), (512, 512))
        t.save(os.path.join(OUT, name + ".png")); print("OK", name, flush=True)
    except Exception as e:
        print("FAIL", name, str(e)[:120], flush=True)
