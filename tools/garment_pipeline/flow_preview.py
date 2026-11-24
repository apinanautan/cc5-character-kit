"""FLOW ชุดใหม่ (รูปเสื้อ -> 3D -> ใส่ตัวละคร CC5 จริง) แบบทีละสเต็ป - AI ต้องทำตามลำดับนี้เท่านั้น ห้ามดึงสคริปต์มั่ว
ใช้:
  python flow_preview.py <run_dir> init  story=<slug> actor=<key> age=<อายุ> top_image=<รูปเสื้อ> [source=<.ccProject ตัวละคร>]
                                         [bottom_library="Knee length skirt"] [weave=<ลายสาน.png>]
  python flow_preview.py <run_dir>                 ดูทุกสเต็ป: ทำแล้ว / ถึงตรงนี้ / ค้าง + เหตุผล
  python flow_preview.py <run_dir> guide           คู่มือเต็มทุกขั้น (คำสั่ง/ไฟล์/เกณฑ์ตรวจ) ละเอียดยิบ
  python flow_preview.py <run_dir> cmd <N>         พิมพ์คำสั่งจริงของสเต็ป N (เติม path ให้แล้ว) + กฎที่ต้องผ่าน
  python flow_preview.py <run_dir> done <N> [หมายเหตุ]      ทำเสร็จ + ตรวจภาพผ่านแล้ว
  python flow_preview.py <run_dir> fail <N> <เหตุผล>         ค้าง/ไม่ผ่าน (แสดงตัวแดงจนกว่าจะ done)
สถานะเก็บใน <run_dir>/flow_state.json ; ค่าตั้งต้นใน <run_dir>/flow_config.json
ทุกสเต็ป: เขียนไฟล์ใหม่เท่านั้น ห้ามทับต้นฉบับ ห้ามบันทึก .ccCloth ห้ามรัน CC5 กับ Blender งานหนักพร้อมกัน
ทุกภาพที่ต้องตรวจ -> ส่ง ntfy Pic-Gptz (ชื่อภาพภาษาไทย) ; คุยกับผู้ใช้ภาษาไทย"""
import json
import os
import sys
import time
from pathlib import Path
GP = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(GP))
VPY = os.path.join(GP, ".venv", "Scripts", "python.exe")
BL = r'"C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" -b --factory-startup -P'
WEAVE = r"G:\คอมพิวเตอร์เครื่องอื่นๆ\คอมพิวเตอร์ของฉัน\โมชั่น\Prop ของใช้ต่างๆ\เสื้อผ้า-ทรงผม\ลายผ้า\HS 4K Fabric Shaders 3\HS4kFS3_Clothtex06.png"

