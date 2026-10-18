# CC5 Character Kit — ทำตัวละคร Character Creator 5 ตามเรื่องนิทาน

ชุดสคริปต์ทำตัวละคร CC5 ทีละตัวจนได้ไฟล์ `.iAvatar` ใช้ได้ทุกเรื่อง ไม่ผูกกับเรื่องใดเรื่องหนึ่ง
คอมพังก็ clone กลับมา ดับเบิลคลิก `install.bat` แล้วทำงานต่อได้เลย

## ติดตั้ง (เครื่องใหม่ / คอมเพิ่งลงใหม่)

1. ลงโปรแกรมให้ครบ: **Character Creator 5**, **Blender 4.2**, **Python 3.11 ขึ้นไป** (ติ๊ก Add to PATH), **Tidmunz Studio** (ใช้สร้างหน้า AI)
2. ให้ Google Drive เห็นคลังเสื้อผ้า `G:\...\Prop ของใช้ต่างๆ\เสื้อผ้า-ทรงผม`
3. ดึงโปรเจกต์:
   ```bash
   git clone https://github.com/apinanautan/cc5-character-kit.git "C:\Users\Apinan\Documents\CC5 Characters"
   ```
4. ดับเบิลคลิก `install.bat` ต้องขึ้น `OK` ทุกบรรทัด ถ้าขึ้น `MISSING` ให้ลงโปรแกรมนั้นหรือแก้ path ใน `config.json`

## ทำตัวละครเรื่องใหม่

1. **เขียนไฟล์เรื่อง** `stories/<ชื่อ>.json` (ดูตัวอย่าง `stories/krong.json`) ตัวละครละ 1 รายการ:
   - `name` ชื่อไฟล์ภาษาไทย, `folder` โฟลเดอร์ตามเลขข้อในเรื่อง
   - `body`: `neutral` (ผู้ใหญ่/คนแก่ เสมอ), `child`, `baby`
   - `outfit`: `[ชิ้นล่าง, ชิ้นบน, รองเท้า]` แต่ละชิ้นเป็น `[ของ, ลายผ้า]`
     - ของ = ไอดีย่อใน `data/wardrobe_verified.json` เช่น `"f7c187"` หรือ `"MO:Farmer\\Shirt 01.ccCloth"` (คลัง Male Outfits) หรือ `"RC:..."`
     - ลายผ้า = ชื่อไฟล์ใน `data/fabrics` เช่น `"floral_brown"` หรือ `null`
     - ดูว่าเสื้อกับกางเกงคู่ไหนใส่ด้วยกันได้ที่ `data/pair_test_results.txt`
   - `hair` ส่วนหนึ่งของชื่อไฟล์ผมใน `data/cc5_hair_pool.json` (`""` = ไม่มีผม)
   - `face` ข้อมูลสร้างหน้า (อายุ บทบาท สีผิว ทรงผม ใบหน้า) + `ref` ถ้าเป็นคนเดียวกันต่างวัย
   - ตัวเลือกพิเศษ: `head_from` (ใช้หัวของอีกตัว = คนเดิม), `morphs` (ผอม/ท้อง), `skin_arm` (แผล), `layer` (`in` เสื้อเก็บในกางเกง / `out` เสื้อปล่อยนอก)
2. **สร้างหน้า** (เปิด Tidmunz Studio ไว้ก่อน): `python tools\gen_faces.py <ชื่อเรื่อง> <job>`
3. **เตรียมงาน**: `python tools\plan.py <ชื่อเรื่อง> <job>`
4. **ใน CC5**: Script → Load Python → `cc5\build.py` (ทำหัว ใส่ชุด ย้อมผม แก้เสื้อทะลุ render บันทึก) ดูผลที่ `<job>\result.txt` และรูป `<job>\<ชื่อ>.png`
5. **Export**: File → Export → iAvatar → บันทึกลง `Desktop\<ชื่อเรื่อง>\<โฟลเดอร์>\<ชื่อ>.iAvatar`

ทำ **ทีละตัว** ให้เสร็จจนได้ iAvatar แล้วค่อยทำตัวต่อไป

## ปุ่มลัดใน CC5 (Script → Load Python)

| ไฟล์ | ทำอะไร |
|---|---|
| `cc5\build.py` | สร้าง/แต่งตัวตัวละครทุกตัวใน `cc5_jobs\batch.txt` |
| `cc5\shirt_out.py` | กดครั้งเดียว: เสื้อปล่อยออกนอกกางเกง/ผ้าถุงพอดี ไม่ทะลุ |
| `cc5\shirt_in.py` | กดครั้งเดียว: เสื้อเก็บเข้าในกางเกงพอดี (ผ้าขาวม้า/เข็มขัดอยู่นอก) |
| `cc5\select_upper.py` | เลือกเสื้อตัวบนไว้ให้กด Modify → Conform เอง |
| `cc5\apply_skin_texture.py` | ใส่ลายผิวแขน (เช่นแผลไฟลวก) |
| `cc5\pair_test.py` | ทดสอบเสื้อ×กางเกงว่าคู่ไหนใส่ด้วยกันแล้วไม่หลุด |

