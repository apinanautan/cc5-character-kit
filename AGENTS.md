# CC5 Characters — UNIVERSAL PROJECT ENTRYPOINT
This project handles hundreds of stories. Do not assume any previous or newest story is active.

## Choose the workflow before starting
- Existing actor, costume, hair or texture revision: use [the one-actor review workflow](docs/production/CC5_EXISTING_ACTOR_REVIEW_FLOW.md). Select one actor and age version by the user’s priority, verify CC5 renders, send the preview, and wait for the user to approve it. Chat approval authorizes only the work within the user’s requested scope; Preview is read-only. Select an explicit single actor or a one-key donor map in the review script.
- For new CC5 previews and iAvatar exports, let skin, hair and cloth textures load after opening the scene, then check that the front view is stable before capturing the image or export thumbnail. See the same review workflow.
- New face or Headshot production: use the Tidmunz face and build workflow below.

Before ANY face, hair, costume, character, image or export task:
1. Verify hostname DESKTOP-F1PJT4S using Dino Tunnel.
2. Read canonical live master: docs/production/THAI_CHARACTER_MASTER.md.
3. Read docs/production/ERA_PROFILES.json, FACE_TIDMUNZ_PIPELINE.md and NTFY_REVIEW.md.
4. Read docs/CHARACTER_QA_STANDARD.md and FACE_GUIDE.md, then the requested story's script/manifest.
5. Confirm the story JSON matches the studio/runner.py schema. Plan face/Headshot via installed Tidmunz Studio when creating a new face.
6. Distinguish epoch/social tier, commoners vs court/royals, business vs rural, historical vs mythology. The user requires Thai faces where story is Thai; never use Western stock CC5 base faces as final.
7. Record every character's source hair/clothing/real color and silhouette in per-story Lookbook. No copied source avatar/clothing meshes merely for cataloging.
8. After each requested face/actor review image render, deliver actual PNG to https://ntfy.sh/Pic-Gptz with verified receipt and dedup.
9. QA Q01-Q10 before marking PASS. Export file exists != visually verified character.
10. Current story/status and project task notes live in PROJECT_MEMORY.md, stories/<slug>.json and runs/<slug>/; do not encode them in the UNIVERSAL rules.
11. Plugin cc5-project-sync is a portable snapshot that references this live master through Dino Tunnel. Disk changes do not mutate packaged plugin; versioned release via Plugin Creator required.
No automation, deletion, restart, forced close of unsaved CC5, background worker or backup unless user specifically authorizes it.
GUI chores (screenshot, hotkeys, popups, file dialogs, save/open): use tools/cc5_gui.ps1 and tools/cc5_popup_guard.ps1, see docs/GUI_TOOLS.md. Do not screenshot-and-click step by step.
## Global executable gate (v1.1.0)
Before work run python tools/cc5_production_preflight.py --story STORY_SLUG --runtime; BLOCKED means stop. Runner enforces schema read-only. Read docs/production/SCHEMA_RUNNER_GATE.md and docs/production/CODE_REALITY_AND_SAFETY.md. Existing tools/plan.py copies assets to job staging and Runner can restart CC5; do not claim zero copies or risk unsaved scenes.
## New face / Headshot production
For new-face jobs, use the Tidmunz face and build flow. Follow the user’s scope and review gates. Run the face and build queues concurrently only when the user has authorized work on multiple new actors. Use one CC5 consumer. Preserve source files and face chat context.
## Deterministic wardrobe policy (code enforced 2026-11-14)
- New actor stories use studio/runner.py:create_story calling tools/cc5_wardrobe_autoplan.py:recommend. Explicit era (modern rural or urban), age, role and real asset paths are required. Every item/hair is locked in runs/STORY/wardrobe_design.json with a reason and original library path.
- tools/plan.py uses tools/cc5_wardrobe_lock.py, with no random fallback. The legacy wardrobe.pick_outfit, wardrobe.pick_hair and runner.reroll APIs have been disabled. Failed AI fabrics do not silently substitute random textures.
- The UI now requires an era choice and says analyze and lock rather than randomize. Historical/royal/ceremonial looks require separately verified period-appropriate assets; the current modern-only auto selector must block rather than guess.
- The rework queue is for technical CC5 processing, not automatic visual QA approval. Inspect actual body renders and front/side/back garment textures, colors and role accuracy. Any ambiguous outfit must be marked FIX, not PASS.
- Prior exported actors remain unchanged; rebuild errors go into separate story/output folders. Do not erase source faces or their chat contexts.
MANDATORY HAIR ART DIRECTION FOR FUTURE STORIES: read docs/production/HAIR_ART_DIRECTION.md and data/hair_catalog_external_g.json; inspect actual thumbnail/crop via gallery or tools/search_hair_catalog.py. GPT designs the hairstyle before searching. No random picker and no rigid cross-story no-reuse rule. External catalog items remain unapproved until rights, file format, CC5 load, and multi-angle visual QA.

