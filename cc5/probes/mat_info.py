# List material channels/textures of the named clothes of the loaded avatar.
import RLPy
A = BRIDGE_ARGS  # noqa: F821
av = RLPy.RScene.GetAvatars()[0]
out = []
for c in av.GetClothes():
    comp = c.GetMaterialComponent()
    for mesh in c.GetMeshNames():
        for mat in comp.GetMaterialNames(mesh):
            ch = []
            for name in ("Diffuse", "Opacity", "Glow", "Specular", "Normal"):
                e = getattr(RLPy, "EMaterialTextureChannel_" + name, None)
                if e is not None:
                    try:
                        ch.append("%s=%s" % (name, comp.GetImageFilePath(mesh, mat, e)))
                    except Exception as ex:
                        ch.append("%s=?%s" % (name, str(ex)[:40]))
            out.append("%s/%s/%s shader=%s %s" % (c.GetName(), mesh, mat, comp.GetShader(mesh, mat) if hasattr(comp, "GetShader") else "", " ".join(ch)))
BRIDGE_RESULT = "\n".join(out)
