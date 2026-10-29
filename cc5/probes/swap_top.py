# Replace the named top of the loaded job with library cloth files (one render each): try kid tops on a kid.
#   tools\cc5.py run cc5\probes\swap_top.py job=<dir> remove=<cloth name> "tops=a.ccCloth;b.ccCloth" fabric=<png> out=<dir>
import json, os
import RLPy
A = BRIDGE_ARGS  # noqa: F821
av = RLPy.RScene.GetAvatars()[0]
for c in list(av.GetClothes()):
    if c.GetName() == A["remove"]:
        RLPy.RScene.RemoveObject(c)
os.makedirs(A["out"], exist_ok=True)
log = []
for n, top in enumerate(A["tops"].split(";")):
    before = set(c.GetName() for c in av.GetClothes())
    RLPy.RScene.SelectObject(av)
    RLPy.RFileIO.LoadFile(top)
    new = [c for c in av.GetClothes() if c.GetName() not in before]
    for c in new:
        comp = c.GetMaterialComponent()
        for mesh in c.GetMeshNames():
            for mat in comp.GetMaterialNames(mesh):
                comp.LoadImageToTexture(mesh, mat, RLPy.EMaterialTextureChannel_Diffuse, A["fabric"])
                comp.AddGlossinessKey(RLPy.RKey(), mesh, mat, 0.0)
        c.Update()
    RLPy.RScene.SelectObject(av)
    RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
    for _ in range(2):
        RLPy.RGlobal.RenderImage(os.path.join(A["out"], "%02d.png" % (n + 1)))
    log.append("%02d %s %s" % (n + 1, os.path.basename(top), [c.GetName() for c in av.GetClothes()]))
    for c in new:
        RLPy.RScene.RemoveObject(c)
BRIDGE_RESULT = "\n".join(log)
