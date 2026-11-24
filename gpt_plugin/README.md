# ปลั๊กอิน/สกิลสำหรับ GPT (Codex)

โฟลเดอร์ `ai-cc5-garment-flow/` คือสกิลที่สั่งให้ AI ทำงานชุดทีละขั้น 20 ขั้นตามลำดับ ผ่านหน้าต่าง Ai-cc5 Preview

ติดตั้งใน Codex (เครื่องนี้):
```powershell
Copy-Item -Recurse -Force "C:\Users\Apinan\Documents\CC5 Characters\gpt_plugin\ai-cc5-garment-flow" "$env:USERPROFILE\.codex\skills\"
```
แล้วสั่ง Codex เช่น: "ทำชุดนงรักษ์ต่อตาม ai-cc5-garment-flow"

ถ้าจะทำเป็นปลั๊กอิน: ใช้ SKILL.md นี้เป็นเนื้อหาสกิลของปลั๊กอิน (ไม่ต้องแก้)
หมายเหตุ: ChatGPT บนเว็บ (Custom GPT) รันคำสั่งบนเครื่องไม่ได้ ต้องใช้ Codex หรือ GPT ที่รันบนเครื่องนี้
