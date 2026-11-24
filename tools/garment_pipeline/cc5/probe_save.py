# sanity: can SaveFile write a .ccCloth at all? save the existing pants (type Lower) to a NEW test file
import os, RLPy
out = BRIDGE_ARGS["out"]; os.makedirs(out, exist_ok=True)
r = ["Upper=%d Lower=%d Unknown=%d Acc=%d" % (RLPy.EClotheType_Upper, RLPy.EClotheType_Lower, RLPy.EClotheType_Unknown, RLPy.EClotheType_Accessory)]
c = [x for x in RLPy.RScene.GetAvatars()[0].GetClothes() if x.GetClotheType() == RLPy.EClotheType_Lower][0]
s = RLPy.RSaveFileSetting(); s.SetSaveType(RLPy.ESaveFileType_Lower)
p = os.path.join(out, "test_pants.ccCloth")
st = RLPy.RFileIO.SaveFile(c, s, p)
r.append("pants save status=%s exists=%s" % (st.IsSuccess() if hasattr(st, "IsSuccess") else st, os.path.exists(p)))
BRIDGE_RESULT = "\n".join(r)