# (id, ชื่อสเต็ป, คำสั่ง (format ด้วย config), ไฟล์ที่ต้องมี (relative run_dir), กฎ/สิ่งที่ต้องตรวจ, ต้องตรวจภาพด้วยตาไหม)
STEPS = [
 ("preflight", "ตรวจเครื่อง + story ก่อนเริ่ม",
  'python "{ROOT}\\tools\\cc5_production_preflight.py" --story {story} --runtime', [],
  "BLOCKED = หยุดทันที. hostname ต้องเป็น DESKTOP-F1PJT4S", False),
 ("design", "ตัดสินใจ + ออกแบบชุดตามยุค/อาชีพ/อายุ",
  '& "{VPY}" outfit_flow.py design --story {story} --actor {actor_key} --run-dir "{RUN}"', ["design.json"],
  "ยุค/ชนชั้น/อาชีพ/อายุตรงเรื่อง (เช่น ช่างเสริมสวย ในเมือง พ.ศ.2539). เปิด design.json ดูผ้า/สีก่อน", False),
 ("prep_body", "CC5: บันทึกฉากเดิมเป็นไฟล์ใหม่ -> เปิดตัวละคร -> ถอดเสื้อเดิม -> ท่า T -> export ตัว",
  'python cc5call.py cc5\\prep_body.py "source={source}" "out={RUN}" preserve= upper=auto', ["body_tpose.obj"],
  "ห้ามปิด/รีสตาร์ท CC5 ที่ยังไม่ได้เซฟ. body_tpose.obj ต้องเป็น Z-up", False),
 ("ref_image", "3D AI ①: รูปต้นแบบเสื้อ — หน้าตรง พื้นขาว ไม่มีคน เห็นปก/กระดุม/แขน/ชายครบ",
  '& "{VPY}" qwen_edit.py --image "{top_image}" --out "{RUN}\\top_ref_clean.png" --long 2048 --seed 1 --prompt "front view of the same garment only, flat lay, pure white background, no person, no mannequin, no hanger, perfectly symmetric, full collar, all buttons, both sleeves and the whole hem visible, keep the exact fabric print, colours and button count"',
  ["top_ref_clean.png"],
  "ตรวจ top_ref_clean.png ก่อนไปต่อ (AI 3D เดาจากรูปนี้รูปเดียว รูปแย่ = เสื้อแย่):"
  " (1) ทรง/ความยาวแขน/ความยาวชาย/ปก ตรงรูปต้นฉบับ {top_image}"
  " (2) จำนวนกระดุมเท่าเดิม (3) ไม่มีมือ ไม่มีคน ไม่มีเงา ไม่มีรอยพับหนัก (4) สมมาตรซ้ายขวา"
  " (5) ลายผ้า/สีเหมือนเดิม. ไม่ผ่าน = รันใหม่ด้วย --seed 2,3 เขียนไฟล์ใหม่ (top_ref_clean_s2.png) แล้วแก้ top_image ใน config"
  " / ถ้ารูปต้นฉบับเป็นหน้าตรงพื้นขาวอยู่แล้ว ให้ copy มาเป็น top_ref_clean.png ได้เลย", True),
 ("ai_3d", "3D AI ②: Hunyuan3D 2.1 (octree 512) → ปิดรู → วางบนตัว → tightfit → ดันออกนอกผิว → smooth push",
  '& "{VPY}" make_garment.py --image "{RUN}\\top_ref_clean.png" --run "{RUN}\\top_build" --body "{RUN}\\body_tpose.obj" --name {actor}_top --faces 100000 --seed 0 --stop_before qc',
  ["top_build/final.obj"],
  "สคริปต์หยุดเองถ้าไม่ผ่านเกณฑ์อัตโนมัติ: clean = ไม่มีรู (boundary 0, nonmanifold 0);"
  " tightfit = ผิวห่างผ้า median < 2.5 cm; push = ผ้าในตัว < 1% และขยับ < 5 cm (เกินนี้ทรงเพี้ยน);"
  " smooth = กลับเข้าในตัว < 1%. หยุด = จดสาเหตุด้วย fail แล้วลอง --seed 1/2 ใน --run top_build_s1 / top_build_s2 (ห้ามทับ top_build เดิม)."
  " ห้ามรัน CC5 งานหนักพร้อมกัน", False),
 ("ai_shape_qc", "3D AI ③: ตรวจทรงเสื้อ AI บนตัวจริง หน้า/ข้าง/หลัง/ซูมอก/ซูมข้าง",
  '& {BL} blender\\qc_on_body.py -- "{RUN}\\body_tpose.obj" "{RUN}\\top_build\\final.obj" "{RUN}\\top_build\\qc_"',
  ["top_build/qc_front.png"],
  "เทียบกับ top_ref_clean.png ทีละข้อ แล้วส่ง ntfy (ชื่อภาพภาษาไทย):"
  " (1) ปกตรงคอ ไม่ลอย ไม่จมคอ (2) ไหล่ตรงไหล่ ไม่ยกเป็นนวม (3) แขนเสื้อยาวตามรูป ไม่บิด ไม่แบน"
  " (4) ชายเสื้อยาวตามรูป เสมอกันรอบตัว (5) ไม่ทะลุผิวทุกมุม (รักแร้/สะบัก/หน้าอก)"
  " (6) ด้านหลังไม่ยุบ ไม่มีหลุม ไม่มีหนาม (7) ผ้าหนาสม่ำเสมอ ไม่มีแผ่นซ้อน."
  " ข้อไหนไม่ผ่าน = fail + กลับขั้น ai_3d ด้วย seed ใหม่ ห้ามซ่อมด้วยมือ", True),
 ("top", "3D AI ④: ผิวเรียบ + เก็บตะเข็บเป็น normal map + กระดุมจริง (ขอบ + รู 4 รู)",
  '& "{VPY}" outfit_flow.py make --story {story} --actor {actor_key} --run-dir "{RUN}" --body "{RUN}\\body_tpose.obj" --top_mesh "{RUN}\\top_build\\final.obj" --only top',
  ["top_buttons.obj", "top_normal.png"],
  "ตรวจ qc_bake_*.png และ qc_btn_*.png: ผิวเรียบไม่มีรอยยับจาก AI แต่ตะเข็บ/ปก/ขอบแขนยังเห็นใน normal map;"
  " จำนวนกระดุม = จำนวนในรูป (buttons found ใน log) ถ้าไม่เท่า = fail; กระดุมเรียงแนวกลางอก ระยะเท่ากัน;"
  " ทุกเม็ดมีขอบ + รู 4 รูชัด ไม่เป็นก้อนดำ; กระดุมไม่ลอย ไม่จม", True),
 ("bottom", "ท่อนล่าง: ใส่ของคลัง CC5 (แนะนำ) ใน CC5 > Content เช่น '{bottom_library}'",
  'ใส่ "{bottom_library}" จาก CC5 Content > Skirts ด้วยมือ/สคริปต์ แล้วรันสเต็ปต่อไป  (สร้างเอง: "{VPY}" outfit_flow.py make ... --only bottom)', [],
  "กระโปรงสร้างเองเคยเป็นคลื่นข้าง/เป็นชั้นเหมือนตึก -> ผู้ใช้เลือกของคลัง. ถ้าสร้างเอง: ห้ามเป็นชั้น ห้ามเป็นคลื่น", True),
 ("export_tpose", "CC5: export ตัว+กระโปรงที่ใส่จริงในท่า T",
  'python cc5call.py cc5\\export_tpose.py "out={RUN}\\cc5_library_bottom\\worn_tpose.obj" pose_after=A-Pose', ["cc5_library_bottom/worn_tpose.obj"],
  "ไม่ทับไฟล์เดิม (สคริปต์ปฏิเสธถ้ามีแล้ว). จบแล้วกลับ A-Pose", False),
 ("align", "จัดแนว export ให้ตรง body_tpose (CC5 หมุน ~173 องศา)",
  '& {BL} blender\\align_export.py -- "{RUN}\\body_tpose.obj" "{RUN}\\cc5_library_bottom\\worn_tpose.obj" "{RUN}\\cc5_library_bottom\\worn_tpose_aligned.obj"',
  ["cc5_library_bottom/worn_tpose_aligned.obj"], "error ต้อง < 1 cm ไม่งั้นสคริปต์หยุด", False),
 ("push", "ดันเสื้อให้อยู่นอกตัว+นอกกระโปรง (แก้ทะลุเอวหลัง + กันผิวในโผล่ออกนอก THICK 1.2)",
  '& {BL} blender\\push_layers.py -- "{RUN}\\top_buttons.obj" "{RUN}\\cc5_library_bottom\\worn_tpose_aligned.obj" "{RUN}\\cc5_library_bottom\\top_final.obj" 0.5 CC_Base_Body,{bottom_group}',
  ["cc5_library_bottom/top_final.obj"],
  "ห้ามเสื้อทะลุกระโปรงด้านหลังเอว, ห้ามผิวในกับผิวนอกทับกันจน texture พัง", False),
 ("fabric", "ลายผ้า diffuse + normal กระดุม + weight map physics (ชายเสื้อ/รักแร้)",
  '& "{VPY}" outfit_flow.py make --story {story} --actor {actor_key} --run-dir "{RUN}" --body "{RUN}\\body_tpose.obj" --only fabric --top-final "{RUN}\\cc5_library_bottom\\top_final.obj"',
  ["top_diffuse.png", "top_normal_btn.png", "top_physics_wmap.png"],
  "ลายผ้าจากรูปจริงที่ผู้ใช้เลือก, กระดุมสีของมันเอง. *** ตรวจว่า fabric ใช้ top_final ตัวล่าสุด (ถ้าใช้ของ cc5_library_bottom ให้ส่ง path นั้น) ***", False),
 ("qc_blender", "Blender QC ภาพหน้า/ข้าง/หลัง บนตัว+กระโปรงที่ align แล้ว",
  '& {BL} blender\\qc_outfit.py -- "{RUN}\\cc5_library_bottom\\worn_tpose_aligned.obj" "{RUN}\\cc5_library_bottom\\qc_" "{RUN}\\cc5_library_bottom\\top_final.obj|{RUN}\\top_diffuse.png|{RUN}\\top_normal_btn.png"',
  ["cc5_library_bottom/qc_front.png", "cc5_library_bottom/qc_side.png", "cc5_library_bottom/qc_back.png"], "ไม่ทะลุ ไม่มีจุดกระโปรงโผล่ผ่านเสื้อ, ส่ง ntfy", True),
 ("wear", "CC5: ใส่เสื้อเข้าตัวละคร (OBJ Y-up, Transfer Skin Weight)",
  'python cc5call.py cc5\\wear_placed.py "obj={RUN}\\cc5_library_bottom\\top_final.obj" "out={RUN}\\cc5" name={actor}_top "diffuse={RUN}\\top_diffuse.png" "normal={RUN}\\top_normal_btn.png"',
  [], "OBJ ต้อง Y-up. ห้ามบันทึก .ccCloth. ตรวจภาพท่าต่างๆ", True),
 ("physics", "physics บางๆ: ชายเสื้อ + รักแร้นิดเดียว + ชายกระโปรง (ไม่หนัก ไม่พลิ้ว)",
  'python cc5call.py cc5\\set_physics.py "cloths={actor}_top|{RUN}\\top_physics_wmap.png;{bottom_library}|-" "out={RUN}\\cc5" save={actor}_outfit_physics_on_character.ccProject',
  [], "ค่า CC5 scale: Mass1 Damping0.5 Drag0.1 Inertia4 Bending30 Stretch1 Elasticity15 (ค่าผิด scale = ผ้าย้วย)", True),
 ("weave_files", "เตรียมลายสาน: Roughness = รูปเดิม(ขาว), Metallic = รูปเดียวกัน invert (ดำ)",
  '& "{VPY}" tile_texture.py --invert "{weave}" "{RUN}\\weave_metal_invert.png"', ["weave_metal_invert.png"],
  "ต้องเป็นรูปเดียวกัน กลับสีกันเท่านั้น (rough+metal=255) ห้ามคนละรูป ห้ามแค่ทำให้มืด", False),
 ("weave_load", "CC5: โหลดลายสานเข้า Roughness/Metallic + โหลดลายดอกกลับเป็นอย่างสุดท้าย",
  'python cc5call.py cc5\\set_fabric_pbr.py cloth={actor}_top "rough={weave}" "metal={RUN}\\weave_metal_invert.png" "diffuse={RUN}\\top_diffuse.png" "out={RUN}\\cc5"',
  [], "BRIDGE_RESULT ต้องเห็น rough=(ขนาดรูปลายสาน) ไม่ใช่รูปอื่น และ diffuse ยังเป็นลายดอก", True),
 ("tiling", "CC5: Tiling 25 ช่อง Roughness + Metallic (ผ่านแผง Modify > Texture Settings เพราะ API เข้า Roughness ไม่ได้)",
  'python cc5call.py cc5\\set_channel_tiling_ui.py channel=Roughness tile=25\npython cc5call.py cc5\\set_channel_tiling_ui.py channel=Metallic tile=25',
  [], "ต้องเลือกเสื้อ + เปิดแผง Texture Settings ไว้. readback ต้อง Roughness=25, Metallic=25, Base Color=1", False),
 ("hair", "ทรงผม/สีผมตามอายุ",
  'ตรวจสีผมจากภาพหน้า/ข้าง/หลัง (อายุ {age}: ต้องเป็น {hair_rule})', [],
  "ผมเน้นแค่ 2 แบบ: ดำ (อายุ < 50) หรือ ดำมีผมงอกขาว/เทาเงิน (อายุ >= 50). ห้ามน้ำตาล/ทอง/สีอื่น ถ้าไม่ตรง = FIX และแก้ใน CC5 ก่อนตรวจซ้ำ ขั้นนี้ยังไม่มีสคริปต์ย้อมสีอัตโนมัติ", True),
 ("final", "บันทึก .ccProject ใหม่ → เรนเดอร์หน้า/ข้าง/หลังและท่าเดิน → ทำชีต → ส่ง Pic-Gptz",
  'python cc5call.py cc5\\save_new.py "save={RUN}\\cc5\\{actor}_outfit_final.ccProject"  แล้วรัน qa_cast_runtime.py กับไฟล์ใหม่นี้เพื่อเก็บหน้า/ข้าง/หลัง T-Pose และเดินเฟรม 0/24/44 จากนั้นใช้ make_actor_review.py และส่งผ่านฟังก์ชัน ntfy_send ของโปรเจกต์ตามเกณฑ์ตรวจภาพ',
  ["cc5/{actor}_outfit_final.ccProject", "review.png"], "QA Q01-Q10 ก่อน PASS. ไฟล์มีอยู่ != ตรวจภาพแล้ว. ห้ามทับไฟล์เดิม", True),
]


