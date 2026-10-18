# Run inside iClone 8 (scene already keyed + one real camera created via Create > Camera > Linear Camera).
# ic8_jobs\shots.json: {"out": mp4 path, "shots": [[start_sec, view, [avatar names]], ...]}
# view = Front/Back/Left/Right. Per shot: frame the named avatars from that side, key the camera there
# (held until the next shot = hard cut), then render the video. Log: ic8_jobs\shots_log.txt
import json, os, traceback
import RLPy

J = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "ic8_jobs")
log = []


def ms(sec):
    return RLPy.RTime.FromValue(int(round(sec * 1000)))


def save_log():
    open(os.path.join(J, "shots_log.txt"), "w", encoding="utf-8").write("\n".join(log))


try:
    job = json.load(open(os.path.join(J, "shots.json"), encoding="utf-8"))
    cams = RLPy.RScene.GetCameras()
    cam = cams[0]
    RLPy.RScene.SetCurrentCamera(cam)
    avatars = {a.GetName(): a for a in RLPy.RScene.GetAvatars()}
    ctrl = cam.GetControl("Transform")
    poses = []
    for start, view, names in job["shots"]:
        RLPy.RGlobal.SetTime(ms(start))
        RLPy.RScene.SelectObjects([avatars[n] for n in names if n in avatars])
        cam.SetCameraLocation(getattr(RLPy, "ECameraLocationType_" + view))
        cam.SetCameraLocation(RLPy.ECameraLocationType_Focus)
        t = RLPy.RTransform()
        ctrl.GetValue(ms(start), t)
        poses.append(RLPy.RTransform(t))
        log.append("shot %.1f %s %s" % (start, view, names))
    end = RLPy.RGlobal.GetEndTime().ToFloat() / 1000.0
    frame = 1.0 / RLPy.RGlobal.GetFps().ToFloat()
    for i, (start, view, names) in enumerate(job["shots"]):
        stop = job["shots"][i + 1][0] - frame if i + 1 < len(job["shots"]) else end
        ctrl.SetValue(ms(start), poses[i])
        ctrl.SetValue(ms(stop), poses[i])
    RLPy.RScene.ClearSelectObjects()
    RLPy.RGlobal.SetTime(ms(0))
    log.append("camera keyed, rendering " + job["out"])
    save_log()
    os.makedirs(os.path.dirname(job["out"]), exist_ok=True)
    RLPy.RGlobal.RenderVideo(job["out"])
    log.append("render done")
except Exception:
    log.append(traceback.format_exc())
save_log()
