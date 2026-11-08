FIRST read PROJECT_MEMORY.md. Log every confirmed project change there. Check only relevant source when needed.
# AGENTS.md — อ่านก่อนเริ่มงานในโฟลเดอร์นี้ (สำหรับ GPT / Codex / AI อื่น)

โปรเจกต์ทำตัวละคร Character Creator 5 ตามเรื่องนิทาน ใช้ภาษาไทยคุยกับผู้ใช้

อ่านตามลำดับ:
1. `CLAUDE.md` — กฎของผู้ใช้ (ร่าง Neutral, สีผม, ชุดชาวบ้านไทยเรียบ, ชื่อไฟล์, ส่งแค่ .iAvatar)
2. `docs/GARMENT_PIPELINE.md` — วิธีทำเสื้อผ้า 3D ใหม่ที่ได้ผล + สิ่งที่ห้ามทำ + TODO ล่าสุด
3. `docs/APP.md` — โปรแกรม CC5 Character Studio (รายชื่อตัวละคร → .iAvatar)
4. `docs/WARDROBE.md` — คลังเสื้อผ้า/ชุดตายตัว/ลายผ้าที่มี
5. `docs/FACE_GUIDE.md` — สร้างรูปใบหน้าตัวละครเอง (เมื่อโปรแกรมติดมันส์สร้างไม่ได้)

สำคัญที่สุด: ห้ามเปิด CC5 กับ Blender ทำงานหนักพร้อมกัน (เครื่องจอฟ้า) และชุดที่ไม่ดีให้สร้างใหม่ ไม่ต้องนั่งแก้

## CC5 Project Sync - 2026-11-08
Before a new story/character batch, inspect file changes in AGENTS.md, CLAUDE.md, docs/GARMENT_PIPELINE.md, docs/WARDROBE.md, stories/*.json, and wardrobe-related source code. Compare timestamps/hash; read only changed files and refresh rules, never trust an old cached description over modified sources. ChatGPT hosted plugin: cc5-project-sync v0.1.0 (sync at task start, not autonomous background watch).
Wardrobe: DO NOT reuse the same cut/silhouette across most characters by merely recoloring fabric. Allocate outfits by role, era, age, occupation, class and personality; verify full outfits by preview. Student/police/monk have correct role-specific attire. Flag catalog deficiencies instead of substituting inappropriate garments. Preserve active CC5 jobs; do not run heavy Blender and CC5 simultaneously.
Story export: identify story by JSON title, confirm matching folder within G:\ไดรฟ์ของฉัน before using a story-specific character subfolder. If not found, export to Desktop. Do not assume absence from folder modification time alone.