AI_SUBSTEPS = ("ref_image", "ai_3d", "ai_shape_qc")   # added 2026-11-25; runs that already finished "top" count them as done


def record_of(records, key):
    if key in AI_SUBSTEPS and key not in records and records.get("top", {}).get("status") == "done":
        return {"status": "done", "note": "ผ่านมาก่อนแตกขั้นย่อย 3D AI (รวมอยู่ในขั้นเสื้อเดิม)"}
    return records.get(key, {})


def load(p, d):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return d


def progress_rows(run, cfg, state):
    folder = Path(run)
    legacy = {
        "export_tpose": ["cc5_library_skirt/worn_tpose.obj"],
        "align": ["cc5_library_skirt/worn_tpose_aligned.obj"],
        "push": ["cc5_library_skirt/top_over_kneeskirt.obj"],
        "qc_blender": [f"cc5_library_skirt/qc_overskirt_{view}.png" for view in ("front", "side", "back")],
    }
    rows = []
    for key, title, _, expected, _, visual in STEPS:
        expected = [path.format(actor=cfg.get("actor", "<actor>")) for path in expected]
        record = record_of(state, key)
        status = {"fail": "ค้าง", "done": "ยืนยันแล้ว", "start": "กำลังทำ"}.get(record.get("status"))
        if not status:
            groups = [expected] if cfg.get("label") else [expected, legacy.get(key, [])]
            found = any(group and all((folder / f).is_file() and (folder / f).stat().st_size
                                      for f in group) for group in groups)
            status = ("รอตรวจภาพ" if visual else "พบไฟล์") if found else "รอหลักฐาน"
        rows.append((title.format(bottom_library=cfg.get("bottom_library", "Knee length skirt")),
                     status, record.get("note", "")))
    return rows


