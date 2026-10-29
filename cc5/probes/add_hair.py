# Put the job's hair (job.json items *.rlHair) back on the loaded avatar, dyed with job hair_rgb, then save_job.
import json, os
import RLPy
A = BRIDGE_ARGS  # noqa: F821
d = A["job"]
job = json.load(open(os.path.join(d, "job.json"), encoding="utf-8-sig"))
av = RLPy.RScene.GetAvatars()[0]
hair = [i for i in job["items"] if i.lower().endswith((".rlhair", ".cchair"))]
if hair and not av.GetHairs():
    RLPy.RScene.SelectObject(av)
    RLPy.RFileIO.LoadFile(os.path.join(d, hair[0]))
c01 = tuple(v / 255.0 for v in job.get("hair_rgb", [18, 16, 15]))
for h in av.GetHairs():
    comp = h.GetMaterialComponent()
    for mesh in h.GetMeshNames():
        for mat in comp.GetMaterialNames(mesh):
            comp.AddDiffuseKey(RLPy.RKey(), mesh, mat, RLPy.RRgb(*c01))
            for p in comp.GetShaderParameterNames(mesh, mat):
                if p in ("RootColor", "TipColor", "_1st Dye Color", "_2nd Dye Color"):
                    comp.SetShaderParameter(mesh, mat, p, c01)
    h.Update()
BRIDGE_RESULT = "hairs=%s" % [h.GetName() for h in av.GetHairs()]
