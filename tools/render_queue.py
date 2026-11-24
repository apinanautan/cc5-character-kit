# Wait until the current render (custom cloth) has finished, then render the rest of the Custom library one list after another:
# accessories -> hair -> props.   python tools\render_queue.py      (resumable: run it again after any stop)
import os, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, "runs", "wardrobe_scan")
def finished(prefix):
    try:
        return "finished up to" in open(os.path.join(S, prefix + ".log"), encoding="utf-8").read().splitlines()[-1]
    except Exception:
        return False
while not finished("custom_batch"):
    time.sleep(30)
for lst, pre, kind in (("cand_custom_acc.json", "custacc_batch", "acc"), ("cand_custom_hair.json", "custhair_batch", "hair"), ("cand_custom_props.json", "custprop_batch", "prop")):
    subprocess.run([sys.executable, "tools/render_list.py", lst, pre, "0", "9999", kind], cwd=ROOT)
