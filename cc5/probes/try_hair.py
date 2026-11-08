# Try a hair file on a job's character and render front/left/back views (nothing saved).
#   tools\cc5.py run cc5\probes\try_hair.py job=<dir> hair=<rlHair> out=<dir>
import json, os
import RLPy
A = BRIDGE_ARGS  # noqa: F821
d = A["job"]
name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8-sig"))["name"]
RLPy.RFileIO.LoadFile(os.path.join(d, name + ".ccProject"))
av = RLPy.RScene.GetAvatars()[0]
for h in list(av.GetHairs()):
    RLPy.RScene.RemoveObject(h)
RLPy.RScene.SelectObject(av)
RLPy.RFileIO.LoadFile(A["hair"])
c = RLPy.RRgb(18 / 255.0, 16 / 255.0, 15 / 255.0)
for h in av.GetHairs():
    comp = h.GetMaterialComponent()
    for mesh in h.GetMeshNames():
        for mat in comp.GetMaterialNames(mesh):
            comp.AddDiffuseKey(RLPy.RKey(), mesh, mat, c)
            for p in comp.GetShaderParameterNames(mesh, mat):
                if p in ("RootColor", "TipColor", "_1st Dye Color", "_2nd Dye Color"):
                    comp.SetShaderParameter(mesh, mat, p, (18 / 255.0, 16 / 255.0, 15 / 255.0))
    h.Update()
out = []
for tag, loc in (("front", RLPy.ECameraLocationType_Front), ("left", RLPy.ECameraLocationType_Left),
                 ("back", RLPy.ECameraLocationType_Back)):
    RLPy.RScene.SelectObject(av)
    RLPy.RScene.GetCurrentCamera().SetCameraLocation(loc)
    p = os.path.join(A["out"], "cc5_%s.png" % tag)
    RLPy.RGlobal.RenderImage(p)
    out.append(p)
BRIDGE_RESULT = "hairs=%s\n%s" % ([h.GetName() for h in av.GetHairs()], "\n".join(out))
