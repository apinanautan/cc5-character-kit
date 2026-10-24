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


OUTFIT_WORDS = [(re.compile(r"ชุดนักเรียน\s*เก่า\s*ๆ?"), "school_old"), (re.compile(r"ชุดนักเรียน"), "school"),
                (re.compile(r"ชุดธรรมดา|ชุดอยู่บ้าน|ชุดลำลอง|ชุดปกติ"), "normal")]
OUTFIT_LABEL = {"school": "ชุดนักเรียน", "school_old": "ชุดนักเรียน", "normal": "ชุดธรรมดา", "": ""}
GENERIC = ("เพื่อน", "คนงาน", "ญาติ", "ชาวบ้าน", "คนแก่", "เด็ก", "พ่อ", "แม่", "ลูก", "ตำรวจ", "ครู", "หมอ", "พยาบาล", "คน")
SKIP_WORDS = SKIP_WORDS + ("มอไซ", "มอเตอร์ไซค์", "จักรยาน", "สองแถว")


def _outfits(text):
    """'ชุดนักเรียนเก่า ๆ + ชุดธรรมดา' -> (['school_old', 'normal'], text with those words blanked)."""
    found = []
    for rx, key in OUTFIT_WORDS:
        for m in rx.finditer(text):
            found.append((m.start(), key))
        text = rx.sub(lambda m: " " * len(m.group(0)), text)
    return [k for _, k in sorted(found)], text


def _count(text):
    """'2-3 คน' -> 3, 'หลายคน' -> 4 (several unnamed people of the same kind)."""
    m = re.search(r"(\d+)\s*-\s*(\d+)\s*คน", text)
    if m:
        return int(m.group(2)), text.replace(m.group(0), " ")
    m = re.search(r"(\d+)\s*คน", text)
    if m and int(m.group(1)) > 1:
        return int(m.group(1)), text.replace(m.group(0), " ")
    if "หลายคน" in text:
        return 4, text.replace("หลายคน", " ")
    return 1, text


def _is_name(p):
    return bool(PREFIX_RE.match(p)) or (" " not in p and 1 < len(p) <= 14 and not any(
        w in p for w in ("แม่", "พ่อ", "ลูก", "อายุ", "ชุด", "ของ", "ที่", "วัย")))


def _school_age(text):
    m = re.search(r"ม\.\s*(\d)", text)
    if m:
        return 12 + int(m.group(1))
    m = re.search(r"ป\.\s*(\d)", text)
    return 6 + int(m.group(1)) if m else None


def _clean(t):
    return re.sub(r"\s+", " ", t).strip(" +,-/")


def _segments(holder, parens, role_all):
    """Split on '+' (outside brackets); read each segment's bracket notes: outfits / age / name / mother-father / role."""
    units = []
    for seg in [x for x in holder.split("+") if x.strip()]:
        info = {"outfits": [], "name": None, "sex": None, "age": None}

        def take(mm, info=info):
            o, rest = _outfits(parens[int(mm.group(1))])
            info["outfits"] += o
            rest = _clean(rest)
            a = re.search(r"อายุ\s*(\d+)", rest)
            if a:
                info["age"] = int(a.group(1))
            elif rest in ("แม่", "พ่อ"):
                info["sex"] = "f" if rest == "แม่" else "m"
            elif rest and not o and _is_name(rest):
                info["name"] = rest
            elif rest:
                role_all.append(rest)
            return " "

        seg = re.sub(r"§(\d+)§", take, seg)
        units.append((_clean(seg), info))
    return units


