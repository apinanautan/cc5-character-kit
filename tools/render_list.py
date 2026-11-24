# Render a candidate list in CC5, 10 per run, one after another (generic version of render_adult_rest.py).
#   python tools\render_list.py <list.json> <batch_prefix> [start] [end]      e.g. cand_cc5_cloth.json cc5_batch
# Output: runs/wardrobe_scan/<prefix>_<a>_<b>/<index>.png ; log: runs/wardrobe_scan/<prefix>.log ; stops if CC5 is not alive / a batch hangs.
import json, os, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, "runs", "wardrobe_scan")
lst = os.path.join(S, sys.argv[1]); pre = sys.argv[2]
N = len(json.load(open(lst, encoding="utf-8")))
start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
end = min(int(sys.argv[4]) if len(sys.argv) > 4 else N - 1, N - 1)
kind = sys.argv[5] if len(sys.argv) > 5 else ""   # acc | hair | prop -> cc5/probes/test_assets.py instead of test_items.py
log = open(os.path.join(S, pre + ".log"), "a", encoding="utf-8")
say = lambda m: (log.write(time.strftime("%H:%M:%S ") + m + "\n"), log.flush())
n = start
while n <= end:
    cnt = min(10, end - n + 1)
    out = os.path.join(S, "%s_%03d_%03d" % (pre, n, n + cnt - 1))
    if all(os.path.exists(os.path.join(out, "%03d.png" % i)) for i in range(n, n + cnt)):   # skip only when EVERY picture of the batch exists
        n += cnt; continue
    ping = subprocess.run([sys.executable, "tools/cc5.py", "run", "cc5/ping.py"], cwd=ROOT, capture_output=True, text=True, timeout=120)
    if "CC5 OK" not in ping.stdout:
        say("STOP: CC5 not alive"); break
    try:
        r = subprocess.run([sys.executable, "tools/cc5.py", "run", ("cc5/probes/test_assets.py" if kind else "cc5/probes/test_items.py"), "list=" + lst, "start=%d" % n, "count=%d" % cnt, "out=" + out] + (["kind=" + kind] if kind else []),
                           cwd=ROOT, capture_output=True, text=True, timeout=480)
        say("batch %d-%d: %s" % (n, n + cnt - 1, (r.stdout.strip().splitlines() or ["no output"])[-1]))
    except subprocess.TimeoutExpired:
        say("batch %d-%d TIMEOUT -> stop" % (n, n + cnt - 1)); break
    n += cnt
say("finished up to %d" % (n - 1))
subprocess.run([sys.executable, "tools/job_state.py"], cwd=ROOT, capture_output=True)   # write RESUME.md / state.json