## No junk in cc5_jobs (user 2026-11-22)
- cc5_jobs grew to 20 GB. After a GOOD build, `cc5/build.py` step `tidy` deletes the copied library clothes/hair/shoes (item*, hair.rlHair, new*) and `layer_fix/*.obj`, and rewrites job.json `items` to the library originals. It keeps the `.ccProject`, the PNG renders, face.png, job.json and result.txt.
- A build with any FAIL keeps everything for debugging. A copy is deleted only if its library original exists and has the same size.
- plan.py and redress.py record `sources` (copy -> original) in job.json. Do not add new copies that stay in a job.

## Ai-cc5 สำหรับพรีวิวตัวละคร
- ใช้ Ai-cc5 กับตัวละครที่มี .ccProject แล้ว ทำทีละ 1 เรื่อง 1 ตัว 1 ช่วงวัย และเลือก actor key ตามลำดับที่ผู้ใช้กำหนด รัน preflight --runtime เป็นขั้นแรกและหยุดเมื่อ BLOCKED
- ใช้สคริปต์เดิมของเรื่องตามขั้น 1–11 ใน docs/production/CC5_EXISTING_ACTOR_REVIEW_FLOW.md ให้ do ทำทีละขั้น และใช้ do --dry ดูขั้นถัดไปโดยไม่เปลี่ยนไฟล์หรือควบคุม CC5
- CLI และหน้าต่างอ่านสถานะจากฟังก์ชันเดียวกันและเก็บสถานะใน runs เท่านั้น เปอร์เซ็นต์อ้างขั้นที่ยืนยันแล้วและจำนวนหลักฐานจริงในขั้นปัจจุบัน Log ทุกบรรทัดมีเวลาและวินาทีที่ผ่านไป
- สคริปต์ worker ที่เปิดแยกเป็น process ต้องเพิ่ม ROOT ของโปรเจกต์เข้า sys.path ก่อน import namespace `tools`; ทดสอบ import จาก working directory ชั่วคราวเพื่อจับปัญหานี้ก่อนส่งงาน
- ทุกการรอตรวจ process, dialog, ไฟล์หลักฐานหรือใบตอบกลับจริงและมีเส้นตาย เมื่อ FAIL ให้เก็บรายงานล่าสุดพร้อม UIA, OCR และภาพ FAIL หนึ่งรูป ลบภาพชั่วคราวที่ใช้ OCR เมื่ออ่านเสร็จ
- ก่อนเปิดโปรเจกต์ ลองชุด เรนเดอร์ หรือส่งออก ให้บอกผู้ใช้ว่าจะทำอะไรและใช้ do --allow-cc5 เฉพาะเมื่อผู้ใช้อนุญาตขั้นนั้น ห้ามเปิด ปิด หรือรีสตาร์ตโปรแกรม CC5 และห้ามทิ้งงานไม่บันทึก ใช้ cc5_gui.ps1 และ cc5_popup_guard.ps1 กับหน้าจอผ่านการตรวจแบบอ่านอย่างเดียว ไม่มีการคลิกตามพิกัด
- หลังเปิดงานให้เวลา Texture อย่างน้อย 15 วินาทีและตรวจความคงที่ของภาพหน้า จากนั้นลองชุดในโปรเจกต์รอบใหม่ เรนเดอร์หน้า ข้าง หลัง T-Pose และท่าเดินเฟรม 0/24/44 แล้วสร้าง review.png ด้วย make_actor_review.py
- ส่ง review.png ไป Pic-Gptz และตรวจใบยืนยัน attachment ใช้ hash กันส่งซ้ำ ถ้าส่งแล้วแต่ยังไม่ยืนยัน ให้ตรวจปลายทางก่อนส่งอีกครั้ง หยุดจนกว่าผู้ใช้จะกดอนุมัติใน Preview หรือพิมพ์อนุมัติจริงในแชตหลังส่งภาพ หากอนุมัติในแชตใช้ approve --said พร้อมข้อความตรงทุกตัวอักษร
- ส่งออกด้วย --export-reviewed เปิด .iAvatar กลับใน CC5 และตรวจ Q01–Q10 จากหลักฐานจริง การมีไฟล์อย่างเดียวไม่ผ่าน QA ใช้ tidy เฉพาะ staging ของงานที่ตรวจผ่านและ build สำเร็จ
- ตั้งค่าเครื่องใน config.json และใช้ path แบบพกพาในซอร์ส ทดสอบหา drive letter ในซอร์สที่ส่งมอบ เก็บไฟล์ทดลองในโฟลเดอร์ชั่วคราวต่อการรันแล้วลบเมื่อเสร็จ
- เช็ก GitHub Release ได้ไม่ถี่กว่า 10 นาทีต่อครั้ง และอนุญาตให้ติดตั้งเฉพาะไฟล์โปรแกรมที่ระบุ ห้ามเขียนทับ stories/, runs/ และ config.json ด้วยไฟล์จาก release
- รัน unittest โดยไม่เปิด CC5 ก่อนทดสอบจริงต้องถามผู้ใช้

