# PROJECT MEMORY — LIVE WORK STATUS (not global policy)
GLOBAL POLICY: docs/production/THAI_CHARACTER_MASTER.md (version 1.1.0).
ERA PROFILES: docs/production/ERA_PROFILES.json.
FACE (Tidmunz Studio): docs/production/FACE_TIDMUNZ_PIPELINE.md.
NTFY: docs/production/NTFY_REVIEW.md -> https://ntfy.sh/Pic-Gptz.
CURRENT PROJECT: multiple-story production; determine active story from user's task. Do not import old story state.
Tidmunz Studio gen_faces.py, prompt builder and Chrome Relay exist. On 2026-11-13 the Relay port listened, but end-to-end image generation was NOT verified by that check alone.
Plugin CC5 Project Sync packaged rules must be version-synced by Plugin Creator after the live canonical files change.
No automatic or background character builder is enabled by this memory file. Keep original G: assets intact.
GLOBAL SAFETY 2026-11-14: tools/cc5_production_preflight.py installed and tested. Runner blocks incompatible story shape before jobs or CC5. Read docs/production/SCHEMA_RUNNER_GATE.md and CODE_REALITY_AND_SAFETY.md. End-to-end image generation remains untested.

## ชัยชนะของคนไม่ยอมแพ้ — ส่งตรวจทีละตัว

- ใช้ [โฟลว์ตรวจตัวละครเดิมทีละตัว](docs/production/CC5_EXISTING_ACTOR_REVIEW_FLOW.md) ผู้ใช้ให้เลือกตัวหลักก่อน ใช้ชุดคนทั่วไปในอดีตจากภาพจริงและงานเดิมบน Drive และตัดโจงกระเบนออก
- ภาพที่ผู้ใช้ให้ไปต่อแล้ว ได้แก่ อำพร–วัยสาว `อำพรวัยสาว_ตรวจทีละตัว_03` อำพร–วัยกลางคน `อำพรวัยกลางคน_ผ้าซิ่น_04` และชัยยศ–วัยกลางคน `ชัยยศวัยกลางคน_ตรวจทีละตัว_02` ของชัยยศ–วัยหนุ่มใช้ภาพล่าสุด `ชัยยศวัยหนุ่ม_เท็กซ์เจอร์_01`
- ชื่อข้างต้นเป็นชื่อรอบใต้ `runs/chai_chana_khon_mai_yom_phae/cast_fittings/` และมี `look.json` กับผลเรนเดอร์ของแต่ละตัว การให้ไปต่อเป็นผลเช็กชุดและทรงผม งานส่งมอบยังต้องผ่าน Q01–Q10 แยกตามไฟล์จริง
- 20 พ.ย. 2569 ผู้ใช้ให้ผ่านลุคน้ำผึ้งวัยสาวจากรอบ `ชุดเดิมจากไดรฟ์_04` เปิดใช้ไฟล์ที่ Export และเปิดกลับใน CC5 แล้วได้จาก `Desktop/ชัยชนะของคนไม่ยอมแพ้/00_ไฟล์ส่งงาน_iAvatar/` มีอำพร 2 ช่วงวัย ชัยยศ 2 ช่วงวัย และน้ำผึ้งวัยสาว เก็บผลเปิดกลับและจุดที่ยังต้องเก็บงานใน `runs/chai_chana_khon_mai_yom_phae/approved_avatar_delivery/results.json`
- ไฟล์โปรเจกต์และรอบเก่าของเรื่องอยู่ใน `Desktop/ชัยชนะของคนไม่ยอมแพ้/99_งานภายใน/` งานถัดไปตามลำดับเดิมคือน้ำผึ้งวัย 45 ปี

## Ai-cc5
- CLI 1.0.0 และหน้าต่างพรีวิวใช้ state ร่วมกัน สคริปต์พรีวิวที่รองรับโหมดแยกขั้นในเครื่องนี้อยู่ใน runs/chai_chana_khon_mai_yom_phae/
- ตรวจด้วย unittest โดยใช้เครื่องมือจำลอง และรัน production preflight แบบอ่านอย่างเดียวกับเรื่องที่มี recipe แล้ว ต้องได้อนุญาตก่อนทดสอบกับ CC5 จริง

## แม่สื่อหรือมือที่สาม
- สถานะเตรียมเรื่อง ใช้ พ.ศ. 2539 เป็นปีอ้างอิงชั่วคราวจากบรีฟ «30 ปีที่แล้ว»
- แฟ้มบรีฟ บทวิเคราะห์ Lookbook และผล preflight อยู่ใน runs/mae_sue_rue_mue_thi_sam/prepare_story/ นงรักษ์เป็นตัวแรกตามบทตัวเอก
- เตรียมเรื่องครบ 4/4 สำหรับนงรักษ์วัยประมาณ 28 ปีตามที่ผู้ใช้ยืนยัน ล็อกชุดจากไฟล์จริงและผมจาก Reallusion Templates แล้ว Preflight พร้อมไปต่อที่ขั้นทำภาพใบหน้า
