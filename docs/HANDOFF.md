# HANDOFF — งานทำตัวละคร CC5 (อ่านไฟล์นี้ก่อนทำต่อ)

> สำหรับ AI/คนที่มาทำต่อ (GPT, Claude, คน) — อัปเดตล่าสุด 2026-10-18 16:15
> repo: https://github.com/apinanautan/cc5-character-kit (public) · โฟลเดอร์ในเครื่อง: `C:\Users\Apinan\Documents\CC5 Characters`
> คู่มือใช้งานสั้นๆ อยู่ที่ `README.md` ไฟล์นี้คือรายละเอียดเต็ม + สถานะงานค้าง

---

## 0. สั่ง CC5 โดยไม่ต้องกดหน้าจอ (ใช้ได้ทั้ง Claude / GPT / Codex)

CC5 มี plugin **CC5Bridge** (`cc5_plugin/CC5Bridge`, ลิงก์เข้า `CC5\Bin64\OpenPlugin` แล้วด้วย `install_plugin.bat`) — รันคำสั่งจากไฟล์ ไม่ต้องเห็นหน้าต่าง
```bash
python tools\start_cc5.py            # เปิด CC5 (กด OK ป๊อปอัปเปิดโปรแกรมเอง) และรอจน bridge พร้อม  (--restart = ปิดเปิดใหม่)
python tools\cc5.py status           # ALIVE ไหม ใครล็อกอยู่
python tools\cc5.py lock gpt         # จองก่อนใช้ (ถ้าขึ้น already locked = อีก agent ใช้อยู่ ห้ามแย่ง)
python tools\cc5.py run cc5uild.py                          # สคริปต์อะไรก็ได้ใน cc5/ รอผลแล้วพิมพ์ log
python tools\cc5.py run cc5\load_render.py job=krong_banphot  # ส่งค่าเข้า BRIDGE_ARGS ได้
python tools\cc5.py unlock           # เลิกใช้แล้วปลดล็อก (ถ้า agent เดิมติดลิมิต ผู้ใช้ลบ cc5_jobs\LOCK.txt เองได้)
```
- ผลรูปอยู่ในโฟลเดอร์ job (เช่น `check.png`, `<ชื่อ>.png`) — เปิดดูรูปทุกครั้งก่อนบอกว่าผ่าน
- ทำครบหนึ่งตัว → อัปเดต `docs/STATUS.md` → `git commit` + `git push` ทันที (อีก agent จะรู้ว่าถึงไหน)
- ยังต้องกดด้วยมือ: **InstaLOD** (ลดโพลี) และ **Export iAvatar** ยังไม่มีคำสั่ง Python — ถ้า agent กดจอไม่ได้ ให้เขียนขั้นตอนให้ผู้ใช้กด (ตำแหน่งปุ่มในข้อ 5 และ 7)
- CC5 แครช/ค้าง → `python tools\start_cc5.py --restart`

## โปรแกรม (ใหม่ 2026-10-19)

ทำตัวละครทั้งเรื่องด้วย **`app.py` (CC5 Character Studio)**: วางรายชื่อ → ยืนยัน → เริ่ม ดูวิธีใช้และสิ่งที่ยังไม่ได้ทดสอบใน [docs/APP.md](APP.md)

## 1. งานนี้คืออะไร

ผู้ใช้ทำคลิปนิทาน/เรื่องเล่าไทยด้วย iClone 8 ต้องการ **ตัวละคร 3D ใน Character Creator 5 (CC5)** ตามรายชื่อตัวละครของแต่ละเรื่อง
ผลลัพธ์ที่ส่ง = ไฟล์ `.iAvatar` หนึ่งไฟล์ต่อตัวละคร วางใน `Desktop\<ชื่อเรื่อง>\<โฟลเดอร์ตามเลขข้อ>\<ชื่อไทย>.iAvatar`
(ผู้ใช้ย้ายขึ้น Google Drive เอง)

