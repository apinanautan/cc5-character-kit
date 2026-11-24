# Render video by script (no Render panel clicks). ic8_jobs\render.json: {"out": path, "start": sec, "end": sec}
# Sets export type = Video, MP4, 1920x1080, 30fps, frame range, then RenderVideo. Log: render_log.txt
import json, os, traceback
import RLPy

J = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "ic8_jobs")
log = []
try:
    job = json.load(open(os.path.join(J, "render.json"), encoding="utf-8"))
    vid = 1  # export type: 0 = Image, 1 = Video (no enum exposed)
    RLPy.RGlobal.SetRenderExportType(vid)
    p = RLPy.RGlobal.GetRenderExportVideoParameter()
    fps = RLPy.RGlobal.GetFps().ToFloat()
    p.strFormat = "MP4"
    p.kCommon.kFps = "60"  # user: always 60 fps
    p.kCommon.nOutputSizeWidth, p.kCommon.nOutputSizeHeight = 1920, 1080
    p.kCommon.bFinalRender = True
    p.kOutputRange.nOutputRangeStart = int(round(job["start"] * fps))
    p.kOutputRange.nOutputRangeEnd = int(round(job["end"] * fps))
    try:
        p.bExportAudio = True
    except Exception:
        pass
    log.append("set param %s" % (RLPy.RGlobal.SetRenderExportParameter(p),))
    log.append("type now %s" % (RLPy.RGlobal.GetRenderExportType(),))
    open(os.path.join(J, "render_log.txt"), "w", encoding="utf-8").write("\n".join(log))
    r = RLPy.RGlobal.RenderVideo(job["out"])
    log.append("render returned %s exists=%s" % (r.IsError() if hasattr(r, "IsError") else r, os.path.exists(job["out"])))
except Exception:
    log.append(traceback.format_exc())
open(os.path.join(J, "render_log.txt"), "w", encoding="utf-8").write("\n".join(log))