- เรื่องใหม่เริ่มในแท็บเตรียมเรื่องของ Ai-cc5 บันทึกบรีฟ บทวิเคราะห์ Lookbook และผลตรวจไว้ใน runs/<story>/prepare_story/ เปิดพรีวิวเมื่อมีต้นฉบับ CC5 ของตัวละครที่ตรวจแล้ว

- หน้าต่าง Ai-cc5 Preview แสดงเฉพาะเรื่องล่าสุดที่ AI รับงาน ตัวเลขหลักคือจำนวนตัวละคร/ช่วงวัยที่ปิดรอบแล้วจากจำนวนที่ต้องทำทั้งเรื่อง อ่านจากบรีฟหรือ manifest ที่สรุปแล้ว และแสดงช่วงหรือกลุ่มที่ยังไม่ระบุจำนวนตามข้อมูลจริง รายการขั้นและสถานะของแต่ละขั้นยังแสดงในแท็บพรีวิว

## บังคับใช้ Preview แบบติดตามงาน (2026-11-24)
- Preview เป็นหน้าติดตาม ไม่ใช้เลือกงานหรือสั่งเริ่มงานจากหน้าต่าง ยกเว้นปุ่มอนุมัติเมื่อภาพตรวจพร้อม AI รับคำสั่งในแชตและเป็นผู้เดินงานเองผ่าน Ai-cc5 use และ do ทีละขั้นตามลำดับจริง
- ก่อนทำแต่ละขั้นใช้สถานะกำลังทำและบันทึกหลักฐานระหว่างรัน เมื่อผ่านจึงขึ้นขั้นถัดไป ห้ามข้ามขั้น ห้ามปรับตัวเลขให้ผ่านโดยไม่มีหลักฐาน ห้ามทำงานนอกโฟลว์แล้วค่อยย้อนมาเติมสถานะ
- เมื่อรออนุมัติให้ใช้คำตอบจริงในแชต หรือผู้ใช้กดปุ่มอนุมัติใน Preview จริงเท่านั้น ขอบเขตงานและการทำตัวถัดไปยึดคำสั่งผู้ใช้ล่าสุด
- หาก PNG ยังเขียนไม่เสร็จให้นับเป็นหลักฐานที่ยังไม่พร้อม รวมถึง SyntaxError ของ Pillow; ตรวจความสมบูรณ์จริงก่อนผ่านขั้น