ขั้นตอนต่อ 1 ตัว: หน้า AI (ChatGPT) → Headshot 3 ใน CC5 สร้างหัว → ใส่ชุด/ผม/รองเท้าจากคลังของผู้ใช้ → ย้อมผม → แก้เสื้อผ้าทะลุ → render ตรวจ → export iAvatar

## 2. กฎของผู้ใช้ (ห้ามฝ่าฝืน)

1. **ทำทีละตัวให้เสร็จจนได้ iAvatar** แล้วส่งรูปให้ดู ค่อยทำตัวถัดไป — ห้ามทำหน้าทั้งหมดก่อน/ห้าม batch ทีเดียวหลายตัวแล้วไม่เห็นผล
2. ร่างผู้ใหญ่/คนแก่ = **Neutral เสมอ** (ไม่มีหน้าอก) · เด็ก = `Kid` · ทารก = `Baby`
3. ผม: ดำ (เด็ก/หนุ่มสาว) · เทา (วัยกลางคน) · ขาว (แก่) — ห้ามสีน้ำตาล/บลอนด์ · ผู้ชายห้ามผมยาวแบบผู้หญิง · **ห้ามทรงผมซ้ำในเรื่องเดียวกัน** (ยกเว้นคนเดียวกันต่างสภาพ)
4. ชุดชาวบ้านไทยเรียบๆ ไม่โป๊ ไม่แฟชั่น ไม่มีโลโก้/ลายการ์ตูน · **ผู้ใหญ่ห้ามเสื้อครอปโชว์สะดือ**
5. **ห้ามชุดซ้ำกัน** ทั้งในเรื่องและข้ามเรื่อง · ผู้ชายต้องต่าง "ชนิดเสื้อ" (เสื้อกล้าม เชิ้ตลายสก็อต เสื้อยืด ชุดนอน ฯลฯ) ไม่ใช่แค่ต่างสี · ใช้ลายผ้า (`data/fabrics`) ให้ต่างกัน สีหม่นๆ แบบชาวบ้าน
6. ชื่อไฟล์ **ภาษาไทย** เช่น `นายสมจิต วัย 40.iAvatar` · โฟลเดอร์ละข้อตามรายชื่อเรื่อง (คนเดียวกันต่างวัยอยู่โฟลเดอร์เดียวกัน)
7. ส่งแค่ `.iAvatar` เข้าโฟลเดอร์เรื่อง — ไฟล์อื่น (png, ccProject) เก็บในโฟลเดอร์ job เท่านั้น
8. ห้ามแก้โค้ดโปรแกรม Tidmunz Studio (repo tidmunz-studio แยก) จาก repo นี้
9. ประหยัด token: เลือกของจากข้อมูล (json) ไม่เปิดรูปทีละชิ้น · ตรวจผลด้วย render ไม่ใช่เดา
10. งาน iClone (คีย์ไอโคน): ส่ง mp4 ให้เร็ว, เปิดเฉพาะไฟล์ฉาก, save `E:\FileSave\N.iProject`, render `E:\Video\N.mp4`, ห้ามเขียนลง G: โฟลเดอร์ส่งงาน, `RTime` = 1/6000 วินาที (ดู `docs/skills/iclone-key`)

## 3. เครื่องมือ/โปรแกรมที่ต้องมี

