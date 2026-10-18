# Run inside iClone 8: timing check -> ic8_jobs\probe.txt
# fps, end time, camera transform key times, each avatar's clip start/length (all in ms as RLPy reports them)
import os
import RLPy
out = ["fps %s end %s" % (RLPy.RGlobal.GetFps().ToFloat(), RLPy.RGlobal.GetEndTime().ToFloat())]
for cam in RLPy.RScene.GetCameras():
    c = cam.GetControl("Transform")
    ts = []
    for i in range(c.GetKeyCount()):
        t = RLPy.RTime()
        c.GetKeyTimeAt(i, t)
        ts.append("%.0f" % t.ToFloat())
    out.append("camera %s keys: %s" % (cam.GetName(), " ".join(ts)))
for a in RLPy.RScene.GetAvatars():
    sk = a.GetSkeletonComponent()
    for i in range(sk.GetClipCount()):
        cl = sk.GetClip(i)
        out.append("%s clip%d start %.0f len %.0f speed %.2f" % (
            a.GetName(), i, cl.ClipTimeToSceneTime(RLPy.RTime.FromValue(0)).ToFloat(),
            cl.GetClipLength().ToFloat(), cl.GetSpeed()))
open(os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "ic8_jobs", "probe.txt"), "w",
     encoding="utf-8").write("\n".join(out))
