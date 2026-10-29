# คู่มือทำเสื้อผ้า 3D ใหม่ให้ตัวละคร CC5 (สำหรับ AI ที่มาทำงานต่อ)

เขียนเมื่อ 2026-10-29 หลังจากลองหลายวิธีกับเรื่อง "พรจากฟ้า" สิ่งที่อยู่ในหน้านี้คือวิธีที่ **ได้ผลจริง** และ **สิ่งที่ห้ามทำ** อ่านให้จบก่อนเริ่ม

## กฎเหล็ก (ผู้ใช้ย้ำหลายครั้ง)
1. **ห้ามเปิด CC5 กับ Blender ทำงานหนักพร้อมกัน** เครื่องจอฟ้า (bugcheck 0x1A, แรมมีปัญหา) ก่อนรัน Blender ให้ `taskkill /IM CharacterCreator.exe /F` ทุกครั้ง (ถ้าผู้ใช้มีงานค้างใน CC5 ให้ถามก่อน)
2. **ชุดที่ AI สร้างแล้วไม่ดี ให้ทิ้งแล้วสร้างใหม่ ห้ามนั่งแก้** (smooth / ดันจุด / remesh วนไปมา = พังกว่าเดิมทุกครั้ง)
3. **เสื้อต้องสร้างเป็นท่า T เสมอ** (แขนเสื้อกางตรงแนวนอน 90°) ห้ามเสื้อท่า A / แขนตก เพราะเวลาตัวละครกางแขน ใต้แขนจะติดกัน
4. **ชุดผู้ใหญ่ห้ามเอามาบีบใส่เด็ก** ยับเป็นปุ่มทุกครั้ง ต้องสร้างชุดไซส์เด็กจากรูปแบบเด็ก
5. **ก่อนส่งให้ผู้ใช้ดู ต้องซูมดูใกล้ๆ เองก่อน** ห้ามบอกว่า "สวย/ผ่าน" ถ้ายังมีปุ่ม ขีดเหลี่ยม รู แขนกาง ให้รายงานข้อเสียตรงๆ
6. ผู้ใช้จัดชุดเองใน **CC5** (ไม่ใช่ Blender) ถ้าเราวางให้เข้าตัวไม่ได้ ให้เปิดใน CC5 เป็น prop ให้เขาจัด
7. ชุดผู้ใหญ่ ร่าง Neutral, เด็ก Kid, ทารก Baby; ผมดำ / วัยกลางคนเทา / แก่ขาว; ส่งแค่ .iAvatar เข้าโฟลเดอร์เรื่อง
8. คุยกับผู้ใช้เป็นภาษาไทยเท่านั้น

## ขั้นตอนที่ได้ผล (ทำชุดเด็ก มิ่ง 8 ขวบ สำเร็จด้วยวิธีนี้)

### 1. แบบชุด (2D) จาก GPT
- ชุดเบสแนวโบราณ 7 แบบอยู่ที่ `data/designs/base_old_thai/` (`_all.jpg` รวมทุกแบบ) ใช้ซ้ำได้
- พรอมต์อยู่ใน `tools/design_outfits.py` (ถ้า story มี era "โบราณ" จะใช้พรอมต์โจงกระเบน/ผ้าซิ่น)
- เด็ก: ห้ามเขียนว่าไม่ใส่เสื้อ (GPT ปฏิเสธ)
- ถ้า ChatGPT ค้าง (`timed out`) ต้องเปิดหน้าต่าง Chrome ของโปรแกรมติดมันส์ที่ล็อกอิน ChatGPT ไว้; ถ้ายังไม่ได้ ใช้วิธีตัดส่วนจากรูปแบบเดิมด้วย PIL (เช่นตัดครึ่งล่าง = โจงกระเบน)

### 2. สร้าง 3D ด้วย Hunyuan (Tidmunz client, 20 เครดิต/วัน)
```
"%LOCALAPPDATA%\Tidmunz Studio\.venv312\Scripts\python.exe" tools\garment_3d.py <ชื่อ> "<คำบรรยาย>" --tpose     (เสื้อ: ต้อง --tpose)
"%LOCALAPPDATA%\Tidmunz Studio\.venv312\Scripts\python.exe" tools\garment_3d.py <ชื่อ> "x" --image <รูป.jpg>    (ใช้รูปที่มีอยู่)
```
ตั้ง `FACES=40000` ใน env ได้ ผลอยู่ที่ `data/garments_3d/<ชื่อ>/model.glb`

### 3. ตรวจก่อนใช้ (ทุกครั้ง)
```
blender -b --python blender\preview_glb.py -- <model.glb> <ABS path preview.png>     (ใช้ path เต็ม)
```
ดู 3 มุม: หน้า/เฉียง/หลัง เสื้อ: แขนต้องตรงแนวนอน; กางเกง: หลังกับเป้าต้องไม่เป็นร่อง/รู
Hunyuan เห็นแค่ด้านหน้า หลังมักพัง → `mirror=1` ใน fit_ai_bottom (สะท้อนด้านหน้าไปหลัง) หรือสร้างใหม่

### 4. วางชุดเข้าตัวละคร (Blender, CC5 ปิด)
- ส่งตัวเปล่าท่า T ออกจาก CC5: `tools\cc5.py run cc5\smooth_cloth.py job=<job dir> step=export` → `<job>\smooth\body.obj`
  (หรือ `cc5\probes\export_body_pose.py job=<dir> pose=T-Pose out=<obj>`)
