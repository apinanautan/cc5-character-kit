# One character standing in a scene for the whole audio length. Driven by ic8_jobs\solo.json:
# {"avatar": path, "pos":[x,y,yaw], "motion": path, "length": sec, "hide":[names], "cam":[x,y,z], "target":[x,y,z],
#  "focal":50, "mode":"still"|"setup"|"video", "out": path}
# Re-runnable: reuses the avatar if already loaded (by file name). Log: ic8_jobs\solo_log.txt
import json, math, os, traceback
import RLPy

J = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "ic8_jobs")
log = []
TICK = 6000.0


def T(sec):
    return RLPy.RTime.FromValue(int(round(sec * TICK)))


def zq(deg):
    h = math.radians(deg) / 2
    return (0.0, 0.0, math.sin(h), math.cos(h))


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz)


def key(obj, sec, pos, q):
    c = obj.GetControl("Transform")
    t = RLPy.RTransform()
    c.GetValue(T(sec), t)
    t.T().x, t.T().y, t.T().z = pos
    t.R().x, t.R().y, t.R().z, t.R().w = q
    c.SetValue(T(sec), t)


try:
    job = json.load(open(os.path.join(J, "solo.json"), encoding="utf-8"))
    L = job["length"]
    for a in RLPy.RScene.GetAvatars():
        if a.GetName() in job.get("hide", []):
            RLPy.RScene.Hide(a)
    want = os.path.splitext(os.path.basename(job["avatar"]))[0]
    av = next((a for a in RLPy.RScene.GetAvatars() if a.GetName() == want), None)
    if not av:
        before = set(a.GetID() for a in RLPy.RScene.GetAvatars())
        RLPy.RScene.ClearSelectObjects()
        RLPy.RFileIO.LoadFile(job["avatar"])
        av = [a for a in RLPy.RScene.GetAvatars() if a.GetID() not in before][0]
        av.SetName(want)
        log.append("loaded " + want)
    RLPy.RGlobal.RemoveAllAnimations(av)
    x, y, yaw = job["pos"]
    key(av, 0, (x, y, job.get("z", 0)), zq(yaw))

    # ONE motion clip, slowed so it ends exactly when the audio ends (user's rule: stretch, don't loop)
    skel = av.GetSkeletonComponent()
    RLPy.RFileIO.LoadMotion(job["motion"], T(0), av)
    clip = skel.GetClip(skel.GetClipCount() - 1)
    d = clip.GetClipLength().ToFloat() / TICK
    clip.SetSpeed(d / L)
    log.append("motion %.2fs -> speed %.3f -> %.2fs (audio %.2f)" % (d, d / L, clip.GetClipLength().ToFloat() / TICK, L))

    # narration audio on a hidden avatar so nobody lip-syncs it
    host = next((a for a in RLPy.RScene.GetAvatars() if a.GetName() == job.get("audio_host")), None)
    if host and job.get("audio"):
        RLPy.RAudio.LoadAudioToObject(host, job["audio"], T(0))
        log.append("audio on " + host.GetName())

    cam = RLPy.RScene.GetCameras()[0]
    RLPy.RScene.SetCurrentCamera(cam)
    RLPy.RGlobal.RemoveAllAnimations(cam)
    c, tg = job["cam"], job["target"]
    dx, dy, dz = tg[0] - c[0], tg[1] - c[1], tg[2] - c[2]
    yawc = math.degrees(math.atan2(-dx, dy))
    pitch = math.degrees(math.atan2(dz, math.hypot(dx, dy)))
    qf = (math.sin(math.radians(45)), 0.0, 0.0, math.cos(math.radians(45)))  # camera base Rx(+90)
    qp = (math.sin(math.radians(pitch) / 2), 0.0, 0.0, math.cos(math.radians(pitch) / 2))
    q = qmul(zq(yawc), qmul(qp, qf))
    cam.SetFocalLength(T(0), job.get("focal", 50))
    key(cam, 0, c, q)
    key(cam, L, c, q)

    RLPy.RGlobal.SetEndTime(T(L))
    RLPy.RGlobal.SetTime(T(0))
    RLPy.RScene.ClearSelectObjects()
    mode = job.get("mode", "still")
    if mode == "still":
        for s in (1.0, L / 2):
            RLPy.RGlobal.SetTime(T(s))
            RLPy.RGlobal.RenderImage(os.path.join(J, "solo_%02d.png" % int(s)))
        log.append("stills done")
    elif mode == "video":
        RLPy.RGlobal.RenderVideo(job["out"])
        log.append("video done " + job["out"])
except Exception:
    log.append(traceback.format_exc())
open(os.path.join(J, "solo_log.txt"), "w", encoding="utf-8").write("\n".join(log))
