"""ONE COMMAND outfit flow for any story: decide -> design -> build -> check -> wear in CC5. No AI hand-fixing.

  .venv\\Scripts\\python.exe outfit_flow.py decide --story <slug>
        Reads stories/<slug>.json, writes runs/<slug>/outfit_decisions.json: for every character MAKE (build a new
        outfit) or KEEP (library outfit is enough) with the reasons. Rules are in decide() below and can be overridden
        per character in the story JSON with "outfit_make": true/false.
  .venv\\Scripts\\python.exe outfit_flow.py design --story <slug> --actor <character key>
        Writes runs/<slug>/outfits/<actor>/design.json (fabric presets from fabric_presets.json, picked by occasion /
        sex / era). Edit that file by hand if you want another fabric, then run make.
  .venv\\Scripts\\python.exe outfit_flow.py make --story <slug> --actor <key> --body <body_tpose.obj>
        [--top_mesh <final.obj of an existing top run> | --top_image <garment.png>] [--stop_before cc5]
        Builds everything below and only then touches CC5 (CC5 is never started, closed or saved over by this script):
          top   : make_garment (Hunyuan 512 -> clean -> place -> tightfit -> push)  [skipped with --top_mesh]
                  smooth_bake (smooth mesh + seams as normal map) -> buttons_detect -> add_buttons (real buttons)
          bottom: make_skirt from the body (A-line / pencil) when design says skirt
          layers: push_layers (top clears body, under-clothes and the new bottom)
          fabric: bake_fabric (user's fabric photos -> diffuse maps, buttons own colour)
          qc    : qc_outfit renders -> outfit_*.png  (CHECK: files exist)
          cc5   : wear_placed for bottom (final=0) then top (pose renders + character saved as a NEW file)
  .venv\\Scripts\\python.exe outfit_flow.py all --story <slug> --body <body.obj>   decide + design + make for every MAKE.
Every step writes new files only. A failing automatic check stops with the reason.
"""
import argparse, json, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PY = sys.executable
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.3\blender.exe"
FABRIC_DIR = Path(r"G:\คอมพิวเตอร์เครื่องอื่นๆ\คอมพิวเตอร์ของฉัน\โมชั่น\Prop ของใช้ต่างๆ\เสื้อผ้า-ทรงผม\ลายผ้า")
PRESETS = json.load(open(HERE / "fabric_presets.json", encoding="utf-8"))


