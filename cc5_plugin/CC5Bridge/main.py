# CC5 Bridge — CC5 loads this at startup (OpenPlugin junction, see install_plugin.bat).
# Lets ANY agent (Claude, GPT/Codex, a person) drive CC5 by writing files — no screen clicks needed.
#   inbox : <cc5_jobs>\bridge\inbox\<id>.json   {"script": "<path to .py>", "args": {...}}
#   outbox: <cc5_jobs>\bridge\outbox\<id>.json  {"status": "ok"|"error", "log": "...", "started": ..., "finished": ...}
#   alive : <cc5_jobs>\bridge\heartbeat.txt     (time of the last poll; stale = CC5 closed or busy)
# The script runs inside CC5 like Script > Load Python, with BRIDGE_ARGS = args in its globals.
# Also clicks OK on the "Failed to establish a connection" startup popup so nobody has to.
import json, os, time, traceback

try:
    from PySide2 import QtCore, QtWidgets
except ImportError:  # CC5 builds with Qt6
    from PySide6 import QtCore, QtWidgets

BRIDGE = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Tidmunz Studio", "snapgen_data", "cc5_jobs", "bridge")
INBOX, OUTBOX = os.path.join(BRIDGE, "inbox"), os.path.join(BRIDGE, "outbox")
_timer = None
AUTO_OK = ("Failed to establish a connection",)


def _write(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def _dismiss_popups():
    for w in QtWidgets.QApplication.topLevelWidgets():
        if isinstance(w, QtWidgets.QMessageBox) and w.isVisible() and any(t in w.text() for t in AUTO_OK):
            w.accept()


def _run(cmd_path):
    cid = os.path.splitext(os.path.basename(cmd_path))[0]
    res = {"id": cid, "started": time.strftime("%Y-%m-%d %H:%M:%S")}
    try:
        cmd = json.load(open(cmd_path, encoding="utf-8"))
        os.remove(cmd_path)
        script = cmd["script"]
        res["script"] = script
        g = {"__file__": script, "__name__": "__main__", "BRIDGE_ARGS": cmd.get("args", {})}
        exec(compile(open(script, encoding="utf-8").read(), script, "exec"), g)
        res["status"] = "ok"
        res["log"] = str(g.get("BRIDGE_RESULT", ""))
    except Exception:
        res["status"] = "error"
        res["log"] = traceback.format_exc()
    res["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    _write(os.path.join(OUTBOX, cid + ".json"), res)


def _tick():
    try:
        _dismiss_popups()
        open(os.path.join(BRIDGE, "heartbeat.txt"), "w").write(time.strftime("%Y-%m-%d %H:%M:%S"))
        jobs = sorted(f for f in os.listdir(INBOX) if f.endswith(".json"))
        if jobs:
            _timer.stop()  # one command at a time; CC5 is single-threaded
            try:
                _run(os.path.join(INBOX, jobs[0]))
            finally:
                _timer.start()
    except Exception:
        pass


def initialize_plugin():
    global _timer
    for d in (INBOX, OUTBOX):
        os.makedirs(d, exist_ok=True)
    _timer = QtCore.QTimer()
    _timer.timeout.connect(_tick)
    _timer.start(2000)


def run_script():
    initialize_plugin()
