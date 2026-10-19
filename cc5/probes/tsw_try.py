import RLPy
av = RLPy.RScene.GetAvatars()[0]
out = []
c = [c for c in av.GetClothes() if "collar" in c.GetName().lower()][0]
for t in ["", "Default", "Clothes", "Cloth", "Tight Fit", "Loose Fit", "Upper", "Upper Body", "Full Body", "Long Sleeve", "Skirt", "Gloves", "Shoes", "Hair", "Pants", "default", "Dress"]:
    try:
        r = c.TransferSkinWeight(t); out.append("%r -> %s" % (t, r.IsError() if hasattr(r, "IsError") else r))
    except Exception as e:
        out.append("%r ERR %s" % (t, e))
BRIDGE_RESULT = "\n".join(out)