def progress_text(run, cfg, state):
    rows = progress_rows(run, cfg, state)
    pending = next((i for i, (_, status, _) in enumerate(rows, 1)
                    if status != "ยืนยันแล้ว"), None)
    confirmed = sum(status == "ยืนยันแล้ว" for _, status, _ in rows)
    available = sum(status in ("พบไฟล์", "รอตรวจภาพ") for _, status, _ in rows)
    lines = [f"ยืนยันแล้ว {confirmed}/{len(rows)} ขั้น · พบไฟล์อีก {available} ขั้น",
             f"ขั้นแรกที่รอดำเนินการหรือยืนยัน · {pending}" if pending else "มีผลครบทุกขั้น", ""]
    for i, (title, status, note) in enumerate(rows, 1):
        lines.append(f"{i:02d}  [{status}]  {title}")
        if note:
            lines.append(f"      {note}")
    return "\n".join(lines)


def command_text(run, cfg, number):
    if not 1 <= number <= len(STEPS):
        raise ValueError(f"ระบุขั้น 1–{len(STEPS)}")
    _, title, command, expected, rule, visual = STEPS[number - 1]
    story = cfg.get("story", "<story>")
    actor = cfg.get("actor", "<actor>")
    age = int(cfg.get("age", 30))
    library = cfg.get("bottom_library", "Knee length skirt")
    values = dict(RUN=run, ROOT=ROOT, VPY=VPY, BL=BL, story=story, actor=actor,
                  actor_key=actor if actor.startswith(story + "_") else f"{story}_{actor}",
                  top_image=cfg.get("top_image") or "<รูปเสื้อ>", source=cfg.get("source") or "<.ccProject>",
                  bottom_library=library, weave=cfg.get("weave") or WEAVE, age=age,
                  hair_rule="ดำมีผมงอกขาว (เทาเงิน)" if age >= 50 else "ดำล้วน",
                  bottom_group=cfg.get("bottom_group") or "_".join([library.replace(" ", "_")] * 2))
    expected = [path.format(**values) for path in expected]
    return "\n".join((f"ขั้น {number}/{len(STEPS)} · {title.format(**values)}",
                      f"โฟลเดอร์คำสั่ง · {GP}", command.format(**values),
                      f"ไฟล์ที่ต้องได้ · {', '.join(expected) or 'บันทึกหลักฐานจากงานจริง'}",
                      f"ตรวจภาพด้วยตา · {'ต้อง' if visual else 'ไม่บังคับ'}",
                      f"กฎ · {rule.format(**values)}"))