def parse(text):
    rows, folders, gen = [], {}, 0
    for raw in text.splitlines():
        line = raw.replace("**", " ").replace("//", " ").strip()
        if not line:
            continue
        m = re.match(r"^(\d+)(?:\.(\d+))?\s*[\.\)]?\s*(.*)$", line)
        num, sub, body = (m.group(1), m.group(2), m.group(3)) if m and m.group(3) else (None, None, line)
        parens = re.findall(r"\(([^)]*)\)", body)
        k = iter(range(len(parens)))
        holder = re.sub(r"\([^)]*\)", lambda mm: " §%d§ " % next(k), body)
        line_outfits, holder = _outfits(holder)  # "ชุดนักเรียน + ชุดธรรมดา" outside brackets = the whole line
        holder = re.sub(r"\+(\s*\+)+", "+", re.sub(r"\+\s*$", "", holder.strip()))
        count, holder = _count(holder)
        role_all = []
        units = _segments(holder, parens, role_all)
        people, states = [], []
        for i, (seg, info) in enumerate(units):
            if count > 1:
                name, state = seg, ""
            elif STATE_RE.match(seg):  # "เกือบ70", "วัยสาว", "4-5ขวบ": another age of the same person(s)
                name, state = "", seg
            elif re.search(r"วัย|ตอน|อายุ", seg) or len(units) > 1:
                name, state = _split_name(seg)
            else:
                name, state = seg, ""
            if info["name"]:  # "พ่อ (นายสิทธิ์)" -> นายสิทธิ์, a man
                info["sex"] = info["sex"] or ("m" if "พ่อ" in seg else "f" if "แม่" in seg else None)
                name = info["name"]
            if name:
                people.append((name, info, seg, i))
            if state:
                states.append((state, info, i))
        mf = re.search(r"ช\s*-\s*ญ|ชาย\s*-\s*หญิง", holder)
        if mf:  # "ญาติๆ ช-ญ": one man + one woman
            base = _clean(holder.replace(mf.group(0), " ").replace("ๆ", ""))
            people = [(base + " ชาย", {"sex": "m"}, base, 0), (base + " หญิง", {"sex": "f"}, base, 0)]
        if not people:
            people = [(_clean(holder) or body, {"outfits": [], "name": None, "sex": None, "age": None}, body, 0)]
        if not states:
            states = [("", {"outfits": [], "age": None}, -1)]
        role = ", ".join(role_all)
        heads = []
        for pname, pinfo, pseg, pi in people:
            first = pname.split()[0] if pname.split() else pname
            short = _clean(pname) if (count > 1 or any(first.startswith(g) for g in GENERIC)) else first
            if count > 1:  # "เพื่อน ๆ เด็กประถมของสุดา" -> "เพื่อน ๆ เด็กประถม"
                short = _clean(re.split(r"ของ|ที่", short)[0]) or short
            heads.append(short)
            for st, sinfo, si in states:
                outs = sinfo.get("outfits") or (pinfo.get("outfits") if si in (pi, -1) else None) or line_outfits or [""]
                for n in range(count):
                    gen += 1
                    sex = pinfo.get("sex") or guess_sex(pseg + " " + st)
                    if sex == "?" and len(people) == 1:
                        sex = guess_sex(body)
                    if sex == "?" and count > 1:
                        sex = "mfm"[n % 3] if "คนงาน" in pname else "mf"[n % 2]
                    age = (sinfo.get("age") or pinfo.get("age") or _school_age(st or pseg)
                           or guess_age(st or pseg))
                    if age == 35 and re.search(r"พ่อ|แม่", pseg + " " + role) and "ลูก" not in pseg:
                        age = 45  # parents of school kids
                    if age == 35 and not st and count == 1 and any(o.startswith("school") for o in outs):
                        age = 15
                    person = ("%s#%d" % (short, gen) if count > 1 else
                              short if any(first.startswith(g) for g in GENERIC) or mf else base_name(short))
                    same = [r for r in rows if r["person"] == person]
                    if sex == "?" and same:
                        sex = same[-1]["sex"]
                    if age == 35 and same and not st:
                        age = same[-1]["age"]
                    if count > 1:  # a group: different ages
                        age = max(1, age + (n % 3 - 1) * (1 if age < 13 else 7))
                    for o in outs:
                        label = " ".join(x for x in [short + (" %d" % (n + 1) if count > 1 else ""),
                                                     _label("", st) if st else "",
                                                     OUTFIT_LABEL[o] if len(outs) > 1 else ""] if x)
                        rows.append({"name": _clean(label), "sex": sex, "age": age, "_num": num,
                                     "notes": ", ".join(notes_of(st + " " + pseg)), "outfit": o, "role": role,
                                     "person": person, "use": sex != "?" or not any(w in pseg for w in SKIP_WORDS)})
        if num and not sub:
            folders[num] = ("%s. %s" % (num, " + ".join(dict.fromkeys(heads))))[:60]
    for r in rows:
        r["folder"] = folders.get(r.pop("_num"), "")
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
