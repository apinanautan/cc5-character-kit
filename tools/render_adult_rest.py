# Render the remaining adult cloth candidates (index 245..353) in CC5, 10 per run, one run after another.
#   python tools\render_adult_rest.py [start] [end]
# Each run goes to runs/wardrobe_scan/adult_batch_<a>_<b>/ (same layout as the earlier batches); progress in render_rest.log.
import os, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, "runs", "wardrobe_scan")
start = int(sys.argv[1]) if len(sys.argv) > 1 else 245
end = int(sys.argv[2]) if len(sys.argv) > 2 else 353
log = open(os.path.join(S, "render_rest.log"), "a", encoding="utf-8")


def say(m):
    log.write(time.strftime("%H:%M:%S ") + m + "\n"); log.flush()


n = start
while n <= end:
    cnt = min(10, end - n + 1)
    out = os.path.join(S, "adult_batch_%03d_%03d" % (n, n + cnt - 1))
    if all(os.path.exists(os.path.join(out, "%03d.png" % i)) for i in range(n, n + cnt)):   # skip only when EVERY picture of the batch exists
        n += cnt; continue
    ping = subprocess.run([sys.executable, "tools/cc5.py", "run", "cc5/ping.py"], cwd=ROOT, capture_output=True, text=True, timeout=120)
    if "CC5 OK" not in ping.stdout:
        say("STOP: CC5 not alive: " + ping.stdout[-120:].replace("\n", " ")); break
    try:
        r = subprocess.run([sys.executable, "tools/cc5.py", "run", "cc5/probes/test_items.py", "list=" + os.path.join(S, "cand_adult_cloth.json"),
                            "start=%d" % n, "count=%d" % cnt, "out=" + out], cwd=ROOT, capture_output=True, text=True, timeout=480)
        say("batch %d-%d: %s" % (n, n + cnt - 1, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "no output"))
    except subprocess.TimeoutExpired:
        say("batch %d-%d TIMEOUT (CC5 hung?) -> stop" % (n, n + cnt - 1)); break
    n += cnt
say("finished up to %d" % (n - 1))
