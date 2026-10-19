# Bridge: paint an old burn scar onto this character's own skin (arm / face / leg) and save.
#   python tools\cc5.py run cc5\scar.py job=<job> where=arm|face|leg
# The body is exported as OBJ with textures to get this character's own skin colour map, the scar is painted on it
# (tools\paint_burn_scar.py look), and the painted map is loaded back. Experimental for face/leg (scar position guessed).
import glob, json, os, subprocess, sys
import RLPy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

A = BRIDGE_ARGS  # noqa: F821
d = os.path.join(kit.JOBS, A["job"])
where = A.get("where", "arm")
MAT = {"arm": "Std_Skin_Arm", "face": "Std_Skin_Head", "leg": "Std_Skin_Leg"}[where]
# scar centre/size on a 2048 map: arm = forearm (proven on krong_somjit_70), face = left cheek, leg = shin (guesses)
SPOT = {"arm": (600, 1130, 230, 300), "face": (560, 1150, 150, 120), "leg": (560, 1300, 200, 260)}[where]
name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8-sig"))["name"]
proj = os.path.join(d, name + ".ccProject")
RLPy.RFileIO.LoadFile(proj)
av = RLPy.RScene.GetAvatars()[0]
log = []

work = os.path.join(d, "scar")
os.makedirs(work, exist_ok=True)
opt = RLPy.EExport3DFileOption__None
for n in dir(RLPy):  # export with textures (option name differs between versions)
    if n.startswith("EExport3DFileOption_") and ("Texture" in n or "Material" in n):
        opt |= getattr(RLPy, n)
        log.append("option " + n)
RLPy.RFileIO.ExportObjFile(av, os.path.join(work, "body.obj"), opt)
hits = [p for p in glob.glob(os.path.join(work, "**", "*"), recursive=True)
        if MAT.lower() in os.path.basename(p).lower() and any(k in os.path.basename(p).lower() for k in ("diffuse", "basecolor", "base_color"))
        and p.lower().endswith((".png", ".jpg", ".jpeg", ".tga", ".bmp"))]
if not hits:
    BRIDGE_RESULT = "\n".join(log + ["NO SKIN MAP for %s in %s" % (MAT, work)])
    raise SystemExit
src = hits[0]
dst = os.path.join(d, "skin_%s_scar.png" % where)
for exe in ("py", "python"):
    r = subprocess.run([exe, os.path.join(kit.REPO, "tools", "paint_burn_scar.py"), src, dst] + [str(v) for v in SPOT],
                       capture_output=True, text=True, creationflags=0x08000000)
    if r.returncode == 0:
        break
log.append("paint: " + (r.stdout + r.stderr).strip()[-200:])
av.GetMaterialComponent().LoadImageToTexture("CC_Base_Body", MAT, RLPy.EMaterialTextureChannel_Diffuse, dst)
av.Update()
RLPy.RScene.SelectObject(av)
RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
RLPy.RGlobal.RenderImage(os.path.join(d, name + ".png"))
s = RLPy.RSaveFileSetting(); s.SetSaveType(RLPy.ESaveFileType_Character)
RLPy.RFileIO.SaveFile(av, s, proj)
log.append("OK scar on " + MAT)
BRIDGE_RESULT = "\n".join(log)
