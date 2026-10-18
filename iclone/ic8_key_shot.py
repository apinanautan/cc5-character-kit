# Run inside iClone 8 (Script > Load Python) AFTER opening the scene .iProject.
# Optional: select one object (prop/dummy) where the action happens = anchor; nothing selected = world origin.
# Reads the job JSON named in snapgen_data\ic8_jobs\shot.txt: loads each character, places it around
# the anchor, gives it ONE motion slowed to fill the audio length,
# sets project length, saves as a new .iProject. Log: ic8_jobs\log.txt
import json, math, os, traceback
import RLPy

J = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "ic8_jobs")
log = []


TICK = 6000.0  # iClone RTime unit: 1/6000 second (NOT ms)


def ms(sec):
    return RLPy.RTime.FromValue(int(round(sec * TICK)))  # RTime = 1/6000 s ticks, int only


def place(av, x, y, z, yaw_deg):
    ctrl = av.GetControl("Transform")
    t = RLPy.RTransform()
    ctrl.GetValue(ms(0), t)
    t.T().x, t.T().y, t.T().z = x, y, z
    q = RLPy.RQuaternion()
    q.FromAxisAngle(RLPy.RVector3(0, 0, 1), math.radians(yaw_deg))
    t.R().x, t.R().y, t.R().z, t.R().w = q.x, q.y, q.z, q.w
    ctrl.SetValue(ms(0), t)


def lay_motion(av, path, length):
    # one motion, slowed down so it lasts the whole audio
    skel = av.GetSkeletonComponent()
    RLPy.RFileIO.LoadMotion(path, ms(0), av)
    clip = skel.GetClip(skel.GetClipCount() - 1)
    dur = clip.GetClipLength().ToFloat() / TICK
    if dur <= 0:
        log.append("  ! motion length 0")
        return
    if dur < length:
        clip.SetSpeed(dur / length)
    log.append("  %s  %.1fs -> %.1fs" % (os.path.basename(path), dur, clip.GetClipLength().ToFloat() / TICK))


try:
    job = json.load(open(open(os.path.join(J, "shot.txt"), encoding="utf-8").read().strip(), encoding="utf-8"))
    log.append("job: " + job["name"])
    sel = RLPy.RScene.GetSelectedObjects()
    ax = ay = az = 0.0
    if sel:
        a = sel[0].WorldTransform().T()
        ax, ay = a.x, a.y  # keep z = 0 (ground); a selected light/camera sits in the air
        log.append("anchor: %s (%.0f, %.0f, %.0f)" % (sel[0].GetName(), ax, ay, az))
    else:
        log.append("anchor: origin (nothing selected)")

    for c in job["characters"]:
        path = os.path.join(job["char_root"], c["file"])
        log.append(c["file"])
        try:
            before = set(a.GetID() for a in RLPy.RScene.GetAvatars())
            RLPy.RScene.ClearSelectObjects()
            RLPy.RFileIO.LoadFile(path)
            new = [a for a in RLPy.RScene.GetAvatars() if a.GetID() not in before]
            if not new:
                log.append("  ! not loaded")
                continue
            av = new[0]
            place(av, ax + c["pos"][0], ay + c["pos"][1], az, c.get("yaw", 0))
            lay_motion(av, os.path.join(job["motion_root"], c["motion"]), job["length"])
        except Exception:
            log.append(traceback.format_exc())

    RLPy.RGlobal.SetEndTime(ms(job["length"]))
    RLPy.RGlobal.SetTime(ms(0))
    out = job.get("save")
    if out:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        s = RLPy.RSaveFileSetting()
        s.SetSaveType(RLPy.ESaveFileType_Project)
        try:
            RLPy.RFileIO.SaveFile(None, s, out)
            log.append("saved: " + out)
        except Exception:
            log.append("! save failed, save manually: " + out + "\n" + traceback.format_exc())
except Exception:
    log.append(traceback.format_exc())

open(os.path.join(J, "log.txt"), "w", encoding="utf-8").write("\n".join(log))
RLPy.RUi.ShowMessageBox("ic8_key_shot", "\n".join(log[-25:]), RLPy.EMsgButton_Ok)
