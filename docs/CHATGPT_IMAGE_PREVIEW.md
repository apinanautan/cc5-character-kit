# วิธีส่งภาพ Preview ให้ผู้ใช้ดูใน ChatGPT

ยืนยัน 2026-11-08: ผู้ใช้เคยดูภาพที่แสดงในแชต GPT ได้จริง

เป้าหมาย: ดูรูปบนมือถือใน ChatGPT โดยตรง ไม่ต้องดาวน์โหลด ไม่ใช้ Google Drive ของบริษัท

ขั้นตอน:
1. เรนเดอร์งานจริงจาก CC5/Blender เป็น JPG/PNG ไว้บนเครื่อง Windows
2. ถ้าต้องตรวจหลายตัว ให้จัดเป็น contact sheet ภาพเดียว พร้อมชื่อ
3. ผ่าน Remote Desktop Commander read_file(path,deviceId) อ่านพาธรูปจริงบนเครื่อง
4. ในผลลัพธ์เครื่องมือ มองหา content_items ที่ type=image, mimeType และ data (base64)
5. ส่งต่อ image block ผ่าน functions.exec ด้วย image({image_url: "data:" + mimeType + ";base64," + data, detail:"high"}) เพื่อแสดงภายในบทสนทนา ChatGPT
6. ระบุว่าเป็นภาพงานจริง/รุ่นอะไร และอะไรยังไม่ผ่าน QA

ข้อจำกัด: วิธีนี้แสดงภาพภายในแชต GPT ที่รองรับ ไม่ได้สร้าง URL สาธารณะหรือเปิดได้ในทุกแอปเอง ไม่ควรกล่าวอ้างว่าเป็นระบบป้องกันการแชร์ต่อโดยสมบูรณ์
ห้ามนำภาพเผยแพร่ GitHub public/Drive/เว็บภายนอกโดยไม่ได้รับอนุญาตเฉพาะครั้ง
หากแอปแสดงภาพไม่สำเร็จ ให้แจ้งและถามผู้ใช้ก่อนเลือกวิธีส่งอื่น

ตัวอย่างภาพที่เตรียมไว้แล้ว: docs/duang_main_cast_10_20261108.jpg (ตัวละครหลัก 10 ตัวจากภาพเรนเดอร์ CC5)

## ntfy notification & image delivery — updated 2026-11-09

ผู้ใช้ยืนยันได้รับ Push Notification บนโทรศัพท์และขอให้ส่งภาพงาน CC5 ผ่าน https://ntfy.sh/Pic-Gptz เป็นช่องทางหลัก

วิธี: เรนเดอร์ภาพจริง -> สร้าง contact sheet เมื่อมีหลายชิ้น -> ตรวจไฟล์ภาพและสถานะ QA -> POST JPEG/PNG ไป URL หัวข้อ พร้อม Filename, Title, Priority=5 -> อ่าน attachment.url จาก response -> ตรวจ URL ว่าเปิดได้และแนบลิงก์ในบทสนทนา -> ใช้วิธีแสดงภาพ inline เดิมเสริมได้

PowerShell:
    $file = 'C:\path\preview.jpg'
    $r = Invoke-RestMethod -Method Post -Uri 'https://ntfy.sh/Pic-Gptz' -InFile $file -ContentType 'image/jpeg' -Headers @{'Filename'='CC5-preview.jpg';'Title'='CC5 Preview';'Priority'='5'} -TimeoutSec 30
    $r.attachment.url

การ POST สำเร็จไม่ยืนยันว่า Push ถึง iPhone เสมอ ลิงก์รูปเป็นสาธารณะชั่วคราว ห้ามส่งไฟล์ส่วนตัว/ความลับ และไม่ให้ย้ายไฟล์อื่นเข้าโฟลเดอร์เรื่องใน G: หรือ Desktop
ข้อความเก่าเรื่อง ChatGPT-only เป็นวิธีเดิม ไม่ใช่ข้อห้ามส่ง ntfy หลังมีคำสั่งล่าสุด

### เฉพาะ GPT ที่คุยกับผู้ใช้
- **ใช้ ntfy.sh/Pic-Gptz เฉพาะ GPT ในแชตนี้เป็นผู้สั่งส่งภาพให้ผู้ใช้โดยตรงเท่านั้น** (GPT เรียกเครื่องมือ shell เพื่อ POST ตามคำสั่งผู้ใช้ได้)
- **ห้ามให้โปรแกรม CC5, Blender, worker, automation, Claude, Codex, agent ตัวอื่น, plugin อื่น หรือสคริปต์เบื้องหลังส่ง ntfy เอง** และห้ามผูก ntfy เข้ากับ pipeline/โปรเจกต์อื่น
- ไม่ส่งอัปเดตสถานะ งานอื่น หรือ notification อัตโนมัติ; ส่งเฉพาะรูปจากงานที่ผู้ใช้ขอให้ GPT ส่งในบทสนทนานี้
- กฎนี้จำกัดเฉพาะการใช้ ntfy ไม่จำกัดการเรนเดอร์/ทดสอบ/QA ที่ทำอยู่ตามปกติ