- ปุ่มอนุมัติและทำต่อแสดงเฉพาะขั้น approve ที่มี review.png และใบยืนยันส่งภาพตรง hash ของรอบปัจจุบัน กดแล้วซ่อนทันทีและใช้ continuation เดิม ห้าม AI กดแทนผู้ใช้ ช่องเปอร์เซ็นต์ส่วนกลางยังคงมีเพียงช่องเดียว

- Preview: เตรียมเรื่อง 5 ขั้น โดยข้อ 5 ต้องมีไฟล์รายชื่อตัวละคร.rtf ใน out_dir ของเรื่องที่ผู้ใช้กำหนดและตรงกับข้อมูลบรีฟ/สถานะ QA จริง สีดำเมื่อเสร็จครบ สีแดงเมื่อยังไม่เสร็จ ดอกจันเฉพาะตัวละครที่บทระบุว่าสำคัญ ใช้รายชื่อเดียวกันในหน้าต่างและเอกสาร ไม่คัดลอกข้อมูลภายในลงโฟลเดอร์ส่งงาน
- แท็บรูปภาพแสดงเฉพาะภาพของเรื่องปัจจุบันที่มีใบยืนยัน NTFY และตรวจ hash ตรงไฟล์ต้นฉบับ ไม่ส่งภาพซ้ำเพียงเพื่อแสดงผล

- ก่อนสร้างตัวแรกต้องออกแบบสี ลายผ้า ทรงเสื้อ กางเกงและผมเทียบทั้ง cast ตามบท ห้ามใช้ cotton_cream เป็นค่าเริ่มต้นซ้ำโดยไร้เหตุผล; สร้าง texture ใหม่จากผ้าเดิมได้ ตรวจสีจริงจากเรนเดอร์ก่อนอนุมัติ เก็บรอบเดิมไว้หากแก้สี

- เมื่อทำชุดผ่าน AI 3D ให้ลงทะเบียนขั้นจริงของ actor/label ปัจจุบันด้วย tools/ai_cc5_cloth3d.py ตั้งแต่ image -> generate (prompt-id จริง, log, log-offset ก่อนส่ง, output-root) -> mesh_ready (GLB ที่ตรวจได้) -> fit -> render -> complete (หลักฐาน QA) หรือ blocked/cancelled; ห้ามใช้เปอร์เซ็นต์จากงานอื่นหรือเดาจากเวลา. Preview ใช้แถบกลางเดิมแสดงเปอร์เซ็นต์ของขั้นย่อย ไม่เพิ่มแถบใหม่; ลด polygon ก่อน UV/Texture ตามความเหมาะสม; ห้ามให้อนุมัติชุดเก่าขณะชุด AI 3D ยังไม่ผ่านการตรวจ.

- HARD GATE AI GARMENT: ตรวจภาพ T-Pose ต้นแบบ, เรนเดอร์ Mesh ก่อนและหลังลด Polygon/Remesh แบบไม่ใช้ texture และแบบมี texture หน้า/ข้าง/หลังระยะใกล้. ห้ามนำเสื้อที่ขาด ผิวแตก topology เสีย หรือทรงเสียไปฟิต; ไม่บังคับ 12k ถ้าคุณภาพพัง. บันทึก mesh_visual_qa.json พร้อม hash Mesh และภาพจริง; tools/ai_cc5_cloth3d.py fit ต้องผ่าน require_visual_gate ก่อนเริ่ม. หลังฟิตตรวจผิวทะลุและ motion จริง; complete และการส่ง garment_trial/garment_preview ผ่าน NTFY ต้องมี visual QA PASS พร้อม hash ภาพตรวจและ review. FIX ให้แก้ก่อน ห้ามส่งเพื่อให้ผู้ใช้ตรวจข้อผิดพลาดแทน AI. ห้ามใช้จำนวนโพลิกอนหรือการ import สำเร็จเป็นตัวตัดสินคุณภาพ.

