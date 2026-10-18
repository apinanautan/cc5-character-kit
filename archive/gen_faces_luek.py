# Generate faces for "เลือกนักมักได้แร่" with the program's own Story Face prompt builder.
import ast, json, os, shutil, sys, traceback

P = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio")
sys.path[:0] = [P, os.path.join(P, "snapgen_modules")]
src = open(os.path.join(P, "snapgen_gui_v2.py"), encoding="utf-8").read()
fn = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "_build_story_face_prompt_from_character")
ns = {}; exec(ast.get_source_segment(src, fn), ns)
build = ns["_build_story_face_prompt_from_character"]
from snapgen_image_gen import generate_image

FACE_DIR = os.path.join(os.environ["USERPROFILE"], "Desktop", "Project snapgen.ai", "export", "story_face")
JOBS = os.path.join(P, "snapgen_data", "cc5_jobs")
ERA = "ชาวบ้านไทยต่างจังหวัด ยุคประมาณ 30-40 ปีที่แล้ว"
M, F = "ผมสั้นเรียบแบบชายไทยสมัยก่อน", "ผมดำยาวรวบตึงไปด้านหลัง"
# (job, english name, thai name, fields, ref_job)
C = [
 ("wina_58", "Wina Age 58", "วีนา ตอนอายุ 58", {"อายุ": "58 ปี", "บทบาท": "วีนาตอนแก่ เคยสวยแต่เย่อหยิ่ง ชีวิตไม่ค่อยดี", "สีผิว": "ขาว", "ทรงผม": "ผมดำแซมเทารวบไปด้านหลัง"}, "wina_young"),
 ("lamduan", "Lamduan", "ลำดวน", {"อายุ": "ประมาณ 20 ปี", "บทบาท": "พี่สาวของวีนา " + ERA, "สีผิว": "สีน้ำผึ้ง", "ทรงผม": F, "ใบหน้า": "หน้ากลม อ่อนโยน"}, None),
 ("wandee", "Wandee", "วันดี", {"อายุ": "ประมาณ 21 ปี", "บทบาท": "พี่สาวของวีนา " + ERA, "สีผิว": "สีน้ำผึ้ง", "ทรงผม": F, "ใบหน้า": "หน้ารูปไข่ คิ้วเข้ม ตาโต"}, None),
 ("lamduan_old", "Lamduan Old", "ลำดวน วัยชรา", {"อายุ": "ประมาณ 70 ปี", "บทบาท": "ลำดวนตอนแก่", "สีผิว": "สีน้ำผึ้ง", "ทรงผม": "ผมขาวรวบไปด้านหลัง"}, "lamduan"),
 ("wandee_old", "Wandee Old", "วันดี วัยชรา", {"อายุ": "ประมาณ 70 ปี", "บทบาท": "วันดีตอนแก่", "สีผิว": "สีน้ำผึ้ง", "ทรงผม": "ผมขาวรวบไปด้านหลัง"}, "wandee"),
 ("son_child", "Son Child", "ลูกชาย 5-6 ขวบ", {"อายุ": "5-6 ขวบ", "บทบาท": "ลูกชายของลำดวนกับวันดี เด็กชาวบ้าน", "สีผิว": "สีน้ำผึ้ง", "ทรงผม": "ผมสั้นเกรียนเด็กชาย"}, None),
 ("son_adult", "Son Adult", "ลูกชาย วัย 20+", {"อายุ": "ประมาณ 22 ปี", "บทบาท": "ลูกชายคนเดิมตอนโต", "สีผิว": "สีน้ำผึ้ง", "ทรงผม": M}, "son_child"),
 ("daughter_child", "Daughter Child", "ลูกสาว 5-6 ขวบ", {"อายุ": "5-6 ขวบ", "บทบาท": "ลูกสาวของลำดวนกับวันดี เด็กชาวบ้าน", "สีผิว": "สีน้ำผึ้ง", "ทรงผม": "ผมเด็กหญิงรวบไปด้านหลัง"}, None),
 ("daughter_adult", "Daughter Adult", "ลูกสาว วัย 20+", {"อายุ": "ประมาณ 21 ปี", "บทบาท": "ลูกสาวคนเดิมตอนโต", "สีผิว": "สีน้ำผึ้ง", "ทรงผม": F}, "daughter_child"),
 ("father", "Father", "พ่อ ชาวนา", {"อายุ": "ประมาณ 50 ปี", "บทบาท": "พ่อของวีนา ชาวนา ตากแดดทำนา", "สีผิว": "คล้ำแดด", "ทรงผม": "ผมสั้นสีเทา"}, None),
 ("mother", "Mother", "แม่ ชาวนา", {"อายุ": "ประมาณ 48 ปี", "บทบาท": "แม่ของวีนา ชาวนา", "สีผิว": "สีน้ำผึ้งเข้ม", "ทรงผม": "ผมดำแซมเทารวบไปด้านหลัง"}, None),
 ("soldier", "Soldier", "ทหารหนุ่ม แฟนวันดี", {"อายุ": "ประมาณ 23 ปี", "บทบาท": "ทหารหนุ่ม " + ERA, "สีผิว": "คล้ำ", "ทรงผม": "ผมสั้นเกรียนทหาร", "ใบหน้า": "กรามเหลี่ยม คิ้วหนา"}, None),
 ("somchai", "Somchai", "สมชาย ตำรวจหนุ่ม", {"อายุ": "ประมาณ 25 ปี", "บทบาท": "ตำรวจยศน้อย แฟนลำดวน", "สีผิว": "สองสี", "ทรงผม": "ผมสั้นรองทรง", "ใบหน้า": "หน้ายาว จมูกโด่ง"}, None),
 ("soldier_old", "Soldier Old", "ทหาร วัยชรา", {"อายุ": "ประมาณ 70 ปี", "บทบาท": "ทหารคนเดิมตอนแก่", "สีผิว": "คล้ำ", "ทรงผม": "ผมสั้นสีขาว"}, "soldier"),
 ("somchai_old", "Somchai Old", "สมชาย วัยชรา", {"อายุ": "ประมาณ 72 ปี", "บทบาท": "สมชายตอนแก่", "สีผิว": "สองสี", "ทรงผม": "ผมสั้นสีขาว"}, "somchai"),
 ("pranee", "Pranee", "ปราณี", {"อายุ": "ประมาณ 18 ปี", "บทบาท": "เพื่อนสาวรุ่นเดียวกับวีนา จิตใจดี เรียบง่าย", "สีผิว": "สองสี", "ทรงผม": F, "ใบหน้า": "หน้ากลม ยิ้มง่าย ตาเล็ก"}, None),
 ("pranee_husband", "Pranee Husband", "สามีของปราณี", {"อายุ": "ประมาณ 22 ปี", "บทบาท": "ชายหนุ่มชาวบ้าน ขยัน ซื่อ", "สีผิว": "คล้ำแดด", "ทรงผม": "ผมสั้นแสกข้าง"}, None),
 ("pranee_58", "Pranee Age 58", "ปราณี ตอนอายุ 58", {"อายุ": "58 ปี", "บทบาท": "ปราณีตอนแก่ ชีวิตสุขสบาย", "สีผิว": "สองสี", "ทรงผม": "ผมดำแซมเทารวบไปด้านหลัง"}, "pranee"),
 ("rice_farmer", "Rice Farmer", "ชายหนุ่มชาวนา", {"อายุ": "ประมาณ 22 ปี", "บทบาท": "ชาวนาหนุ่ม " + ERA, "สีผิว": "คล้ำแดด", "ทรงผม": "ผมสั้นยุ่งเล็กน้อย", "ใบหน้า": "หน้าเหลี่ยม จมูกกว้าง"}, None),
 ("chicken_farmer", "Chicken Farmer", "ชายหนุ่มเลี้ยงไก่", {"อายุ": "ประมาณ 24 ปี", "บทบาท": "ชายหนุ่มเลี้ยงไก่ " + ERA, "สีผิว": "สองสี", "ทรงผม": "ผมสั้นเกรียน", "ใบหน้า": "หน้าผอม โหนกแก้มสูง"}, None),
 ("nai_chai", "Nai Chai", "นายใช้", {"อายุ": "ประมาณ 24 ปี", "บทบาท": "ลูกชายเขียงหมู ดูมีเงิน แต่งตัวดี", "สีผิว": "ขาวเหลือง", "ทรงผม": "ผมหวีเรียบแสกข้างแบบยุค 80", "ใบหน้า": "หน้าอวบเล็กน้อย"}, None),
 ("mill_daughter", "Rice Mill Daughter", "ลูกสาวเจ้าของโรงสี", {"อายุ": "ประมาณ 20 ปี", "บทบาท": "ลูกสาวเจ้าของโรงสี มีฐานะ", "สีผิว": "ขาวเหลือง", "ทรงผม": F, "ใบหน้า": "หน้าเรียว ตาชั้นเดียว"}, None),
 ("somphop", "Somphop", "สมภพ ปลัดหนุ่ม", {"อายุ": "ประมาณ 27 ปี", "บทบาท": "ปลัดอำเภอหนุ่ม ดูภูมิฐาน", "สีผิว": "สองสี", "ทรงผม": "ผมสั้นหวีเรียบ", "ใบหน้า": "หน้าคม กรามชัด"}, None),
 ("ratree", "Ratree", "ราตรี", {"อายุ": "ประมาณ 21 ปี", "บทบาท": "ลูกสาวกำนัน", "สีผิว": "สองสี", "ทรงผม": F, "ใบหน้า": "หน้ารูปหัวใจ ตาคม"}, None),
 ("airport_officer", "Airport Officer", "เจ้าหน้าที่สนามบิน", {"อายุ": "ประมาณ 35 ปี", "บทบาท": "เจ้าหน้าที่สนามบิน", "สีผิว": "สองสี", "ทรงผม": "ผมสั้นเรียบร้อย"}, None),
]
only = set(sys.argv[1:])
for job, en, th, fields, ref in C:
    if only and job not in only:
        continue
    d = os.path.join(JOBS, job); os.makedirs(d, exist_ok=True)
    face = os.path.join(d, "face.png")
    if os.path.exists(face):
        continue
    try:
        ch = dict(fields, name=th)
        prompt = build(ch)
        refs = None
        if ref:
            rp = os.path.join(JOBS, ref, "face.png")
            refs = [rp] if os.path.exists(rp) else None
            prompt = ("Same person as the reference photo, aged as described. " if refs else "") + prompt
        p = generate_image(prompt, output_dir=FACE_DIR, name_hint=th.replace(" ", "_") + "_face",
                           aspect_ratio="3:4", ref_images=refs, use_story_face_history=True)
        shutil.copy(p, face)
        json.dump({"name": en, "thai": th, "fields": fields}, open(os.path.join(d, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False)
        print("OK", job, flush=True)
    except Exception:
        print("FAIL", job, traceback.format_exc()[-300:], flush=True)