def read_flow(store, state):
    if not state.get("actor") or not state.get("label"):
        return None
    story, actor = state["story"], state["actor"]
    active = store.folder(state) / "garment"
    config = load(active / "flow_config.json", None)
    if config is not None:
        if (config.get("story"), config.get("actor"), config.get("label")) != (story, actor, state["label"]):
            raise ValueError("งานชุดไม่ตรงตัวละครหรือรอบใน Preview")
        return active, config, load(active / "flow_state.json", {})
    key = actor if actor.startswith(story + "_") else f"{story}_{actor}"
    legacy = store.runs / story / "outfits" / key
    return legacy, {"story": story, "actor": actor, "age": int(str(state.get("age") or 30).split()[0])}, {}


def next_number(records):
    return next((i for i, (key, *_) in enumerate(STEPS, 1)
                 if record_of(records, key).get("status") != "done"), None)


def pending_before_review(store, state):
    flow = read_flow(store, state)
    if flow and flow[1].get("label"):
        number = next_number(flow[2])
        if number is not None and STEPS[number - 1][0] != "final":
            return number
    return None


MANUAL = {"bottom", "hair", "final"}      # these need a person/eye or a multi-tool sequence; `run` refuses them


def run_step(store, args):
    """Ai-cc5 garment run: execute the CURRENT step's command, stream its output into the Ai-cc5 log (the preview
    window shows it live), then record done / fail / waiting-for-eye-check automatically."""
    import subprocess
    from ai_cc5_state import Blocked, lock, save, png
    with lock(store.runs / ".ai_cc5.lock"):
        state = store.active(); flow = read_flow(store, state)
        if not flow or not flow[1].get("label"):
            raise Blocked("ลงทะเบียนรอบชุดด้วย Ai-cc5 garment init ก่อน")
        run, cfg, records = flow
        number = next_number(records)
        if number is None:
            print(f"ยืนยันครบ {len(STEPS)} ขั้นแล้ว"); return 0
        key, title, command, expected, _, visual = STEPS[number - 1]
        if record_of(records, key).get("status") == "start" and visual:
            raise Blocked(f"ขั้น {number} รันแล้ว รอตรวจภาพ · ตรวจแล้วใช้ garment done {number} --note \"...\"")
        if key in MANUAL:
            raise Blocked(f"ขั้น {number} ({key}) ต้องทำ/ตรวจด้วยคน · ดูคำสั่งด้วย garment next แล้วใช้ garment start/done")
        lines = command_text(run, cfg, number).splitlines()[2:]
        text = "\n".join(lines[:next(i for i, l in enumerate(lines) if l.startswith("ไฟล์ที่ต้องได้"))])
        records[key] = {"status": "start", "note": "สคริปต์กำลังรัน", "time": time.strftime("%Y-%m-%d %H:%M:%S")}
        save(run / "flow_state.json", records)
        store.log(state, f"งานชุด · ขั้น {number}/{len(STEPS)} · เริ่ม · {title}")
        store.log(state, text)
    logs = run / "garment_logs"; logs.mkdir(parents=True, exist_ok=True)
    log_path = logs / f"{number:02d}_{key}_{time.strftime('%Y%m%d_%H%M%S')}.log"
    started = time.monotonic()
    with log_path.open("wb") as out, log_path.open("rb") as reader:
        proc = subprocess.Popen(["pwsh", "-NoProfile", "-NonInteractive", "-Command", text], cwd=GP, stdout=out,
                                stderr=subprocess.STDOUT, env=os.environ | {"PYTHONIOENCODING": "utf-8"},
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        while True:
            done = proc.poll() is not None
            chunk = reader.read().decode("utf-8", errors="replace")
            for line in chunk.splitlines()[-6:]:
                if line.strip(): store.log(state, f"  ขั้น {number} › {line.strip()[:200]}")
            if done: break
            time.sleep(2)
    tail = log_path.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-4:]
    secs = round(time.monotonic() - started)
    with lock(store.runs / ".ai_cc5.lock"):
        records = load(run / "flow_state.json", {})
        files = [path.format(actor=cfg["actor"]) for path in expected]
        missing = [f for f in files if not (run / f).is_file() or not (run / f).stat().st_size
                   or (f.endswith(".png") and not png(run / f))]
        if proc.returncode or missing:
            why = f"exit {proc.returncode}" if proc.returncode else "ไม่มีไฟล์ " + ", ".join(missing)
            records[key] = {"status": "fail", "note": f"{why} · {' | '.join(tail)[:300]} · log {log_path.name}",
                            "time": time.strftime("%Y-%m-%d %H:%M:%S")}
            verdict = "ค้าง · " + why
        elif visual:
            records[key] = {"status": "start", "note": f"สคริปต์ผ่าน {secs} วิ · รอตรวจภาพ แล้วใช้ garment done {number}",
                            "time": time.strftime("%Y-%m-%d %H:%M:%S")}
            verdict = "สคริปต์ผ่าน · รอตรวจภาพ"
        else:
            records[key] = {"status": "done", "note": f"สคริปต์ผ่าน {secs} วิ · {' | '.join(tail)[:200]}",
                            "time": time.strftime("%Y-%m-%d %H:%M:%S")}
            verdict = "ผ่าน"
        save(run / "flow_state.json", records)
        store.log(state, f"งานชุด · ขั้น {number}/{len(STEPS)} · {verdict} ({secs} วิ)")
        print(progress_text(run, cfg, records))
    return 0 if records[key]["status"] != "fail" else 1