def sh(cmd, step):
    t = time.time(); print(f"\n=== {step} ===", flush=True)
    r = subprocess.run([str(c) for c in cmd], cwd=HERE, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = r.stdout + r.stderr
    if r.returncode != 0 or "Traceback" in out:
        sys.exit(f"[{step}] FAILED (exit {r.returncode}):\n" + out[-3000:])
    print(f"[{step}] ok {round(time.time() - t)} s", flush=True); return out


def blender(script, *args, step):
    return sh([BLENDER, "-b", "--factory-startup", "-P", HERE / "blender" / script, "--", *args], step)


def check(ok, step, why):
    if not ok: sys.exit(f"[{step}] CHECK FAILED: {why}")


def story(slug):
    return json.load(open(ROOT / "stories" / f"{slug}.json", encoding="utf-8"))


def brief_for(st, key):
    """cast_brief entry that belongs to a production character key (e.g. ..._nongrak_28 -> nongrak)"""
    for k, v in st.get("cast_brief", {}).items():
        if k in key: return k, v
    return None, {}


# ---------------------------------------------------------------- decide
OCCUPATION_WORDS = ["ช่าง", "ตำรวจ", "หมอ", "พยาบาล", "ครู", "ทหาร", "พนักงาน", "เสริมสวย", "แม่ค้า", "นักเรียน"]
STYLE_WORDS = ["แต่งตัวสวย", "เนี้ยบ", "หรู", "โดดเด่น", "ตัวเอก"]


def decide(slug):
    st = story(slug); out = {}
    for key, ch in st.get("characters", {}).items():
        bk, br = brief_for(st, key); role = br.get("role", "") + " " + ch.get("notes", "") + " " + ch.get("style", "")
        why, score = [], 0
        if "outfit_make" in ch:
            out[key] = dict(decision="MAKE" if ch["outfit_make"] else "KEEP", reasons=["story JSON outfit_make"]); continue
        if bk and bk == st.get("lead"): score += 2; why.append("ตัวเอก ต้องมีชุดเฉพาะตัว")
        if any(w in role for w in STYLE_WORDS): score += 1; why.append("บทระบุว่าแต่งตัวสวย/เนี้ยบ")
        if any(w in role for w in OCCUPATION_WORDS): score += 1; why.append("อาชีพในบทต้องดูออกจากชุด")
        qa = ROOT / "runs" / slug / key / "qa.json"
        if qa.exists() and json.load(open(qa, encoding="utf-8")).get("outfit") == "FIX":
            score += 2; why.append("QA ชุดเดิมได้ FIX")
        if not ch.get("outfit"): score += 2; why.append("ยังไม่มีชุดล็อกไว้")
        if br.get("count") or "สมทบ" in role or "กลุ่ม" in role: score -= 2; why.append("ตัวประกอบกลุ่ม ใช้ชุดคลังพอ")
        dec = "MAKE" if score >= 2 else "KEEP"
        if dec == "KEEP" and not why: why.append("ชุดคลังที่ล็อกไว้ตรงบทแล้ว")
        out[key] = dict(decision=dec, score=score, reasons=why, name=ch.get("name"))
    p = ROOT / "runs" / slug / "outfit_decisions.json"; p.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for k, v in out.items(): print(v["decision"], k, v.get("name", ""), "|", "; ".join(v["reasons"]))
    print("->", p); return out


# ---------------------------------------------------------------- design
def design(slug, key, run_dir=None):
    st = story(slug); ch = st["characters"][key]
    occ, sex = ch.get("occasion", "everyday"), ch.get("sex", "female")
    rule = next((r for r in PRESETS["rules"] if r["occasion"] in (occ, "*") and r["sex"] in (sex, "*")), None)
    check(rule is not None, "design", f"no fabric rule for occasion={occ} sex={sex} in fabric_presets.json")
    d = dict(story=slug, actor=key, occasion=occ, era=st.get("era_profile"), reason=rule["why"],
             top=dict(PRESETS["fabrics"][rule["top"]], preset=rule["top"], button_hex=rule.get("button_hex", "F4F1EA")),
             bottom=dict(kind=rule["bottom"]["kind"], style=rule["bottom"].get("style", "aline"),
                         hem_k=rule["bottom"].get("hem_k", 1.0), flare=rule["bottom"].get("flare", 4),
                         **PRESETS["fabrics"][rule["bottom"]["fabric"]], preset=rule["bottom"]["fabric"]),
             remove=rule.get("remove", []))
    p = (run_dir or ROOT / "runs" / slug / "outfits" / key) / "design.json"; p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists(): json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(json.load(open(p, encoding="utf-8")), ensure_ascii=False, indent=1)); print("->", p); return p


def fabric_path(name):
    hits = list(FABRIC_DIR.rglob(name)); check(hits, "fabric", f"{name} not found under {FABRIC_DIR}"); return hits[0]


def fabric_file(spec, run, tag):
    """photo to bake. A plain colour swatch + "tint_weave" = that colour with the weave of a white cotton photo."""
    src = fabric_path(spec["file"])
    if not spec.get("tint_weave"): return src
    from PIL import Image, ImageStat
    col = ImageStat.Stat(Image.open(src).convert("RGB")).mean
    wv = Image.open(fabric_path(spec["tint_weave"])).convert("RGB"); m = ImageStat.Stat(wv).mean
    out = run / f"fabric_{tag}.png"
    Image.merge("RGB", [ch.point(lambda x, k=col[i] / m[i]: min(255, int(x * k))) for i, ch in enumerate(wv.split())]).save(out)
    return out


