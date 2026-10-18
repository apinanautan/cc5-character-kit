# Run inside iClone 8: list every prop/building/avatar/camera/light with world position + bounding box
# -> snapgen_data\ic8_jobs\survey.txt  (so placement can be planned from text, not by looking)
import os
import RLPy

out = []


def row(kind, o):
    try:
        t = o.WorldTransform().T()
        mx, c, mn = RLPy.RVector3(), RLPy.RVector3(), RLPy.RVector3()
        o.GetBounds(mx, c, mn)
        out.append("%s\t%s\tpos %.0f %.0f %.0f\tmin %.0f %.0f %.0f\tmax %.0f %.0f %.0f" % (
            kind, o.GetName(), t.x, t.y, t.z, mn.x, mn.y, mn.z, mx.x, mx.y, mx.z))
    except Exception as e:
        out.append("%s\t%s\t! %s" % (kind, o.GetName(), e))


for kind, lst in (("prop", RLPy.RScene.GetProps()), ("building", RLPy.RScene.GetBuildings()),
                  ("avatar", RLPy.RScene.GetAvatars()), ("camera", RLPy.RScene.GetCameras()),
                  ("light", RLPy.RScene.FindObjects(RLPy.EObjectType_Light))):
    for o in lst:
        row(kind, o)
    for o in lst if kind == "prop" else []:
        for ch in RLPy.RScene.FindChildObjects(o, RLPy.EObjectType_Prop):
            row("  child", ch)

open(os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "ic8_jobs", "survey.txt"), "w",
     encoding="utf-8").write("\n".join(out))
RLPy.RUi.ShowMessageBox("ic8_survey", "%d objects listed" % len(out), RLPy.EMsgButton_Ok)
