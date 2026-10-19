import RLPy
av = RLPy.RScene.GetAvatars()[0]
comp = av.GetMaterialComponent()
out = [m for m in dir(comp) if "tex" in m.lower() or "image" in m.lower() or "export" in m.lower()]
for f in ("GetImageTexture", "GetTextureFilePath", "GetTexturePath", "ExportTexture", "ExportTextures"):
    if hasattr(comp, f):
        try:
            out.append("%s -> %r" % (f, getattr(comp, f)("CC_Base_Body", "Std_Skin_Arm", RLPy.EMaterialTextureChannel_Diffuse)))
        except Exception as e:
            out.append("%s ERR %s" % (f, e))
BRIDGE_RESULT = "\n".join(out)
