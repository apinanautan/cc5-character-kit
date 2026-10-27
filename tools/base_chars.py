# Fixed-outfit characters (uniforms etc.) kept whole as bases in the library: <LIB>\ชุดตายตัว\
# file = short name; full description lives here + data/wardrobe_db.json. Copy:  python tools\base_chars.py
import os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

DIR = os.path.join(kit.LIB, "ชุดตายตัว")
S = os.path.join(os.path.expanduser("~"), "Desktop", "จุดหักเหของชีวิต")
# (file, group, sex/age, detail, source)
BASES = [
    ("นร หญิงมัธยม 01.iAvatar", "ชุดนักเรียนหญิงมัธยม", "หญิง 15", "เสื้อขาวคอซอง โบว์กรมท่า แขนพองจีบ + กระโปรงจีบรอบตัวกรมท่าคลุมเข่า + ถุงเท้าขาว + รองเท้าหนังดำ", r"1. สุดา\สุดา วัย 15 ชุดนักเรียน.iAvatar"),
    ("นร หญิงมัธยม 02.iAvatar", "ชุดนักเรียนหญิงมัธยม", "หญิง 14", "เหมือน 01 (คนละหน้า/รูปร่าง)", r"7. สุภา\สุภา ชุดนักเรียน.iAvatar"),
    ("นร ชายมัธยม 01.iAvatar", "ชุดนักเรียนชายมัธยม", "ชาย 17", "เชิ้ตขาวแขนสั้น + กางเกงขายาวกรมท่า + รองเท้าหนังดำ", r"5. สมโชค\สมโชค ชุดนักเรียน.iAvatar"),
    ("นร ชายประถม 01.iAvatar", "ชุดนักเรียนชายประถม", "เด็กชาย 9-10", "เชิ้ตขาว + กางเกงขาสั้นกากี + เข็มขัด + ถุงเท้าขาว รองเท้าดำ", r"4. เพื่อน ๆ เด็กประถม\เพื่อนเด็กประถม 1.iAvatar"),
    ("นร ชายประถม 02.iAvatar", "ชุดนักเรียนชายประถม", "เด็กชาย 9-10", "เหมือน 01 (คนละหน้า)", r"4. เพื่อน ๆ เด็กประถม\เพื่อนเด็กประถม 2.iAvatar"),
    ("นร ชายประถม 03.iAvatar", "ชุดนักเรียนชายประถม", "เด็กชาย 9-10", "เหมือน 01 (คนละหน้า)", r"4. เพื่อน ๆ เด็กประถม\เพื่อนเด็กประถม 3.iAvatar"),
    ("คนงานชาย 01.iAvatar", "คนงาน/ชาวบ้านชาย", "ชายหนุ่ม", "เชิ้ตเปิดทับเสื้อยืด + กางเกงขายาวสีเข้ม", r"8. คนงานฟาร์มหมู\คนงาน 1.iAvatar"),
    ("คนงานชาย 02.iAvatar", "คนงาน/ชาวบ้านชาย", "ชายหนุ่ม", "เชิ้ตเปิดทับเสื้อยืด + กางเกงขายาวสีเข้ม (อีกแบบ)", r"8. คนงานฟาร์มหมู\คนงาน 2.iAvatar"),
    ("ชาวนาแก่ 01.iAvatar", "ชาวนา", "ชายแก่", "หมวกสาน + เสื้อกรมท่า + ผ้าขาวม้าคาดเอว + กางเกงสามส่วน", r"8. คนงานฟาร์มหมู\คนงาน 3.iAvatar"),
]

if __name__ == "__main__":
    os.makedirs(DIR, exist_ok=True)
    for f, *_, src in BASES:
        dst = os.path.join(DIR, f)
        if not os.path.exists(dst):
            shutil.copy2(os.path.join(S, src), dst)
            print("copied", f, flush=True)
    lines = ["รายการชุดตายตัว (หยิบทั้งตัวมาใช้เป็นเบส แล้วเปลี่ยนหัว/หน้าได้)", ""]
    lines += ["%s  |  %s  |  %s  |  %s" % (f, g, a, d) for f, g, a, d, _ in BASES]
    open(os.path.join(DIR, "_รายการ.txt"), "w", encoding="utf-8-sig").write("\n".join(lines) + "\n")
    print("done")