| อะไร | อยู่ที่ |
|---|---|
| Character Creator 5 (5.07) | `C:\Program Files\Reallusion\Character Creator 5\Bin64\CharacterCreator.exe` |
| Blender 4.2 | `C:\Program Files\Blender Foundation\Blender 4.2\blender.exe` |
| Tidmunz Studio (สร้างหน้า AI ผ่าน ChatGPT) | `%LOCALAPPDATA%\Tidmunz Studio` — **ต้องเปิดโปรแกรมไว้** ไม่งั้นได้ `token_revoked` |
| คลังเสื้อผ้า/ผม | `G:\คอมพิวเตอร์เครื่องอื่นๆ\คอมพิวเตอร์ของฉัน\โมชั่น\Prop ของใช้ต่างๆ\เสื้อผ้า-ทรงผม` |
| โฟลเดอร์งานต่อตัว (job) | `%LOCALAPPDATA%\Tidmunz Studio\snapgen_data\cc5_jobs\<job>\` (face.png, job.json, ไอเท็ม, `<ชื่อ>.ccProject`, `<ชื่อ>.png`, result.txt) |
| path ทั้งหมด | `kit.py` อ่านจาก `config.json` (สร้างโดย `install.bat`, ไม่อยู่ใน git) |

ติดตั้งเครื่องใหม่: clone → ดับเบิลคลิก `install.bat` (ดู README)

## 4. วิธีทำงาน (ลำดับจริง)

1. ไฟล์เรื่อง `stories/<เรื่อง>.json` — ตัวอย่างครบ: `stories/krong.json` (16 ตัว)
2. หน้า: `python tools\gen_faces.py <เรื่อง> <job>` (ทีละตัว) → `cc5_jobs\<job>\face.png` — ดูรูปก่อนใช้ (อายุต้องตรง)
3. เตรียม: `python tools\plan.py <เรื่อง> <job>` → job.json + ก็อปไอเท็ม + ลายผ้า + ผม + เขียน `cc5_jobs\batch.txt`
4. CC5: เมนู **Script → Load Python** → `cc5\build.py` → ดู `result.txt` (ทุกบรรทัด OK) + รูป `<ชื่อ>.png`
5. ถ้าเสื้อ/กางเกงทะลุกัน: `cc5\shirt_out.py` (เสื้อปล่อยนอก) หรือ `cc5\shirt_in.py` (เสื้อเก็บใน — ผ้าขาวม้าอยู่นอก) แล้วดูรูป
6. Export: File → Export → iAvatar → Export → ช่องชื่อไฟล์ใส่ path เต็ม → Enter → ถ้าถามทับไฟล์กด "ใช่"
7. ส่งรูป render ให้ผู้ใช้ดู แล้วไปตัวถัดไป
8. เปลี่ยนชุดตัวที่เสร็จแล้ว: `python tools\redress.py <job> "<ชิ้นล่าง>=<ลายผ้า>" "<ชิ้นบน>=<ลายผ้า>"` → CC5 `cc5\build.py` (โหลดโปรเจกต์เดิม หัว/ผมเดิม) → **แก้ outfit ใน stories json ให้ตรงด้วย**
9. แก้สคริปต์/ข้อมูลแล้ว → `git commit` + `git push`

### ระบุของใน outfit
- ไอดีย่อจาก `data/wardrobe_verified.json` เช่น `"f7c187"`
- `MO:` = `...\!Converted STUFFS\Male Outfits\` (85 เสื้อ: Farmer, Billybob Vest, Sweat Top, Streetstyle, Pyjamas, Painter, Underbelly, Old ฯลฯ)
- `RC:` = `...\Reallusion Custom\Cloth\`
- ลำดับ: **ชิ้นล่างก่อน ชิ้นบนทีหลัง รองเท้าท้ายสุด** (ชิ้นผ้าตัวสุดท้ายถือเป็น "เสื้อตัวบน" → `upper.txt`)
- คู่เสื้อ×กางเกงที่ใส่ด้วยกันได้ (ไม่หลุด): `data/pair_test_results.txt` (ทดสอบด้วย `cc5\pair_test.py`)

## 5. การสั่ง CC5 อัตโนมัติ (สำคัญ — ที่เคยพัง)

- รันสคริปต์ได้ทางเดียว: เมนู Script (x≈400,y≈30 บนจอ 1456×819) → Load Python (≈442,53) → ช่อง File name (≈300,715) พิมพ์ path เต็ม → Enter
- **ห้ามใช้ open_application กับ CC5** (เปิดกล่อง Run ของ Windows) — ถ้า CC5 ไม่อยู่หน้าสุด ให้คลิกไอคอนบน taskbar
- ป๊อปอัปที่เจอประจำ: "Failed to establish a connection" ตอนเปิด → OK · "Unsaved project data found" → Cancel · ไฟล์ texture ผมหาย (ผม `ทรงผม\Hair\...`) → OK (≈1016,582) · DRM Missing (สไลเดอร์ผอม Male Skinny/Face Thinner เป็นของเสียเงินที่ไม่ได้ซื้อ) → **Close ห้ามกด Buy All**
- **CC5 กิน RAM เพิ่มทุกครั้งที่เปิดโปรเจกต์** → เปิด ~4–5 โปรเจกต์ติดกันแล้วค้าง (Not Responding 10–16 GB) หรือเด้ง (`torch_cpu.dll`) → ปิดเปิด CC5 ใหม่บ่อยๆ (ปิดได้ถ้าหัวหน้าต่างไม่มี `*`)
- ตรวจผลด้วยไฟล์ (result.txt / layer_fix.txt / render png) ไม่ต้อง screenshot ระหว่างรอ

## 6. ความรู้ทางเทคนิคที่หามาแล้ว (อย่าลองซ้ำ)

- Headshot API: `RLPy2.Headshot3.GetInterface().CenerateCharacter(face, EHSBodyType.Neutral|Kid|Baby, False, ...)` ~3–4 นาที/ตัว — `Child` ไม่มี (จะได้ร่างผู้ใหญ่)
- ย้อมผมเทา/ขาว: ต้องปิด `BaseColorMapStrength`, `VertexColorStrength`, เปิด `ActiveChangeHairColor` + ตั้ง `VertexGrayToColor`/`RootColor`/`TipColor` (อยู่ใน build.py แล้ว)
- ผมในโฟลเดอร์ `ทรงผม\Hair\` (Fringe, Classic Side Parted, Slicked Back) texture หาย โหลด ~6 นาที ย้อมเทาไม่ได้ → ใช้ Prime Hairstyles / Hair2 / Hair Builder · `cc5_pick_hair.py` สุ่มซ้ำได้ ให้ระบุ `hair` ในไฟล์เรื่องเอง
- สไลเดอร์รูปร่าง: `av.GetAvatarShapingComponent().SetShapingMorphWeight(id, w)` — ผอม `2025-06-10-16-36-51_pack_skinny_fullbody_01` (+หน้า `2019-09-30-13-56-29_face thinner`) · ท้อง `cc embed morphs/embed_torso113` + `embed_torso111` · คนเดียวกันต่างสภาพ ใช้ `head_from` (หัวเดิม)
- แผลไฟลวก: ลาก texture แขน `CC_Base_Body/Std_Skin_Arm` ด้วย `GetImage(...).SaveFile()` → วาดด้วย `tools/paint_burn_scar.py` → `LoadImageToTexture` (`data/arm_burn.png`)
- Collision อัตโนมัติ: `cloth.SetClothConformValue("Iteration",3) / ("Margin",0.3) / ("IncreaseSize",0.2)` + `cloth.CalculateCollision()` (build.py ทำให้)
- เสื้อ-กางเกงทะลุ: export OBJ (ท่าปัจจุบัน, Z-up, cm) → `blender/layer_fix_obj.py` ดันเฉพาะจุดที่จมออกไปพ้นชั้นนอกสุด → `mesh.ReplaceMesh(obj, EReplaceMeshOption_ZUp, False)` (จำนวนจุดต้องเท่าเดิม) — **ห้ามใช้ LoadClotheFromFbx** (เสื้อพอง)
- เสื้อที่ทำให้กางเกงหลุด (CC5 นับช่องเดียวกัน): Close/Open_collar_long_sleeves (ko=1), Pants(24) "เสื้อ", Lift & Haul Henley, Farmer Shirt + Biker/Old pants ฯลฯ → ดู pair_test · 193290 = เกาะอก · b67f5d = ไหล่เดียว · 04f1fc = เสื้ออย่างเดียว · dbafdf = กระเป๋า · 6f3677 = กระโปรงจีนแดง · fc523c เสื้อไหล่โหว่ตอนแขนลง · 3ccaca = ครอปโชว์สะดือ

## 7. ลดโพลีกอน (ทำค้างอยู่)

- เกณฑ์ที่ตั้ง: ร่าง CC5 ≈ 20,000 หน้า → ผ้าแต่ละชิ้น ≤ ~15,000 (เสื้อ ~12k, กระโปรง/กางเกงยาว ~15k), ทั้งตัว ~60–80k (ค่าแนวทางทั่วไปของงาน real-time — ยังหาเอกสาร Reallusion ยืนยันไม่ได้เพราะ web search ใช้ไม่ได้ตอนนั้น)
- วัด: `cc5\poly_report.py` → `cc5_jobs\poly_report.json` · ผลก่อนลด: `data/poly_report_krong_before.json` (หมายเหตุ: ค่า "Body" ในไฟล์นั้นคือรวมทั้งตัวแล้ว)
- **วิธีที่ใช้ได้: InstaLOD ใน CC5** (เก็บ skin weight/UV/ลายผ้า): ใส่ชื่อผ้าใน `cc5_jobs\select_cloth.txt` + ตั้ง batch.txt เป็น job นั้น → Script `cc5\select_cloth.py` (โหลดโปรเจกต์+เลือกผ้า) → แผง Modify → **ดับเบิลคลิก** "Polygon Reduction - Object" (≈1296,600; คลิกเดียวมักไม่เปิด) → **By Percentage** (≈625,330 / ช่องค่า ≈798,330 พิมพ์แล้วกด Tab) → Apply (≈664,494) → รอ 25–30 วิ → Close (≈790,487) → **Ctrl+S** → export iAvatar
  - **"By Face Count" ใช้ไม่ได้** · ตัวนับหน้าใน CC5 (`GetFacesCount`) อ่านผิดหลัง InstaLOD → นับจริงด้วย `cc5\export_cloth_obj.py` แล้วนับบรรทัด `f ` ใน `cc5_jobs\cloth_check.obj`
- Blender decimate (`blender/decimate_obj.py`, `cc5/reduce_polys.py`) ลดได้สวยแต่ **ส่งกลับ CC5 ไม่ได้** (ReplaceMesh ปฏิเสธจำนวนจุดต่าง) — อย่าใช้ทางนี้

## 8. สถานะเรื่อง "กรงกตัญญู" — ตัวล่าสุดอยู่ที่ docs/STATUS.md (ตารางนี้คือ ณ 2026-10-18 16:15)

ไฟล์อยู่ `Desktop\กรงกตัญญู\` ครบ 16 ตัว (โฟลเดอร์ 1,2,3,4,6,7,8 — ข้อ 5 รถยนต์ ผู้ใช้จัดเอง)

| job | ชื่อไฟล์ | สถานะ |
|---|---|---|
| krong_somjit_40 | นายสมจิต วัย 40 | เสร็จ · **ค้างลดโพลี** กางเกง `Pants_37128_Shape` 36,762 → 40% |
| krong_urai_40 | นางอุไร วัย 40 | เสร็จ + ลดแล้ว (กระโปรง 49,810→14,942) |
| krong_somjit_70 | นายสมจิต วัย 70 แผลไฟลวก | เสร็จ + ลดแล้ว (กางเกงเล 100,000→13,662) |
| krong_somjit_70_thin | นายสมจิต วัย 70 ซูบผอม | เสร็จ + ลดแล้ว (100,000→13,560) |
| krong_urai_70 | นางอุไร วัย 70 | **ค้าง**: เสื้อเดิม fc523c ไหล่โหว่ตอนแขนลง → เข้าคิวเปลี่ยนเป็น `MO:Old\Shirt.ccCloth` ลาย floral_blue_faded แล้ว (job.json `load_project`, ยังไม่ได้รัน build) → รัน `cc5\build.py` → ดูรูปไหล่ → ลดผ้าถุง `node_0` 50,008 → 30% → export → แก้ outfit ใน `stories/krong.json` ให้เป็น Old Shirt |
| krong_relative_m | ญาติ ชาย | เสร็จ (ไม่มีชิ้นเกิน 20k) |
| krong_relative_f | ญาติ หญิง | เสร็จ |
| krong_orawan_child | อรวรรณ วัยประถม | เสร็จ · **ค้างลดโพลี** กระโปรง `node_0` 49,810 → 30% |
| krong_orawan_young | อรวรรณ วัยสาว | เสร็จ · **ค้างลดโพลี** เสื้อ `UnderbellyShirt_44305_Shape` 43,997 → 30% |
| krong_orawan_pregnant | อรวรรณ ตอนท้อง | เสร็จ · **ค้างลดโพลี** เสื้อ `geometry_0` 79,418 → 15% |
| krong_banphot | บรรพจ | เสร็จ + ลดแล้ว (เสื้อ 75,000→13,001) |
| krong_son_baby | ลูกชายอรวรรณ วัยทารก | เสร็จ |
| krong_son_child | ลูกชายอรวรรณ 4-5 ขวบ | เสร็จ · **ค้างลดโพลี** กางเกง `CargoShorts_50332_Shape` 57,617 → 25% (ผม Side-swept Fringe 37k — ผมการ์ดใส ไม่แนะนำลด) |
| krong_neighbor_f | เพื่อนบ้าน หญิง | เสร็จ |
| krong_elder_m | คนแก่ ชาย | เสร็จ |
| krong_elder_f | คนแก่ หญิง | เสร็จ |

หลังลดแต่ละตัว: render เทียบก่อน/หลัง (ส่วนที่ลดต้องดูเหมือนเดิม) → export iAvatar ทับ → ส่งรูปผู้ใช้

## 9. ไฟล์สำคัญใน repo

```
cc5/build.py            สร้าง/แต่งตัวทุก job ใน batch.txt (หัว ชุด ลายผ้า ผม สไลเดอร์ แผล layer collision render save)
cc5/layer_fix.py        เสื้อ-กางเกงทะลุ (shirt_in.py / shirt_out.py เรียกตัวนี้)
cc5/select_cloth.py     โหลดโปรเจกต์ job + เลือกผ้าตาม select_cloth.txt (ก่อน InstaLOD)
cc5/poly_report.py      นับโพลีทุก job · count_current.py นับตัวที่เปิดอยู่ + render · export_cloth_obj.py
cc5/pair_test.py        ทดสอบคู่เสื้อ×กางเกง · apply_skin_texture.py · select_upper.py · render_check.py · probes/
blender/layer_fix_obj.py  ดันผ้าที่จมออก · decimate_obj.py (ใช้ไม่ได้กับ CC5)
tools/plan.py gen_faces.py redress.py install.py paint_burn_scar.py fabric_onto_garment.py gen_fabrics.py
stories/krong.json      ตัวละครเรื่องกรงกตัญญู (หน้า ชุด ผม สไลเดอร์)
data/                   wardrobe_verified.json (สถานะเสื้อผ้า ok/rejected + โน้ต), cc5_hair_pool.json, fabrics/, pair_test_results.txt, arm_burn.png, poly_report_krong_before.json
docs/skills/            วิธีทำงานแบบเต็มของ Claude (cc5-character, iclone-key) · docs/steps_log.md
archive/                สคริปต์เก่าเฉพาะเรื่อง (ไม่ต้องใช้)
```

## 10. ถ้าเป็น AI ที่สั่ง CC5 ไม่ได้ (เช่น GPT ไม่มี computer-use)

- แก้/เพิ่มไฟล์เรื่อง, เลือกชุดจาก `data/*.json`, เขียน/แก้สคริปต์ใน repo ได้เลย แล้ว commit
- ส่วนที่ต้องกดใน CC5 ให้เขียนเป็นขั้นตอนให้ผู้ใช้กด (Script → Load Python → ไฟล์ไหน) และให้ผู้ใช้ส่ง `result.txt` / รูป render กลับมาตรวจ
- ห้ามเดาว่าผ่าน — ต้องดูรูป render ทุกครั้ง
