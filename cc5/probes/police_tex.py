# python tools/cc5.py run cc5/probes/police_tex.py out=<folder>   (current avatar) -> diffuse/normal PNGs + material names
import os
import RLPy
A = BRIDGE_ARGS  # noqa: F821
av = RLPy.RScene.GetAvatars()[0]
os.makedirs(A["out"], exist_ok=True)
log = []
for i, c in enumerate(av.GetClothes()):
    comp = c.GetMaterialComponent()
    for mesh in c.GetMeshNames():
        for mat in comp.GetMaterialNames(mesh):
            for ch, tag in ((RLPy.EMaterialTextureChannel_Diffuse, "diff"), (RLPy.EMaterialTextureChannel_Normal, "norm"), (RLPy.EMaterialTextureChannel_Opacity, "opac")):
                try:
                    img = comp.GetImage(mesh, mat, ch)
                    p = os.path.join(A["out"], "c%d_%s_%s_%s.png" % (i, mesh, mat, tag))
                    r = img.SaveFile(p)
                    log.append("%s/%s/%s %s %s" % (c.GetName(), mesh, mat, tag, os.path.exists(p)))
                except Exception as e:
                    log.append("%s/%s/%s %s none" % (c.GetName(), mesh, mat, tag))
BRIDGE_RESULT = "\n".join(log)
