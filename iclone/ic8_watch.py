# Load ONCE per iClone launch (Script > Load Python). Afterwards Claude drops scripts into
#   %LOCALAPPDATA%\Tidmunz Studio\snapgen_data\ic8_jobs\run\*.py
# and this timer runs each one inside iClone, then renames it to .done (or .err) and writes <name>.log.
# No more menus / screenshots needed.
import os, glob, traceback, builtins
from PySide2 import QtCore

RUN = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "ic8_jobs", "run")
os.makedirs(RUN, exist_ok=True)


def _tick():
    for f in sorted(glob.glob(os.path.join(RUN, "*.py"))):
        base = f[:-3]
        try:
            code = open(f, encoding="utf-8").read()
            g = {"__name__": "__main__", "__file__": f}
            exec(compile(code, f, "exec"), g)
            open(base + ".log", "a", encoding="utf-8").write("OK\n")
            os.replace(f, base + ".done")
        except Exception:
            open(base + ".log", "a", encoding="utf-8").write(traceback.format_exc())
            os.replace(f, base + ".err")


old = getattr(builtins, "_claude_ic8_timer", None)
if old:
    old.stop()
t = QtCore.QTimer()
t.timeout.connect(_tick)
t.start(1000)
builtins._claude_ic8_timer = t  # keep it alive
open(os.path.join(RUN, "watcher.alive"), "w").write("ok")