def cli(store, args):
    from ai_cc5_state import Blocked, lock, save, png
    if args.action == "run":
        return run_step(store, args)

    with lock(store.runs / ".ai_cc5.lock"):
        state = store.active()
        flow = read_flow(store, state)
        if not flow:
            raise Blocked("เลือกเรื่องและตัวละครด้วย Ai-cc5 use ก่อน")
        run, cfg, records = flow
        active = store.folder(state) / "garment"
        if args.action == "init":
            if run == active:
                raise Blocked("รอบนี้มีงานชุดแล้ว")
            if not args.source.is_file() or args.source.suffix.lower() != ".ccproject" or not png(args.top_image):
                raise Blocked("ต้องระบุโปรเจกต์ CC5 และรูปเสื้อ PNG ที่เปิดได้")
            save(active / "flow_config.json", {**cfg, "label": state["label"], "age": args.age,
                 "source": str(args.source.resolve()), "top_image": str(args.top_image.resolve()),
                 "bottom_library": args.bottom_library, "weave": str(args.weave.resolve()) if args.weave else WEAVE})
            store.log(state, f"งานชุด · ลงทะเบียน {len(STEPS)} ขั้นสำหรับรอบนี้")
            run, cfg, records = read_flow(store, state)
        number = args.number if hasattr(args, "number") else next_number(records)
        if args.action in ("cmd", "next"):
            if run != active:
                print("ยังไม่ได้ลงทะเบียนรอบชุด · ใช้ Ai-cc5 garment init ก่อนรันคำสั่ง")
            print(command_text(active, cfg, number) if number is not None else f"ยืนยันครบ {len(STEPS)} ขั้น")
            return 0
        if args.action in ("start", "fail", "done"):
            if run != active or number != next_number(records) or not number:
                raise Blocked("เริ่มงานชุดด้วย garment init และบันทึกเฉพาะขั้นปัจจุบัน")
            key, _, _, expected, _, _ = STEPS[number - 1]
            expected = [path.format(actor=cfg["actor"]) for path in expected]
            if args.action == "done":
                if records.get(key, {}).get("status") != "start":
                    raise Blocked("ใช้ garment start ก่อนเริ่มทำขั้นนี้")
                missing = [f for f in expected if not (run / f).is_file() or not (run / f).stat().st_size
                           or (f.endswith(".png") and not png(run / f))]
                if missing:
                    raise Blocked("หลักฐานยังไม่ครบ · " + ", ".join(missing))
            note = args.note.strip()
            if args.action != "start" and not note:
                raise Blocked("ระบุหลักฐานที่ตรวจหรือสาเหตุที่ค้าง")
            records[key] = {"status": args.action, "note": note, "time": time.strftime("%Y-%m-%d %H:%M:%S")}
            save(run / "flow_state.json", records)
            store.log(state, f"งานชุด · ขั้น {number}/{len(STEPS)} · {args.action} · {note}")
        print(progress_text(run, cfg, records))
        return 0


