# Name the character folders of a story like the work sheet ("ใบงาน"): "<number>.<label from the sheet>", several people of one
# sheet line in ONE folder. Works on Desktop\<story>\ and on Google Drive <story>\<story> ตัวละคร\. Only .iAvatar files are moved
# (never deleted); an old folder is removed only when it is empty afterwards. Everything is logged to runs\drive_backup\rename_log_<story>.json.
#   python tools\organize_story_folders.py <story> [--apply]        (without --apply it only prints what it would do)
import json, os, shutil, sys, time

STORIES = {
    "ดวงเมียน้อย": {  # sheet line -> folder name ; old folder names (Drive: person names, Desktop: sheet numbers) that belong in it
        "1.สุนีย์ + ปรีชา":              {"drive": ["สุนีย์", "ปรีชา"], "desk": ["1"]},
        "2.นารี":                         {"drive": ["นาวี"], "desk": ["2"]},
        "3.นิวัตน์":                      {"drive": ["นิวัตน์"], "desk": ["3"]},
        "5.เมียน้อยของปรีชา":              {"drive": ["เมียน้อยปรีชา"], "desk": ["5"]},
        "6.ชาวบ้านหลายคน":                 {"drive": ["ชาวบ้าน"], "desk": ["6"]},
        "7.วินัย":                        {"drive": ["วินัย"], "desk": ["7"]},
        "8.เถ้าแก่โรงงานขนม":              {"drive": ["เถ้าแก่โรงงานขนม"], "desk": ["8"]},
        "9.ธีภพ + ปรียา":                 {"drive": ["พีภพ", "ปรียา"], "desk": ["9"]},
        "10.อรทัย":                       {"drive": ["อรทัย"], "desk": ["10"]},
        "11.รุ่นพี่ที่มหาลัย":              {"drive": ["รุ่นพี่มหาลัยชาย1", "รุ่นพี่มหาลัยหญิง1"], "desk": ["11"]},
        "12.พระวัดป่า":                    {"drive": ["พระวัดป่า"], "desk": ["12"]},
        "13.หญิงสาวที่โกนผมปฏิบัติธรรม":     {"drive": ["หญิงปฏิบัติธรรม1", "หญิงปฏิบัติธรรม2"], "desk": ["13"]},
    }
}
story = sys.argv[1]; apply = "--apply" in sys.argv
plan = STORIES[story]
roots = {"desk": os.path.join(os.path.expanduser("~"), "Desktop", story), "drive": os.path.join(r"G:\ไดรฟ์ของฉัน", story, story + " ตัวละคร")}
log = []


def avatars_under(folder):
    return [os.path.join(dp, f) for dp, dn, fn in os.walk(folder) for f in fn if f.lower().endswith(".iavatar")]


for kind, root in roots.items():
    if not os.path.isdir(root):
        print("no folder:", root); continue
    print("==", kind, root)
    for new, olds in plan.items():
        target = os.path.join(root, new)
        for old in olds[kind]:
            src = os.path.join(root, old)
            if not os.path.isdir(src) or os.path.normcase(src) == os.path.normcase(target):
                continue
            for f in avatars_under(src):
                dst = os.path.join(target, os.path.basename(f))
                print("  move %-50s -> %s" % (os.path.relpath(f, root), new))
                if apply:
                    os.makedirs(target, exist_ok=True)
                    if os.path.exists(dst):
                        print("   !! exists, skipped:", dst); continue
                    shutil.move(f, dst); log.append({"from": f, "to": dst})
            if apply:
                left = [os.path.join(dp, x) for dp, dn, fn in os.walk(src) for x in fn]
                if not left:   # remove only empty folders (no files at all inside)
                    for dp, dn, fn in sorted(os.walk(src, topdown=False), key=lambda t: -len(t[0])):
                        os.rmdir(dp)
                else:
                    print("   (kept old folder, other files inside:", len(left), ")")
if apply:
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runs", "drive_backup", "rename_log_%s_%s.json" % (story, time.strftime("%H%M%S")))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(log, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1); print("log:", out)