# ---------------------------------------------------------------- make
def make(slug, key, body, top_mesh=None, top_image=None, stop_before=None, takeoff="", only=None, run_dir=None, top_final=None):
    run = run_dir or ROOT / "runs" / slug / "outfits" / key; f = lambda n: run / n
    d = json.load(open(f("design.json"), encoding="utf-8")); body = Path(body).resolve()
    steps = ["top", "bottom", "layers", "fabric", "qc", "cc5", "physics"]
    todo = [only] if only else steps[:steps.index(stop_before)] if stop_before else steps
    ph = dict(dict(top_hem=0.35, top_arm=0.2, skirt_hem=0.5), **d.get("physics", {}))   # grey at the edge, 0..1 (light)
    if "top" in todo and not f("top_buttons.obj").exists():
        if not top_mesh:
            check(top_image, "top", "give --top_mesh (finished final.obj) or --top_image (garment picture)")
            sh([PY, "make_garment.py", "--image", top_image, "--run", f("top_build"), "--body", body, "--stop_before", "qc"], "top build")
            top_mesh = f("top_build") / "final.obj"
        shutil.copyfile(top_mesh, f("top_detail.obj"))
        blender("smooth_bake.py", f("top_detail.obj"), f("top_low.obj"), f("top_normal.png"), str(f("qc_bake_")), step="smooth bake")
        out = sh([PY, "buttons_detect.py", "--run", run, "--mesh", "top_detail.obj", "--out", "buttons.json", "--thr", 0.08], "buttons detect")
        n = json.loads(out.strip().splitlines()[-1])["found"]; print("buttons found", n)
        if n:
            blender("add_buttons.py", f("top_low.obj"), f("top_normal.png"), f("buttons.json"), f("top_buttons.obj"),
                    f("top_normal_btn.png"), str(f("qc_btn_")), step="add buttons")
        else:
            shutil.copyfile(f("top_low.obj"), f("top_buttons.obj")); shutil.copyfile(f("top_normal.png"), f("top_normal_btn.png"))
    if "bottom" in todo and d["bottom"]["kind"] == "skirt" and not f("bottom.obj").exists():
        b = d["bottom"]
        out = blender("make_skirt.py", body, f("bottom.obj"), f"style={b['style']}", f"hem_k={b['hem_k']}", f"flare={b['flare']}", step="skirt")
        print([l for l in out.splitlines() if l.startswith(("WAIST", "WROTE"))])
    extra = [f("bottom.obj")] if f("bottom.obj").exists() else []
    if "layers" in todo:
        out = blender("push_layers.py", f("top_buttons.obj"), body, f("top_final.obj"), 0.5,
                      "CC_Base_Body" + ("" if extra else ",BBJ_Base"), *extra, step="layers")
        print([l for l in out.splitlines() if l.startswith("PUSHED")])
    if "fabric" in todo:
        t = d["top"]; cell = (0.0078, 0.0078)
        bj = f("top_buttons.buttons_uv.json")
        blender("bake_fabric.py", top_final or f("top_final.obj"), fabric_file(t, run, "top"), f("top_diffuse.png"), t["tile_cm"], 2048,
                *((bj, 0) if bj.exists() else cell), d["top"]["button_hex"], f("top_normal_btn.png"), str(f("qc_top_")), step="fabric top")
        if extra:
            b = d["bottom"]
            blender("bake_fabric.py", f("bottom.obj"), fabric_file(b, run, "bottom"), f("bottom_diffuse.png"), b["tile_cm"], 1024,
                    0.5, 0.5, "-", step="fabric bottom")
        # physics weight maps (light: hem + a touch under the arms; buttons black)
        blender("make_weightmap.py", top_final or f("top_final.obj"), f("top_physics_wmap.png"), "top", f"hem={ph['top_hem']}",
                f"arm={ph['top_arm']}", *([bj] if bj.exists() else []), step="weightmap top")
        if extra:
            blender("make_weightmap.py", f("bottom.obj"), f("bottom_physics_wmap.png"), "skirt", f"hem={ph['skirt_hem']}", "arm=0",
                    step="weightmap bottom")
    if "qc" in todo:
        specs = ([f"{f('bottom.obj')}|{f('bottom_diffuse.png')}|-"] if extra else []) + \
                [f"{f('top_final.obj')}|{f('top_diffuse.png')}|{f('top_normal_btn.png')}"]
        blender("qc_outfit.py", body, str(f("outfit_")), *specs, step="qc")
        check(all(f(f"outfit_{v}.png").exists() for v in ("front", "side", "back", "waist")), "qc", "renders missing")
        print("look at:", *sorted(run.glob("outfit_*.png")), sep="\n  ")
    if "cc5" in todo:
        sys.path.insert(0, str(HERE)); import cc5call
        name = key.split("_")[-2] if "_" in key else key
        rm = ",".join(d.get("remove", []) + ([takeoff] if takeoff else []))
        if extra:
            r = cc5call.call(str(HERE / "cc5" / "wear_placed.py"), dict(obj=str(f("bottom.obj")), out=str(run), name=f"{name}_{d['bottom']['preset']}",
                             diffuse=str(f("bottom_diffuse.png")), remove=rm, final="0"), timeout=3600)
            check(r["status"] == "ok", "cc5 bottom", r.get("log", "")); rm = ""
        (run / "cc5").mkdir(exist_ok=True)
        r = cc5call.call(str(HERE / "cc5" / "wear_placed.py"), dict(obj=str(f("top_final.obj")), out=str(run / "cc5"), name=f"{name}_{d['top']['preset']}",
                         diffuse=str(f("top_diffuse.png")), normal=str(f("top_normal_btn.png")), remove=rm), timeout=3600)
        check(r["status"] == "ok", "cc5 top", r.get("log", "")); print(r.get("log", ""))
    if "physics" in todo:
        sys.path.insert(0, str(HERE)); import cc5call
        name = key.split("_")[-2] if "_" in key else key
        cl = [f"{name}_{d['top']['preset']}|{f('top_physics_wmap.png')}"] + \
             ([f"{name}_{d['bottom']['preset']}|{f('bottom_physics_wmap.png')}"] if extra else [])
        (run / "cc5").mkdir(exist_ok=True)
        r = cc5call.call(str(HERE / "cc5" / "set_physics.py"), dict(cloths=";".join(cl), out=str(run / "cc5"),
                         save=f"{name}_outfit_physics_on_character.ccProject"), timeout=3600)
        check(r["status"] == "ok", "physics", r.get("log", "")); print(r.get("log", ""))
    print("\nDONE ->", run)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["decide", "design", "make", "all"])
    ap.add_argument("--story", required=True); ap.add_argument("--actor"); ap.add_argument("--body")
    ap.add_argument("--run-dir", type=Path); ap.add_argument("--top-final", type=Path)
    ap.add_argument("--top_mesh"); ap.add_argument("--top_image"); ap.add_argument("--takeoff", default="")
    ap.add_argument("--stop_before", choices=["top", "bottom", "layers", "fabric", "qc", "cc5", "physics"])
    ap.add_argument("--only", choices=["top", "bottom", "layers", "fabric", "qc", "cc5", "physics"], help="run just this one step")
    a = ap.parse_args()
    if a.cmd == "decide": decide(a.story)
    elif a.cmd == "design": design(a.story, a.actor, a.run_dir)
    elif a.cmd == "make": make(a.story, a.actor, a.body, a.top_mesh, a.top_image, a.stop_before, a.takeoff, a.only, a.run_dir, a.top_final)
    else:
        for k, v in decide(a.story).items():
            if v["decision"] == "MAKE" and (not a.actor or a.actor == k):
                design(a.story, k); make(a.story, k, a.body, a.top_mesh, a.top_image, a.stop_before, a.takeoff)


if __name__ == "__main__":
    main()
