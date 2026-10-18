# Run inside CC5 ONCE: for each entry in cc5_jobs\redress_luek.json -> open project, remove old clothes
# (keep hair), load new items, put fabric textures on them, render <name>_v2.png, save project.
import json, os, traceback
import RLPy
J = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "cc5_jobs")
log = []
for job in json.load(open(os.path.join(J, "redress_luek.json"), encoding="utf-8")):
    if os.path.exists(job["render"]):
        continue
    try:
        RLPy.RFileIO.LoadFile(job["project"])
        av = RLPy.RScene.GetAvatars()[0]
        for o in list(av.GetClothes()) + list(av.GetAccessories()):
            RLPy.RScene.RemoveObject(o)
        for it in job["items"]:
            before = set(o.GetName() for o in av.GetClothes())
            RLPy.RScene.SelectObject(av)
            RLPy.RFileIO.LoadFile(it["path"])
            if not it["fabric"]:
                continue
            for cl in av.GetClothes():
                if cl.GetName() in before:
                    continue
                comp = cl.GetMaterialComponent()
                for mesh in cl.GetMeshNames():
                    for mat in comp.GetMaterialNames(mesh):
                        comp.LoadImageToTexture(mesh, mat, RLPy.EMaterialTextureChannel_Diffuse, it["fabric"])
                        comp.AddDiffuseKey(RLPy.RKey(), mesh, mat, RLPy.RRgb(1, 1, 1))
                cl.Update()
        RLPy.RScene.SelectObject(av)
        RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
        RLPy.RGlobal.RenderImage(job["render"])
        s = RLPy.RSaveFileSetting(); s.SetSaveType(RLPy.ESaveFileType_Character)
        RLPy.RFileIO.SaveFile(av, s, job["project"])
        log.append("OK " + job["dir"])
    except Exception:
        log.append("FAIL %s\n%s" % (job["dir"], traceback.format_exc()[-300:]))
    open(os.path.join(J, "redress_log.txt"), "w", encoding="utf-8").write("\n".join(log))
