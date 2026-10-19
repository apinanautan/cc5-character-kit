# Turn a pasted Thai character list into character rows (name, sex, age, folder, notes).
# Understands lines like the user's story lists:
#   1 นายสมจิต+นางอุไร วัยเกือบ40+เกือบ70      -> 4 people (each name at each age)
#   1.1 สมจิตวัย70 แผลไฟลวกที่แขน              -> same folder as 1, burn scar on the arm
#   2 ญาติๆ ช-ญ                                 -> one man + one woman
#   3 อรวรรณ ลูกสาว วัยประถม+วัยสาว+ตอนท้อง     -> 3 versions of one person
# Anything it gets wrong is fixed in the app's table before starting.
import re

SKIP_WORDS = ("รถ", "สุนัข", "หมา", "แมว", "ควาย", "วัว", "ฉาก")
MALE = ("นาย", "ชาย", "ลุง", "ตา ", "พ่อ", "หนุ่ม", "ปู่", "น้า ชาย", "พระ", "เณร", "ผู้ใหญ่บ้าน", "เด็กชาย", "ด.ช.")
FEMALE = ("นาง", "หญิง", "ป้า", "ยาย", "แม่", "สาว", "ย่า", "ด.ญ.", "เด็กหญิง", "ลูกสาว")
STATE_WORDS = ("วัย", "ตอน", "อายุ", "ขวบ", "ทารก", "ประถม", "แก่", "ชรา", "ท้อง", "ผอม", "ซูบ", "แผล", "หนุ่ม", "สาว",
               "เด็ก", "กลางคน", "วัยรุ่น")


def _num(s):
    m = re.search(r"(\d+)\s*-\s*(\d+)", s)
    if m:
        return (int(m.group(1)) + int(m.group(2))) // 2
    m = re.search(r"(\d+)", s)
    if not m:
        return None
    n = int(m.group(1))
    return n - 1 if "เกือบ" in s else n


def guess_age(text):
    n = _num(text)
    if n is not None and ("ขวบ" in text or "เดือน" in text):
        return max(n, 1) if "ขวบ" in text else 1
    if n is not None and 0 < n < 110:
        return n
    for words, age in ((("ทารก", "แรกเกิด", "เด็กอ่อน"), 1), (("อนุบาล",), 5), (("ประถม",), 9), (("มัธยม", "วัยรุ่น"), 16),
                       (("เด็ก",), 8), (("ท้อง",), 27), (("หนุ่ม", "สาว"), 24), (("กลางคน",), 45),
                       (("แก่", "ชรา", "ยาย", "ตา", "ปู่", "ย่า", "บ้านพักคนชรา"), 72), (("ป้า", "ลุง"), 55)):
        if any(w in text for w in words):
            return age
    return 35


def guess_sex(text):
    if any(w in text for w in ("ลูกชาย", "เด็กชาย", "หลานชาย")):
        return "m"
    if any(w in text for w in FEMALE):
        return "f"
    if any(w in text for w in MALE):
        return "m"
    return "?"


def notes_of(text):
    n = []
    if "แผล" in text or "ไฟไหม้" in text or "ไฟลวก" in text or "น้ำร้อนลวก" in text:
        where = "หน้า" if "หน้า" in text else "ขา" if "ขา" in text else "แขน"
        n.append("แผลไฟไหม้ที่" + where)
    if "ผอม" in text or "ซูบ" in text:
        n.append("ผอม")
    if "ท้อง" in text and "ทารก" not in text:
        n.append("ท้อง")
    return n


STATE_RE = re.compile(r"เกือบ|วัย|ตอน|อายุ|\d|ทารก|ประถม|(?<!ลูก)สาว|(?<!แฟน)หนุ่ม|ซูบ|ผอม|ท้อง|แผล|ชรา|กลางคน")
PREFIX_RE = re.compile(r"^(นางสาว|นาย|นาง|ด\.ช\.|ด\.ญ\.|เด็กชาย|เด็กหญิง)")


