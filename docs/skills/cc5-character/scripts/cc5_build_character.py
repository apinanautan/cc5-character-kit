# Run inside Character Creator 5 (Script > Load Python). Reads job.json next to
# this file and builds one character end to end:
#   AI face -> Headshot 3 head -> strip default clothes/hair -> put on chosen
#   hair/clothes/shoes -> dye hair (black/gray only) -> full-body front render
#   -> save .ccProject + .png into the story folder.  Writes result.txt.
import json, os, time, traceback
import RLPy
import RLPy2

HERE = os.path.dirname(os.path.abspath(__file__))
log = []


def _write():
    with open(os.path.join(HERE, "result.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(log))


try:
    job = json.load(open(os.path.join(HERE, "job.json"), encoding="utf-8"))
except Exception:
    log.append("FAIL job.json\n" + traceback.format_exc()); _write(); raise


def step(name, fn):
    t = time.time()
    try:
        r = fn()
        log.append("OK   %s (%.1fs) %s" % (name, time.time() - t, "" if r is None else r))
        return r
    except Exception:
        log.append("FAIL %s\n%s" % (name, traceback.format_exc()))
        return None


def body_type():
    name = {"male": "Male", "female": "Female", "neutral": "Neutral"}.get(job.get("body", "male"), "Neutral")
    return getattr(RLPy2.EHSBodyType, name, RLPy2.EHSBodyType.Neutral)


def headshot():
    skin = RLPy2.RArrayListWString(3, "None"); skin[0] = "Soft Skin"
    mask = RLPy2.RArrayListWString(4, "None"); mask[0] = "No Mask"
    return RLPy2.Headshot3.GetInterface().CenerateCharacter(
        os.path.join(HERE, job["face"]), body_type(), False, RLPy2.RArrayListWString(), skin, mask)


if not job.get("skip_headshot"):
    step("headshot", headshot)
avatar = RLPy.RScene.GetAvatars()[0]


def strip():
    gone = []
    for obj in list(avatar.GetClothes()) + list(avatar.GetHairs()) + list(avatar.GetAccessories()):
        gone.append(obj.GetName())
        RLPy.RScene.RemoveObject(obj)
    return gone


step("strip defaults", strip)
for item in job["items"]:
    def load(item=item):
        RLPy.RScene.SelectObject(avatar)
        return RLPy.RFileIO.LoadFile(os.path.join(HERE, item))
    step("load " + item, load)

rgb = job.get("hair_rgb", [18, 16, 15])


def dye_hair():
    color = RLPy.RRgb(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)
    out = []
    for hair in avatar.GetHairs():
        comp = hair.GetMaterialComponent()
        for mesh in hair.GetMeshNames():
            for mat in comp.GetMaterialNames(mesh):
                comp.AddDiffuseKey(RLPy.RKey(), mesh, mat, color)
                for p in comp.GetShaderParameterNames(mesh, mat):
                    if p in ("RootColor", "TipColor"):
                        comp.SetShaderParameter(mesh, mat, p, [float(c) for c in rgb])
                out.append(mesh)
    return out


step("dye hair", dye_hair)
log.append("wearing: %r" % ([o.GetName() for o in list(avatar.GetClothes()) + list(avatar.GetHairs())],))


def frame():
    RLPy.RScene.SelectObject(avatar)
    RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)


step("camera front", frame)
out_dir, name = HERE, job["name"]  # check files stay in the job folder; only the .iAvatar goes to the story folder
step("render", lambda: RLPy.RGlobal.RenderImage(os.path.join(out_dir, name + ".png")))


def save():
    setting = RLPy.RSaveFileSetting()
    setting.SetSaveType(RLPy.ESaveFileType_Character)
    return RLPy.RFileIO.SaveFile(avatar, setting, os.path.join(out_dir, name + ".ccProject"))


step("save", save)
with open(os.path.join(HERE, "result.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(log))
