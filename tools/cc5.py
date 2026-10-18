# Drive CC5 from any agent/terminal through the CC5Bridge plugin (no screen control needed).
#   python tools\cc5.py status                     is CC5 alive? who holds the lock?
#   python tools\cc5.py run <script.py> [k=v ...]  run a script inside CC5 and wait for the result
#   python tools\cc5.py lock <name> / unlock       claim / free CC5 so two agents don't drive it at once
# Scripts get BRIDGE_ARGS (dict of k=v) and may set BRIDGE_RESULT (text returned here).
import json, os, sys, time, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

B = os.path.join(kit.JOBS, "bridge")
INBOX, OUTBOX, LOCK = os.path.join(B, "inbox"), os.path.join(B, "outbox"), os.path.join(kit.JOBS, "LOCK.txt")


def alive():
    try:
        age = time.time() - os.path.getmtime(os.path.join(B, "heartbeat.txt"))
    except OSError:
        return False, None
    return age < 10, age


def main(a):
    os.makedirs(INBOX, exist_ok=True)
    os.makedirs(OUTBOX, exist_ok=True)
    if not a or a[0] == "status":
        ok, age = alive()
        print("CC5 bridge:", "ALIVE" if ok else "NOT RUNNING (open CC5; if just opened wait ~2 min)",
              "" if age is None else "(last beat %.0fs ago)" % age)
        print("lock:", open(LOCK, encoding="utf-8").read().strip() if os.path.exists(LOCK) else "free")
        print("queued:", len(os.listdir(INBOX)))
        return
    if a[0] == "lock":
        if os.path.exists(LOCK):
            sys.exit("already locked: " + open(LOCK, encoding="utf-8").read())
        open(LOCK, "w", encoding="utf-8").write("%s since %s" % (a[1], time.strftime("%Y-%m-%d %H:%M")))
        print("locked by", a[1]); return
    if a[0] == "unlock":
        if os.path.exists(LOCK):
            os.remove(LOCK)
        print("unlocked"); return
    if a[0] == "run":
        script = os.path.abspath(a[1] if os.path.isabs(a[1]) or os.path.exists(a[1]) else os.path.join(kit.REPO, a[1]))
        args = dict(x.split("=", 1) for x in a[2:])
        cid = time.strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:6]
        p = os.path.join(INBOX, cid + ".json")
        json.dump({"script": script, "args": args}, open(p + ".tmp", "w", encoding="utf-8"), ensure_ascii=False)
        os.replace(p + ".tmp", p)
        if not alive()[0]:
            print("WARNING: bridge not alive — the command waits in the inbox until CC5 runs")
        out = os.path.join(OUTBOX, cid + ".json")
        t = time.time()
        from start_cc5 import cc5_pids, popups, press, VK_RETURN
        while not os.path.exists(out):
            time.sleep(2)
            for h in popups(cc5_pids()):  # modal warnings (missing hair textures etc.) block CC5 -> OK them
                press(h, VK_RETURN)
            if time.time() - t > 3600:
                sys.exit("timeout waiting for " + out)
        r = json.load(open(out, encoding="utf-8"))
        print(r["status"].upper(), r.get("started"), "->", r.get("finished"))
        print(r.get("log", ""))
        sys.exit(0 if r["status"] == "ok" else 1)
    sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