def _split_name(seg):
    """'อรวรรณ ลูกสาว วัยประถม' -> ('อรวรรณ ลูกสาว', 'วัยประถม'); no state -> (seg, '')."""
    m = STATE_RE.search(seg)
    if not m or m.start() == 0:
        return ("", seg) if m else (seg, "")
    return seg[:m.start()].strip(" ,-"), seg[m.start():].strip()


def _label(name, state):
    if state and state[0].isdigit() or state.startswith("เกือบ"):
        state = "วัย" + state
    return re.sub(r"\s+", " ", (name + " " + state).strip())


def _expand(text):
    """-> list of (display name, text used for guessing)."""
    if re.search(r"ช\s*-\s*ญ|ชาย\s*-\s*หญิง", text):
        base = re.sub(r"ช\s*-\s*ญ|ชาย\s*-\s*หญิง", "", text).replace("ๆ", "").strip()
        return [(base + " ชาย", base + " ชาย"), (base + " หญิง", base + " หญิง")]
    segs = [s.strip() for s in text.split("+") if s.strip()]
    if len(segs) == 1:
        name, state = _split_name(segs[0]) if re.search(r"วัย|ตอน|อายุ|\d", segs[0]) else (segs[0], "")
        return [(_label(name or segs[0], state), segs[0])]
    names, states = [], []
    for s in segs:
        name, state = _split_name(s)
        if name:
            names.append(name)
        if state:
            states.append(state)
    names = names or [segs[0]]
    states = states or [""]
    return [(_label(n, st), n + " " + st) for n in names for st in states]


def parse(text):
    rows, folders = [], {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = re.match(r"^(\d+)(?:\.(\d+))?[\.\)]?\s+(.*)$", line)
        num, sub, body = (m.group(1), m.group(2), m.group(3)) if m else (None, None, line)
        if num and not sub:
            head = re.sub(r"ช\s*-\s*ญ|ชาย\s*-\s*หญิง", "", body)
            head = " + ".join(p for p in (re.split(r"เกือบ|วัย|ตอน|อายุ|\d", x)[0].strip() for x in head.split("+")) if p)
            folders[num] = ("%s. %s" % (num, re.sub(r"\s+", " ", head).strip()))[:60]
        folder = folders.get(num, ("%s. %s" % (num, body))[:60] if num else "")
        for label, guess in _expand(body):
            sex = guess_sex(guess)
            same = [r for r in rows if base_name(r["name"]) == base_name(label)]
            if sex == "?" and same:
                sex = same[-1]["sex"]
            age = guess_age(guess)
            if age == 35 and same and not re.search(r"\d|วัย|ตอน", guess):
                age = same[-1]["age"]
            rows.append({"name": label, "sex": sex, "age": age, "folder": folder, "notes": ", ".join(notes_of(guess)),
                         "use": sex != "?" or not any(w in body for w in SKIP_WORDS)})
    return rows


def base_name(name):
    w = PREFIX_RE.sub("", name.strip())
    return re.split(r"\s|วัย|ตอน|ซูบ|ผอม", w)[0]


def age_group(age):
    return "baby" if age < 3 else "child" if age < 13 else "adult" if age < 45 else "middle" if age < 60 else "old"


if __name__ == "__main__":
    import json, sys
    sample = sys.stdin.read() if not sys.stdin.isatty() else (
        "1 นายสมจิต+นางอุไร วัยเกือบ40+เกือบ70\n1.1 สมจิตวัย70 แผลไฟลวกที่แขน\n1.2 สมจิตซูบผอม\n2 ญาติๆ ช-ญ\n"
        "3 อรวรรณ ลูกสาว วัยประถม+วัยสาว+ตอนท้อง\n4 บรรพจ แฟนหนุ่มอรวรรณ\n5 รถยนต์\n6 ลูกชายอรวรรณ ทารก+4-5ขวบ\n"
        "7 ชาวบ้าน เพื่อนบ้านหญิง มีบทพูด\n8 คนแก่บ้านพักคนชรา ช-ญ")
    for r in parse(sample):
        print(json.dumps(r, ensure_ascii=False))
