import RLPy
out=[]
av = RLPy.RScene.GetAvatars()
out.append("avatars: %d" % len(av))
for a in av:
    out.append("avatar %s type=%s" % (a.GetName(), a.GetAvatarType()))
    for m in a.GetMeshNames() if hasattr(a,'GetMeshNames') else []:
        out.append("  mesh "+m)
    try:
        for c in a.GetAccessories(): out.append("  acc "+c.GetName())
    except Exception as e: out.append(str(e))
    try:
        for c in a.GetClothes(): out.append("  cloth "+c.GetName())
    except Exception as e: out.append("cl err "+str(e))
out.append("RLPy attrs: "+", ".join(x for x in dir(RLPy) if 'Cloth' in x or 'Import' in x or 'Export' in x or 'Fbx' in x.lower()))
BRIDGE_RESULT="\n".join(out)