## เปลี่ยนชุดตัวที่ทำเสร็จแล้ว

```bash
python tools\redress.py krong_urai_40 "RC:Pants\Pants(28).ccCloth=pha_thung_green" "MO:Painter\Shirt.ccCloth=floral_brown"
```
แล้วใน CC5 รัน `cc5\build.py` (หัวและผมเดิม เปลี่ยนแค่ชุด) อย่าลืมแก้ชุดในไฟล์เรื่องให้ตรงด้วย

## ลดโพลีกอนเสื้อผ้า (ให้ iClone เบา)

- เกณฑ์: ร่างกาย CC5 ราว 20,000 หน้า → เสื้อผ้าแต่ละชิ้นไม่ควรเกิน **~15,000 หน้า** (เสื้อ ~12,000, กระโปรง/กางเกงยาว ~15,000) ทั้งตัวรวมไม่ควรเกิน ~60,000–80,000
- วัด: CC5 → Script → `cc5\poly_report.py` (ทุกงานใน batch.txt) → `cc5_jobs\poly_report.json` (ผลก่อนลดของเรื่องกรงกตัญญู: `data/poly_report_krong_before.json`)
- ลด: ใช้ **InstaLOD ใน CC5** (เก็บ skin weight + UV + ลายผ้าไว้ให้) แบบ **By Percentage** เท่านั้น ("By Face Count" ใช้ไม่ได้)
  1. เขียนชื่อเสื้อผ้าใน `cc5_jobs\select_cloth.txt` แล้ว `python -c "import kit,os;kit.set_batch([os.path.join(kit.JOBS,'<job>')])"`
  2. CC5 → Script → `cc5\select_cloth.py` (เปิดโปรเจกต์ + เลือกชิ้นนั้น)
  3. Modify → InstaLOD → Polygon Reduction - Object (ดับเบิลคลิก) → By Percentage = เป้าหมาย/จำนวนเดิม×100 → Apply → Close → Ctrl+S
  4. นับจริงด้วย `cc5\export_cloth_obj.py` (ตัวนับหน้าใน CC5 อ่านผิดหลัง InstaLOD)
- Blender decimate (`blender/decimate_obj.py`) ลดได้สวยแต่ **ส่งกลับ CC5 ไม่ได้** (ReplaceMesh ต้องจำนวนจุดเท่าเดิม)
- CC5 กิน RAM เพิ่มทุกครั้งที่เปิดโปรเจกต์ → เปิดหลายตัวต่อกันแล้วค้าง/เด้ง ให้ปิดเปิด CC5 ใหม่ทุก ~4–5 ตัว

## โครงสร้าง

```
cc5/       สคริปต์ที่รันใน CC5          blender/  สคริปต์ Blender (รันเบื้องหลัง)
tools/     สคริปต์รันด้วย python ปกติ    stories/  ไฟล์เรื่อง (ตัวละคร ชุด ผม หน้า)
data/      ข้อมูลเสื้อผ้าที่ตรวจแล้ว ผม ลายผ้า แผล    iclone/  สคริปต์ iClone 8
docs/      บันทึกปัญหา + skill ของ Claude    archive/  สคริปต์เก่าเฉพาะเรื่อง
kit.py     path ทั้งหมดอยู่ที่นี่ (อ่านจาก config.json)
```

## ปัญหาที่เจอแล้วและวิธีแก้ (อย่าเจออีก)

- ร่างเด็กต้องเป็น `Kid` ใน CC5 (ไม่ใช่ Child) ถ้าผิดจะได้ร่างผู้ใหญ่
- ผมเทา/ขาว: build.py ปิด base color map + vertex color ให้แล้ว ไม่งั้นผมจะออกน้ำตาล
- ผมในโฟลเดอร์ `ทรงผม\Hair\` texture หาย โหลดนาน ~6 นาที ย้อมเทาไม่ได้ ใช้ Prime Hairstyles แทน
- เสื้อบางตัวทำให้กางเกงหลุด (CC5 นับเป็นช่องเดียวกัน) ดู `data/pair_test_results.txt`
- ห้ามใช้ LoadClotheFromFbx ส่งเสื้อกลับจาก Blender (เสื้อพอง) ใช้ ReplaceMesh แบบใน `cc5\layer_fix.py`
- สร้างหน้าต้องเปิด Tidmunz Studio ไว้ ถ้าปิดจะได้ error `token_revoked`
- อย่าใช้เสื้อครอปกับผู้ใหญ่ (โชว์สะดือ) และอย่าให้ผู้ชายใส่เชิ้ตแบบเดียวกันทุกตัว
