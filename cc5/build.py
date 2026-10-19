# CC5 > Script > Load Python: builds every job listed in cc5_jobs\batch.txt (made by tools\plan.py / tools\redress.py).
# Per job: head (Headshot from face.png, or load_project = same head) -> strip -> body sliders ("morphs") ->
# hair/clothes/shoes + fabric -> dye hair -> skin texture ("skin_arm") -> shirt fix ("layer": in/out) or
# collision on the top garment -> render <name>.png -> save <name>.ccProject. Log: <job>\result.txt
# A job is skipped once it has result.txt (delete it to rebuild). Export the .iAvatar by hand afterwards.
import importlib, json, os, sys, time, traceback
import RLPy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit
import layer_fix
importlib.reload(kit)
importlib.reload(layer_fix)
BODY = {"male": "Male", "female": "Female", "neutral": "Neutral", "child": "Kid", "baby": "Baby"}  # CC5 enum has Kid, not Child


def build(here):
    job = json.load(open(os.path.join(here, "job.json"), encoding="utf-8-sig"))
    name, log = job["name"], []

    def step(label, fn):
        with open(os.path.join(here, 'progress.txt'), 'a', encoding='utf-8') as progress:
            progress.write('START ' + label + '\n')
        t = time.time()
        try:
            r = fn()
            log.append("OK   %s (%.1fs) %s" % (label, time.time() - t, "" if r is None else r))
        except Exception:
            log.append("FAIL %s\n%s" % (label, traceback.format_exc()))

    def headshot():
        import RLPy2  # Load Headshot only when needed; existing-project re-dress skips the AI module.
        skin = RLPy2.RArrayListWString(3, "None"); skin[0] = "Soft Skin"
        mask = RLPy2.RArrayListWString(4, "None"); mask[0] = "No Mask"
        body = getattr(RLPy2.EHSBodyType, BODY.get(job.get("body"), "Neutral"), RLPy2.EHSBodyType.Neutral)
        return RLPy2.Headshot3.GetInterface().CenerateCharacter(
            os.path.join(here, job["face"]), body, False, RLPy2.RArrayListWString(), skin, mask)

    if job.get("load_project"):  # re-dress a finished character: same head, new clothes
        step("load project", lambda: RLPy.RFileIO.LoadFile(os.path.join(here, job.get("project_source", name + ".ccProject"))))
    elif not job.get("skip_headshot"):
        step("headshot", headshot)
    av = RLPy.RScene.GetAvatars()[0]

    def strip():
        keep_hair = job.get("load_project") and not job.get("new_hair")  # new_hair: swap it; re-dress keeps the project's hair (some hairs load ~6 min)
        for o in list(av.GetClothes()) + ([] if keep_hair else list(av.GetHairs())) + list(av.GetAccessories()):
            RLPy.RScene.RemoveObject(o)

    step("strip", strip)

    def morphs():  # job "morphs": {slider id: weight 0..1}, before clothes so they fit the new body
        sh = av.GetAvatarShapingComponent()
        done = []
        for mid, w in job.get("morphs", {}).items():
            sh.SetShapingMorphWeight(mid, float(w))
            done.append("%s=%.2f" % (mid[-25:], sh.GetShapingMorphWeight(mid)))
        av.Update()
        return " ".join(done)

    if job.get("morphs"):
        step("morphs", morphs)
    for item in job["items"]:
        if job.get("load_project") and not job.get("new_hair") and item.lower().endswith((".rlhair", ".cchair", ".ihair")):
            continue  # the loaded project already has its hair
        def load(item=item):
            before = set(o.GetName() for o in av.GetClothes())
            RLPy.RScene.SelectObject(av)
            RLPy.RFileIO.LoadFile(os.path.join(here, item))
            new = [o.GetName() for o in av.GetClothes() if o.GetName() not in before]
            if new and item.lower().endswith((".cccloth", ".icloth")):  # last cloth item = upper (lower first, upper second)
                open(os.path.join(here, "upper.txt"), "w", encoding="utf-8").write("\n".join(new))
            fab = job.get("fabrics", {}).get(item)
            if not fab:
                return None
            for cl in av.GetClothes():
                if cl.GetName() in before:
                    continue
                comp = cl.GetMaterialComponent()
                for mesh in cl.GetMeshNames():
                    for mat in comp.GetMaterialNames(mesh):
                        comp.LoadImageToTexture(mesh, mat, RLPy.EMaterialTextureChannel_Diffuse, fab)
                        comp.AddDiffuseKey(RLPy.RKey(), mesh, mat, RLPy.RRgb(1, 1, 1))
                cl.Update()
            return "fabric"
        step("load " + item, load)

    c01 = tuple(v / 255.0 for v in job.get("hair_rgb", [18, 16, 15]))

    def dye():
        for hair in av.GetHairs():
            comp = hair.GetMaterialComponent()
            for mesh in hair.GetMeshNames():
                for mat in comp.GetMaterialNames(mesh):
                    comp.AddDiffuseKey(RLPy.RKey(), mesh, mat, RLPy.RRgb(*c01))
                    for p in comp.GetShaderParameterNames(mesh, mat):
                        if p in ("RootColor", "TipColor", "_1st Dye Color", "_2nd Dye Color"):
                            comp.SetShaderParameter(mesh, mat, p, c01)
                        elif p in ("_1st Dye Strength", "_2nd Dye Strength"):
                            comp.SetShaderParameter(mesh, mat, p, (0.0,))
                    # gray/white: the brown base map + vertex color would win over Root/Tip, so switch them off
                    gray = max(job.get("hair_rgb", [0])) > 60
                    names = comp.GetShaderParameterNames(mesh, mat)
                    for p, v in (("ActiveChangeHairColor", (1.0,) if gray else (0.0,)),
                                 ("BaseColorMapStrength", (0.0,) if gray else None),
                                 ("VertexColorStrength", (0.0,) if gray else None),
                                 ("VertexGrayToColor", c01 if gray else None)):
                        if v is not None and p in names:
                            comp.SetShaderParameter(mesh, mat, p, v)
            hair.Update()

    step("dye hair", dye)

    if job.get("skin_arm"):  # e.g. burn scar painted by tools\paint_burn_scar.py (same head -> same arm UVs)
        tex = job["skin_arm"] if os.path.isabs(job["skin_arm"]) else os.path.join(kit.REPO, "data", job["skin_arm"])
        step("skin arm", lambda: av.GetMaterialComponent().LoadImageToTexture(
            "CC_Base_Body", "Std_Skin_Arm", RLPy.EMaterialTextureChannel_Diffuse, tex))
    if job.get("layer") in ("in", "out"):
        step("layer " + job["layer"], lambda: layer_fix.fix(av, here, job["layer"], log))

    def collision():  # Conform > Calculate Collision on the top garment (settings that fixed clipping by hand)
        names = open(os.path.join(here, "upper.txt"), encoding="utf-8").read().splitlines()
        for cl in av.GetClothes():
            if cl.GetName() in names:
                for k, v in (("Iteration", 3.0), ("Margin", 0.3), ("IncreaseSize", 0.2)):
                    cl.SetClothConformValue(k, v)
                cl.CalculateCollision()
                return cl.GetName()

    if os.path.exists(os.path.join(here, "upper.txt")) and not job.get("layer"):
        step("collision", collision)
    log.append("wearing: %r" % ([o.GetName() for o in list(av.GetClothes()) + list(av.GetHairs())],))

    def frame():
        RLPy.RScene.SelectObject(av)
        RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)

    step("camera front", frame)
    if job.get("side_render"):
        def side():
            RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Left)
            RLPy.RGlobal.RenderImage(os.path.join(here, name + "_side.png"))
            RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
        step("side render", side)
    step("render", lambda: RLPy.RGlobal.RenderImage(os.path.join(here, name + ".png")))

    def save():
        s = RLPy.RSaveFileSetting(); s.SetSaveType(RLPy.ESaveFileType_Character)
        return RLPy.RFileIO.SaveFile(av, s, os.path.join(here, name + ".ccProject"))

    step("save", save)
    open(os.path.join(here, "result.txt"), "w", encoding="utf-8").write("\n".join(log))


for d in open(kit.BATCH, encoding="utf-8").read().splitlines():
    d = d.strip()
    if not d:
        continue
    name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8-sig"))["name"]
    if os.path.exists(os.path.join(d, "result.txt")):  # delete result.txt to (re)build a job
        continue
    try:
        build(d)
    except Exception as e:
        open(os.path.join(d, "result.txt"), "a", encoding="utf-8").write("\nBATCH FAIL %r" % e)
open(os.path.join(kit.JOBS, "batch_done.txt"), "w", encoding="utf-8").write(time.strftime("%Y-%m-%d %H:%M:%S"))
