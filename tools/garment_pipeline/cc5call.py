"""Run a python script inside CC5 through the CC5Bridge file inbox. Usage: cc5call.py script.py key=value ..."""
import json, os, sys, time, uuid
B = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "cc5_jobs", "bridge")
def call(script, args=None, timeout=900):
    cid = time.strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8]
    tmp = os.path.join(B, "inbox", cid + ".tmp")
    json.dump({"script": os.path.abspath(script), "args": args or {}}, open(tmp, "w", encoding="utf-8"))
    os.replace(tmp, tmp[:-4] + ".json")
    out = os.path.join(B, "outbox", cid + ".json")
    t0 = time.time()
    while time.time() - t0 < timeout:
        if os.path.exists(out):
            time.sleep(0.2); return json.load(open(out, encoding="utf-8"))
        time.sleep(0.5)
    raise TimeoutError(cid)
if __name__ == "__main__":
    r = call(sys.argv[1], dict(a.split("=", 1) for a in sys.argv[2:]))
    print(r["status"]); print(r["log"])
