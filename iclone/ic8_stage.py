# Run inside iClone 8 on a scene whose characters are already loaded (ic8_key_shot.py) + one camera.
# Reads ic8_jobs\stage.json, then: narration audio on a hidden avatar (no visible lip sync),
# wipes old animation, places actors, lays their motions (each repeats until the next one starts),
# keys the camera per shot with a hard cut (position + look-at target, computed here),
# and either renders one still per shot (mode "stills" -> stage_shotN.png) or the final video (mode "video").
# Log: ic8_jobs\stage_log.txt
import json, math, os, traceback
import RLPy

J = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "ic8_jobs")
log = []


TICK = 6000.0  # iClone RTime unit: 1/6000 second (NOT ms)


def ms(sec):
    return RLPy.RTime.FromValue(int(round(sec * TICK)))  # RTime = 1/6000 s ticks, int only


def qmul(a, b):  # (x, y, z, w)
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz)


def zq(deg):
    h = math.radians(deg) / 2
    return (0.0, 0.0, math.sin(h), math.cos(h))


def set_key(obj, sec, pos, quat):
    ctrl = obj.GetControl("Transform")
    t = RLPy.RTransform()
    ctrl.GetValue(ms(sec), t)
    t.T().x, t.T().y, t.T().z = pos
    t.R().x, t.R().y, t.R().z, t.R().w = quat
    ctrl.SetValue(ms(sec), t)


def lay_motions(av, motions, root, length):
    skel = av.GetSkeletonComponent()
    for i, (start, rel) in enumerate(motions):
        end = motions[i + 1][0] if i + 1 < len(motions) else length
        cur = float(start)
        while cur < end - 0.2:
            RLPy.RFileIO.LoadMotion(os.path.join(root, rel), ms(cur), av)
            clip = skel.GetClip(skel.GetClipCount() - 1)
            spd = 1.0 if "Walk" in rel else max(0.4, SPEED)  # slow the acting (user: never below 40%)
            clip.SetSpeed(spd)
            dur = clip.GetClipLength().ToFloat() / TICK  # scene seconds, after speed
            if dur <= 0:
                log.append("  ! zero length " + rel)
                break
            if cur + dur > end:
                clip.SetLength(ms((end - cur) * spd))  # SetLength is in clip time: scale back by speed
                dur = clip.GetClipLength().ToFloat() / TICK
                if abs(cur + dur - end) > 0.05:
                    log.append("  ! trim off: ends %.2f want %.2f" % (cur + dur, end))
            log.append("  %.1f-%.1f %s" % (cur, min(cur + dur, end), os.path.basename(rel)))
            cur += dur


try:
    job = json.load(open(os.path.join(J, "stage.json"), encoding="utf-8"))
    L = job["length"]
    SPEED = job.get("speed", 1.0)
    avatars = {a.GetName(): a for a in RLPy.RScene.GetAvatars()}
    cam = RLPy.RScene.GetCameras()[0]
    RLPy.RScene.SetCurrentCamera(cam)

    # camera looks down its local -Z with +Y up; rotate +90 deg about X so it looks along world +Y, Z up.
    # (Reading the Front view instead is unreliable: on a re-run it came back flipped 180 deg.)
    RLPy.RGlobal.RemoveAllAnimations(cam)
    q_front = (math.sin(math.radians(45)), 0.0, 0.0, math.cos(math.radians(45)))

    for name in job.get("hide", []):
        if name in avatars:
            RLPy.RScene.Hide(avatars[name])
    for name, a in job["actors"].items():
        av = avatars.get(name)
        if not av:
            log.append("! missing actor " + name)
            continue
        RLPy.RGlobal.RemoveAllAnimations(av)
        x, y, yaw = a["pos"]
        set_key(av, 0, (x, y, 0), zq(yaw))
        for mt, mx, my, myaw in a.get("moves", []):  # extra position keys (walk paths)
            set_key(av, mt, (mx, my, 0), zq(myaw))
        log.append(name)
        lay_motions(av, a["motions"], job["motion_root"], L)

    host = avatars.get(job["audio_host"])
    if host and job.get("mode") in ("video", "setup"):  # setup = build everything, no render
        RLPy.RAudio.LoadAudioToObject(host, job["audio"], ms(0))
        log.append("audio on " + job["audio_host"])

    frame = 1.0 / RLPy.RGlobal.GetFps().ToFloat()
    shots = job["shots"]
    def look(cpos, target):
        dx, dy = target[0] - cpos[0], target[1] - cpos[1]
        dz = target[2] - cpos[2]
        yaw = math.degrees(math.atan2(-dx, dy))
        pitch = math.degrees(math.atan2(dz, math.hypot(dx, dy)))
        # pitch around the camera's own right axis (= world X before yaw), then yaw around world Z
        return qmul(zq(yaw), qmul((math.sin(math.radians(pitch) / 2), 0.0, 0.0, math.cos(math.radians(pitch) / 2)), q_front))

    # lens: job "focal" (mm). Camera positions in the json are framed for the default lens, so pull
    # each camera back along its view line by focal/default to keep the same subject size.
    f0 = 50.0  # json camera positions are framed for a 50mm lens (don't read the camera: a re-run leaves it at 100)
    focal = job.get("focal") or f0
    k = focal / f0
    cam.SetFocalLength(ms(0), focal)
    log.append("lens %.0fmm -> %.0fmm (x%.2f distance)" % (f0, focal, k))

    def back(c, t, kk):
        return [t[0] + (c[0] - t[0]) * kk, t[1] + (c[1] - t[1]) * kk, t[2] + (c[2] - t[2]) * kk]

    # shot = [start, cam, target] (static) or [start, cam, target, cam_end, target_end] (dolly/pan to end)
    # optional 6th item = this shot's own lens in mm
    for i, s in enumerate(shots):
        start, target = s[0], s[2]
        fi = s[5] if len(s) > 5 else focal
        ki = fi / f0
        cpos = back(s[1], target, ki)
        cend, tend = (back(s[3], s[4], ki), s[4]) if len(s) > 3 else (cpos, target)
        stop = shots[i + 1][0] - frame if i + 1 < len(shots) else L
        cam.SetFocalLength(ms(start), fi)
        cam.SetFocalLength(ms(stop), fi)
        set_key(cam, start, cpos, look(cpos, target))
        set_key(cam, stop, cend, look(cend, tend))
        log.append("shot %d %.1f-%.1f cam %s -> %s" % (i + 1, start, stop, cpos, cend))

    RLPy.RGlobal.SetEndTime(ms(L))
    RLPy.RScene.ClearSelectObjects()
    open(os.path.join(J, "stage_log.txt"), "w", encoding="utf-8").write("\n".join(log))
    if job.get("mode") == "video":
        RLPy.RGlobal.SetTime(ms(0))
        RLPy.RGlobal.RenderVideo(job["out"])
        log.append("render done " + job["out"])
    elif job.get("mode") == "setup":
        RLPy.RGlobal.SetTime(ms(0))
        log.append("setup done")
    else:
        for i, s in enumerate(shots):
            start = s[0]
            stop = shots[i + 1][0] if i + 1 < len(shots) else L
            for tag, sec in (("a", start + 0.5), ("b", stop - 0.5)):
                RLPy.RGlobal.SetTime(ms(sec))
                RLPy.RGlobal.RenderImage(os.path.join(J, "stage_shot%d%s.png" % (i + 1, tag)))
        log.append("stills done")
except Exception:
    log.append(traceback.format_exc())
open(os.path.join(J, "stage_log.txt"), "w", encoding="utf-8").write("\n".join(log))
