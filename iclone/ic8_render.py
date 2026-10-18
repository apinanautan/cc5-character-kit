# Run inside iClone 8: render an exact frame range to mp4 (no reliance on the Render panel's range).
# ic8_jobs\render.json: {"out": path, "start": sec, "end": sec}  -> frames at the project fps. Log: render_log.txt
import json, os, traceback
import RLPy

J = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "ic8_jobs")
log = []
try:
    job = json.load(open(os.path.join(J, "render.json"), encoding="utf-8"))
    fps = RLPy.RGlobal.GetFps().ToFloat()
    s, e = int(round(job["start"] * fps)), int(round(job["end"] * fps))
    p = RLPy.RExportVideoParameter()
    p.strFormat = "MP4"
    p.kCommon.kFps = "30"  # this field is a string
    p.kCommon.nOutputSizeWidth, p.kCommon.nOutputSizeHeight = 1280, 720
    p.kCommon.bFinalRender = True
    p.kOutputRange.nOutputRangeStart = s
    p.kOutputRange.nOutputRangeEnd = e
    log.append("fps %.0f frames %d-%d end_time %.0f" % (fps, s, e, RLPy.RGlobal.GetEndTime().ToFloat()))
    open(os.path.join(J, "render_log.txt"), "w", encoding="utf-8").write("\n".join(log))
    # overloads: RenderVideo(path) | RenderVideo(RTime start, RTime end, path) -> use the explicit range
    r = RLPy.RGlobal.RenderVideo(RLPy.RTime.FromValue(int(job["start"] * 6000)),
                                 RLPy.RTime.FromValue(int(job["end"] * 6000)), job["out"])
    log.append("render returned %s" % (r,))
except Exception:
    log.append(traceback.format_exc())
open(os.path.join(J, "render_log.txt"), "w", encoding="utf-8").write("\n".join(log))