def add_cli(parser):
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("status")
    commands.add_parser("next")
    commands.add_parser("run")
    commands.add_parser("cmd").add_argument("number", type=int)
    init = commands.add_parser("init")
    init.add_argument("--source", required=True, type=Path)
    init.add_argument("--top-image", required=True, type=Path)
    init.add_argument("--age", required=True, type=int)
    init.add_argument("--bottom-library", default="Knee length skirt")
    init.add_argument("--weave", type=Path)
    for action in ("start", "fail", "done"):
        step = commands.add_parser(action)
        step.add_argument("number", type=int, choices=range(1, len(STEPS) + 1))
        step.add_argument("--note", default="", required=action != "start")


def main():
    if len(sys.argv) < 2: print(__doc__); return
    run = os.path.abspath(sys.argv[1]); a = sys.argv[2:]
    cp, sp = os.path.join(run, "flow_config.json"), os.path.join(run, "flow_state.json")
    cfg, st = load(cp, {}), load(sp, {})
    if cfg.get("label") and a and a[0] in ("init", "done", "fail"):
        raise SystemExit("รอบนี้จัดการผ่าน Ai-cc5 garment เพื่อบันทึกสถานะตามลำดับ")
    if a and a[0] == "init":
        cfg.update(dict(kv.split("=", 1) for kv in a[1:]))
        cfg.setdefault("bottom_library", "Knee length skirt"); cfg.setdefault("weave", WEAVE); cfg.setdefault("source", "")
        os.makedirs(run, exist_ok=True); json.dump(cfg, open(cp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("saved", cp); a = []
    age = int(cfg.get("age", 30))
    v = dict(cfg, RUN=run, ROOT=ROOT, VPY=VPY, BL=BL, story=cfg.get("story", "<story>"), actor=cfg.get("actor", "<actor>"),
             top_image=cfg.get("top_image", "<รูปเสื้อ>"), source=cfg.get("source", "<.ccProject>"),
             bottom_library=cfg.get("bottom_library", "Knee length skirt"), weave=cfg.get("weave", WEAVE), age=age,
             hair_rule="ดำมีผมงอกขาว (เทาเงิน)" if age >= 50 else "ดำล้วน")
    v["bottom_group"] = cfg.get("bottom_group", "_".join([v["bottom_library"].replace(" ", "_")] * 2))
    ids = [s[0] for s in STEPS]
    if a and a[0] in ("done", "fail"):
        n = int(a[1]) - 1; st[ids[n]] = dict(status=a[0], note=" ".join(a[2:]), time=time.strftime("%Y-%m-%d %H:%M"))
        json.dump(st, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1); a = []
    if a and a[0] == "guide":      # คู่มือเต็มทุกขั้น ละเอียดยิบ (คำสั่ง + ไฟล์ที่ต้องได้ + เกณฑ์ตรวจ)
        print("\n\n".join(command_text(run, cfg, n) for n in range(1, len(STEPS) + 1)))
        return
    if a and a[0] == "cmd":
        print(command_text(run, cfg, int(a[1])))
        return
    print("FLOW ชุดใหม่: %s / %s  อายุ %d  (ผม: %s)\n" % (v["story"], v["actor"], age, v["hair_rule"]))
    print(progress_text(run, cfg, st))


if __name__ == "__main__":
    main()
