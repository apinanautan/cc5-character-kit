# Put a diffuse texture on named clothes of the loaded avatar and render it (tools\cc5.py run ... names=a;b tex=x.png out=y.png)
import RLPy
A = BRIDGE_ARGS  # noqa: F821
av = RLPy.RScene.GetAvatars()[0]
res = []
for c in av.GetClothes():
    if c.GetName() not in A["names"].split(";"):
        continue
    comp = c.GetMaterialComponent()
    for mesh in c.GetMeshNames():
        for mat in comp.GetMaterialNames(mesh):
            r = comp.LoadImageToTexture(mesh, mat, RLPy.EMaterialTextureChannel_Diffuse, A["tex"])
            comp.AddDiffuseKey(RLPy.RKey(), mesh, mat, RLPy.RRgb(1, 1, 1))
            comp.AddSpecularKey(RLPy.RKey(), mesh, mat, RLPy.RRgb(0.1, 0.1, 0.1)) if hasattr(comp, "AddSpecularKey") else None
            comp.AddGlossinessKey(RLPy.RKey(), mesh, mat, 0.0)
            comp.AddSelfIlluminationKey(RLPy.RKey(), mesh, mat, 0.0) if hasattr(comp, "AddSelfIlluminationKey") else None
            res.append("%s/%s load=%s" % (mesh, mat, r))
    c.Update()
RLPy.RScene.SelectObject(av)
RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
for _ in range(2):
    RLPy.RGlobal.RenderImage(A["out"])
BRIDGE_RESULT = "\n".join(res)