- กางเกง/โจงกระเบน: `blender -b --python blender\fit_ai_bottom.py -- <glb> <body.obj> <out.obj> <out_tex.png> <preview.png> mirror=1 push=0`
- เสื้อ: `blender -b --python blender\fit_ai_top.py -- <glb> <body.obj> <out.obj> <out_tex.png> <preview.png> push=0 grow=1.08`
  (`push=1` = ดันผ้าออกจากผิว ทำให้ผ้าสองชั้นไขว้กันเป็นปื้น — อย่าใช้)
- OBJ ที่ส่งเข้า CC5 ต้องเป็น **Y-up** (Blender export forward -Z, up Y); นำ OBJ ของ CC5 เข้า Blender ด้วย forward Y, up Z

### 5. (ถ้าผิวผ้าหยาบ/มีรู) รีเมช + bake
```
blender -b --python blender\remesh_bake.py -- <in.obj> <tex.png> <out.obj> <out.png> 30000 0.3 thick=0.8
blender -b --python blender\compare_render.py -- <cmp.png> <a.obj> <a.png> <b.obj> <b.png>     (เทียบก่อน/หลัง)
```
`thick=0.8` สำคัญ (ไม่ใส่ = รีเมชแล้วเป็นรู) ผลได้ตาข่ายสี่เหลี่ยมเท่ากัน ทรง+ลายใกล้เดิม

### 6. ให้ผู้ใช้จัดใน CC5 แล้วแปลงเป็นเสื้อผ้า
```
python tools\start_cc5.py
python tools\cc5.py run cc5\stage_garment.py job=<job> remove=all "obj=a.obj;b.obj" "tex=a.png;b.png"
```
ผู้ใช้เลื่อน/ย่อ prop ในท่า T แล้วแปลงเอง หรือ `cc5\skin_garment.py job=<job> prop=<ชื่อ> tex=<png> save=<ชื่อตัวละคร>`
(ใส่ OBJ เป็นเสื้อผ้าเลยโดยไม่ให้จัด: `cc5\wear_base.py job=<dir> "items=a.obj|a.png" [pose=A-Pose] [keep=1]`)
ผิวทะลุ: `cc5\probes\collide_cloth.py job=<dir> names=<cloth> margin=0.3` (ทำใน CC5 อย่างเดียว)

### 7. ตรวจผม + บันทึก + Export
- **สคริปต์ส่งตัวเปล่าออก จะถอดผมในฉาก** ถ้าหัวโล้น: `cc5\probes\add_hair.py job=<dir>`
- บันทึก+เรนเดอร์: `cc5\probes\save_job.py job=<dir>` แล้วดู `<job>\<ชื่อ>.png`
- Export: runner step export (ลบ status "export" ใน `stories/<story>.json` แล้วรัน Runner เฉพาะ job นั้น) — ถ้า CC5 เด้งหน้าต่าง "texture missing" ต้องกด OK ก่อน (ปุ่มที่ ~(1018,582) ในกรอบ 1456x819)

## สิ่งที่ยังต้องแก้ (TODO)
1. **ลายผ้าที่ bake มีช่องสี่เหลี่ยมดำขาด** (เห็นที่ชายผ้าห้อยหน้าโจงกระเบนมิ่ง) = จุดที่ bake ยิงแสงไม่โดนผิวเดิม แก้ใน `remesh_bake.py`: เพิ่ม `cage_extrusion` (1.0→2.5), `margin` (8→16), ใส่ `max_ray_distance`; หรือหลัง bake ให้เติมสีช่องดำจากรอบข้าง (dilate/inpaint ด้วย OpenCV `cv2.inpaint`)
2. **ผ้าที่รีเมชแบบ thick เป็นแผ่นสองชั้น + ผิวเป็นขั้นบันได voxel** ผู้ใช้กด Smooth แล้วเป็นเหลี่ยม: ทำเป็นผ้าชั้นเดียว (ลบหน้าที่ normal หันเข้าตัว) และ Corrective Smooth เบาๆ ก่อน bake
3. **มั่น 8 ขวบ** ยังใส่ชุดเก่า (ผู้ใหญ่บีบ) — ใช้ชุดเบสเด็กชุดเดียวกับมิ่ง (`smooth/kidjong_rb.obj` + `kidshirt_fit.obj`) เปลี่ยนลายผ้าให้ต่างกัน
4. ตัวประกอบเรื่องพรจากฟ้า (ชาวบ้าน คนงาน หญิงหลอกเงิน) ยังไม่ได้ทำ
5. ทางยาว: ChatGarment / GarmentCode (AI ตัดแพทเทิร์นจริง) ยังไม่ได้ติดตั้ง ต้องใช้ WSL

## ไฟล์ชุดเบสเด็กที่ใช้ได้แล้ว (มิ่ง 8 ขวบ)
- งาน: `%LOCALAPPDATA%\Tidmunz Studio\snapgen_data\cc5_jobs\story_1029_0051_05\smooth\`
  - `kidjong_rb.obj` + `kidjong_rb.png` โจงกระเบน (รีเมช+bake)
  - `kidshirt_fit.obj` + `kidshirt_tex.png` เสื้อกระดุมจีนท่า T
- ต้นฉบับ Hunyuan: `data/garments_3d/kid_jong/`, `data/garments_3d/kid_shirt_t2/`

## เรื่อง "พรจากฟ้า" (story_1029_0051) สถานะ
ตัวหลัก 10 ตัวอยู่ใน `Desktop\พรจากฟ้า\` ครบ: ตา ยาย มิ่ง/มั่น ทารก มิ่ง 8 ขวบ (ชุดใหม่ผ่านแล้ว) มั่น 8 ขวบ (ต้องเปลี่ยนชุด) มิ่ง/มั่น หนุ่ม มั่น ตอนร่ำรวย นางเอก
คลังเสื้อผ้า/ลายผ้าทั้งหมด: `docs/WARDROBE.md` (สร้างจาก `tools/build_wardrobe_db.py`)