- QUALITY-FIRST DECIMATION: 12k เสื้อเป็นเพียงเกณฑ์เตือน ไม่ใช่ target บังคับ. เก็บ Mesh ดิบก่อนลดเสมอ; ทดลองลดแบบอนุรักษ์รูปทรงทีละระดับ ตรวจ geometry และ texture ภาพหน้า/ข้าง/หลังเทียบต้นฉบับแต่ละระดับ; เลือกระดับต่ำสุดที่ยังสมบูรณ์ ไม่ฝืนลดเมื่อขอบ คอ แขน ตะเข็บ ลายผ้า หรือพื้นผิวเริ่มพัง. ถ้าต้นฉบับเสียให้แก้การสร้างก่อน ไม่ฟิต Mesh ที่ไม่ผ่าน. ห้ามส่งชุดที่ไม่ผ่านให้ผู้ใช้อนุมัติ.

- ผู้ใช้กำหนดแนวทางเสื้อ AI 3D ประมาณ 50,000 Faces เป็นเป้าทดลองเริ่มต้น (ไม่ใช่เพดานตายตัว); รักษาคุณภาพก่อนจำนวน Faces และหยุดลดเมื่อทรง/ผิวเริ่มเสีย.

## เมื่อ AI รับงานทำชุดให้ตัวละครหนึ่งตัวจนเรนเดอร์เสร็จ
- ใช้ Preview เดิมติดตามงาน AI อ่าน actor, ช่วงวัย, label และโปรเจกต์เป้าหมายจาก Ai-cc5 ก่อนเริ่ม รอบที่มีอยู่ให้ใช้ do --dry และเทียบกับหลักฐานของชุดที่ขอ หากคำสั่งชี้ไปชุดคนละรอบ ให้หยุดก่อนเปิดฉาก
- สำหรับชุดจากรูป ใช้ STEPS ใน tools/garment_pipeline/flow_preview.py เป็นลำดับปฏิบัติ อ่าน cmd N และกฎของขั้นนั้น ตรวจว่าอินพุตและพาธเป็นของรอบจริง แล้ว AI จึงทำขั้นนั้นเอง บางขั้นเป็นงานตรวจภาพหรือคำสั่งตัวอย่าง ต้องเติมข้อมูลจริงก่อนใช้
- ลำดับงานคือ ตรวจเครื่อง → ออกแบบชุดและระบุรูปต้นแบบ → เตรียมตัวท่า T → สร้างเสื้อและตรวจ mesh → เลือกท่อนล่าง → export ท่า T → จัดแนว → แก้ผ้าทะลุ → ทำ texture และ weight map → ตรวจหน้า/ข้าง/หลัง → ใส่ชุดใน CC5 → ตั้ง physics → เตรียมและโหลดลายผ้า → ตรวจ tiling → ตรวจผมตามวัย → เรนเดอร์ตัวจริงหน้า/ข้าง/หลัง T-Pose และเดินเฟรม 0/24/44 ตรวจภาพ ทำชีต ส่งภาพตามกฎ และบันทึกโปรเจกต์ใหม่
- ก่อนขยับขั้น ตรวจผลจริงของขั้นนั้น ใช้ do ทีละขั้นสำหรับงานหลักและบันทึกสถานะงานชุดของ actor/label เดียวกันตามกฎด้านบน ถ้าผลไม่ผ่านให้แก้ที่ขั้นเดิม รายงานเลขขั้นที่ทำถึง หลักฐาน และสิ่งที่ยังค้าง การเปิด Preview ไม่ใช่การเริ่มงานผลิต

สำหรับงานชุดใหม่ 20 ขั้น (ทำตามลำดับใน gpt_plugin/ai-cc5-garment-flow/SKILL.md; รันขั้นอัตโนมัติด้วย `Ai-cc5 garment run`) ให้ AI ลงทะเบียนรอบผ่าน `Ai-cc5 garment init --source <ccProject> --top-image <PNG> --age <ปี>` อ่านขั้นปัจจุบันผ่าน `garment next` และอ่านกฎรายขั้นผ่าน `garment cmd N` ก่อนเริ่มบันทึก `garment start N` หลังตรวจหลักฐานจริงใช้ `garment done N --note "<หลักฐาน>"` หรือบันทึก `garment fail N --note "<สาเหตุ>"` งานชุดเก่าแสดงเป็นหลักฐานอ้างอิงและแยกจากรอบใหม่ที่ลงทะเบียน
