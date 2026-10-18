# Run inside iClone 8: move avatars already in the scene to world positions (no reload), hide others.
# Data: ic8_jobs\place.json {"place": {avatar name: [x, y, yaw]}, "hide": [names]}
# yaw: 0 = face -Y (front camera), 90 = face +X, 180 = face +Y
import json, math, os
import RLPy
J = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "ic8_jobs")
job = json.load(open(os.path.join(J, "place.json"), encoding="utf-8"))
log = []
for a in RLPy.RScene.GetAvatars():
    n = a.GetName()
    if n in job.get("hide", []):
        RLPy.RScene.Hide(a)
        log.append("hide " + n)
    elif n in job["place"]:
        x, y, yaw = job["place"][n]
        ctrl = a.GetControl("Transform")
        t = RLPy.RTransform()
        ctrl.GetValue(RLPy.RTime.FromValue(0), t)
        t.T().x, t.T().y, t.T().z = x, y, 0
        q = RLPy.RQuaternion()
        q.FromAxisAngle(RLPy.RVector3(0, 0, 1), math.radians(yaw))
        t.R().x, t.R().y, t.R().z, t.R().w = q.x, q.y, q.z, q.w
        ctrl.SetValue(RLPy.RTime.FromValue(0), t)
        log.append("move %s -> %d %d yaw %d" % (n, x, y, yaw))
    else:
        log.append("skip " + n)
cam = RLPy.RScene.GetCurrentCamera()
RLPy.RScene.SelectObject(RLPy.RScene.FindObject(RLPy.EObjectType_Avatar, "วีนา วัยสาว"))
cam.SetCameraLocation(RLPy.ECameraLocationType_Front)
RLPy.RGlobal.RenderImage(os.path.join(J, "place_check.png"))
open(os.path.join(J, "place_log.txt"), "w", encoding="utf-8").write("\n".join(log))
