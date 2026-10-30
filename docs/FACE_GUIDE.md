# แนวทางสร้างรูปใบหน้าตัวละคร (สำหรับ Headshot ใน CC5)

ใช้เมื่อโปรแกรมติดมันส์สร้างหน้าไม่ได้ (ChatGPT ค้าง `timed out`, โควตารูปหมด, หรือ GPT ปฏิเสธ)
ให้สร้างเองในหน้าเว็บ ChatGPT (หรือ AI วาดรูปตัวอื่น) แล้วเอาไฟล์มาวางเอง

## หน้าแบบไหนที่ Headshot ใช้ได้ (สำคัญกว่าพรอมต์)
| ต้องมี | ห้ามมี |
|---|---|
| หน้าตรง มองกล้อง ศีรษะถึงไหล่ | หน้าเอียง หันข้าง ก้ม เงย |
| ปากปิดสนิท สีหน้าเฉยๆ | ยิ้ม เห็นฟัน อ้าปาก |
| เห็นหน้าผาก คิ้ว หูทั้งสองข้าง | หน้าม้า ผมปิดหน้าผาก/หู หมวก ผ้าโพก |
| แสงขาวเท่ากันทั้งสองข้างของหน้า | เงาครึ่งหน้า แสงเหลือง/ส้ม แสงย้อน |
| ฉากหลังเทาอ่อนเรียบ | ฉากหลังมีของ ลวดลาย |
| อายุตรงตามบท (คนแก่ต้องมีริ้วรอยจริง) | ผิวเนียนเป็นพลาสติก แต่งหน้า ฟิลเตอร์ |
| ไม่มีเครื่องประดับ | ต่างหู สร้อย แว่น |

**ผมไม่สำคัญ** (ผมจริงมาจากคลังผมใน CC5) ขอแค่ผมไม่ปิดหน้าผากกับหู

## พรอมต์สั้น (ใช้ได้ดีกว่าพรอมต์ยาว)
แทนค่าใน `< >` แล้ววางในหน้าเว็บ ChatGPT ขอรูป **สัดส่วน 4:5 หรือ 3:4**

```
Photorealistic ID-style portrait photo of a Thai <man / woman / boy / girl>, about <อายุ> years old,
<บทบาท เช่น poor village woodcutter in old Siam / kind village grandmother>.
<ผิว เช่น sun-tanned brown skin>, <ใบหน้า เช่น long face, round eyes, thin lips>.
Head and shoulders, facing the camera straight on, looking into the lens, neutral expression, mouth closed.
Black hair pulled back, forehead and both ears fully visible, no bangs, no hat, no jewelry.
Even soft white studio light on both sides of the face, plain light-gray background.
Real skin texture with age-accurate wrinkles, no makeup, no beauty filter.
```
- **คนแก่:** เติม `deep wrinkles, age spots, white hair pulled back`
- **วัยกลางคน:** `some gray in the hair, fine lines`
- **เด็ก (5-12):** ใช้ `boy/girl` และใส่เสื้อเสมอ `wearing a plain cotton shirt` (ถ้าไม่ระบุเสื้อ GPT มักปฏิเสธ)
- **ทารก:** `Thai baby about 1 year old, wrapped in a plain cotton cloth, front-facing ID-style photo, neutral face` (ห้ามคำว่า naked / shirtless)
- **คนเดียวกันต่างวัย:** แนบรูปหน้าวัยแรกแล้วพิมพ์
  `Same person as the attached photo, now about <อายุ> years old. Keep the same face identity.` ตามด้วยพรอมต์ข้างบน

## ถ้า GPT ปฏิเสธ / ได้รูปไม่ตรง
- **ปฏิเสธ (นโยบายเนื้อหา):** เกือบทุกครั้งเกิดกับเด็ก/ทารก ให้ใส่เสื้อผ้า ตัดคำที่เกี่ยวกับร่างกาย ใช้ "ID-style photo"
- **หน้าเหมือนคนเดิมทุกรูป:** เติมลักษณะเฉพาะ เช่น `square jaw, thick eyebrows, small mole on left cheek, slightly crooked nose`
- **แก่/อ่อนกว่าอายุ:** เขียนอายุเป็นตัวเลขชัดๆ และเติม `looks exactly <อายุ> years old`
- **หน้าเอียง/ยิ้ม:** สั่งแก้ในแชทเดิม `Same person, but face straight to the camera, mouth closed, no smile`

## วางไฟล์แล้วให้โปรแกรมทำต่อ
1. บันทึกรูปเป็น **`face.png`** (PNG หรือ JPG เปลี่ยนชื่อเป็น face.png ได้)
2. วางไว้ในโฟลเดอร์งานของตัวละคร:
   `%LOCALAPPDATA%\Tidmunz Studio\snapgen_data\cc5_jobs\<job>\face.png`
   (job ดูได้จาก `stories/<story>.json` เช่น `story_1029_0051_06` = มั่น 8 ขวบ)
3. เปิดโปรแกรม CC5 Character Studio → เลือกเรื่อง → กด **ทำต่อ** สเต็ป "หน้า" จะเห็นว่ามี face.png แล้วข้ามไปสร้างตัวต่อเอง
   - ถ้าตัวนั้นเคยทำหน้าไปแล้ว ให้กด **ทำใหม่** จากสเต็ป "สร้างตัว" (ไม่ใช่จาก "ลายผ้า" ซึ่งจะลบ face.png)

## ทำไมสร้างผ่านโปรแกรมติดมันส์แล้วพัง (ข้อมูลสำหรับแก้ทีหลัง)
- โปรแกรมไม่ได้ใช้ Bridge ที่พอร์ต 8000 แล้ว ใช้ส่วนขยาย Chrome "Tidmunz ChatGPT" (ที่อยู่ใน `snapgen_data\chrome_relay.json`) ต้องเปิดหน้าต่าง Chrome ของโปรแกรมที่ล็อกอิน ChatGPT ไว้ตลอด
- `timed out` = ส่วนขยายไม่ได้รับงาน / หน้า ChatGPT ค้าง → รีเฟรชหน้า ChatGPT ใน Chrome ของโปรแกรม
- `rate_limited` = โควตารูปของบัญชี ChatGPT หมด (Go plan) รอรีเซ็ตหรือเปลี่ยนบัญชี
- พรอมต์ของโปรแกรมยาวมาก (`_build_story_face_prompt_from_character` ใน snapgen_gui_v2.py) ใช้ได้ แต่ถ้าสร้างเองในเว็บ พรอมต์สั้นข้างบนได้ผลเหมือนกันและโดนปฏิเสธน้อยกว่า
