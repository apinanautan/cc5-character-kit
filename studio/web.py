# Local server for the app window (studio/ui/index.html). Standard library only; listens on 127.0.0.1.
import json, os, socket, sys, threading, time, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit
import planner, runner, wardrobe

UI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "index.html")
STATE = {"runner": None, "thread": None, "story": None, "log": [], "image": None}
LOCK = threading.Lock()


def log(msg):
    with LOCK:
        STATE["log"].append(time.strftime("%H:%M ") + msg)
        STATE["log"] = STATE["log"][-200:]


def on_update(kind, data):
    if kind == "log":
        log(data)
    elif kind == "image":
        STATE["image"] = data


def busy():
    t = STATE["thread"]
    return bool(t and t.is_alive())


def item_names():
    pool = json.load(open(wardrobe.POOL, encoding="utf-8"))
    return {i["spec"]: i["name"] for k in ("tops", "bottoms", "full", "shoes") for i in pool[k]}


def story_view(path):
    s = runner.load(path)
    names = item_names()
    chars = []
    for job, c in s["characters"].items():
        d = os.path.join(kit.JOBS, job)
        st = s.get("status", {}).get(job, {})
        render = os.path.join(d, c["name"] + ".png")
        face = os.path.join(d, "face.png")
        pic = render if os.path.exists(render) else face if os.path.exists(face) else ""
        outfit = []
        for spec, fab in c["outfit"]:
            outfit.append({"name": names.get(spec, spec), "fabric": fab[4:] if fab and fab.startswith("gen:") else ""})
        designs = c.get("fabric_designs", [])
        if designs and not any(o["fabric"] for o in outfit):  # fabrics already made: show their designs
            k = 0
            for o, (spec, fab) in zip(outfit, c["outfit"]):
                if fab and k < len(designs):
                    o["fabric"] = designs[k]; k += 1
        chars.append({"job": job, "dir": d, "name": c["name"], "sex": "m" if c.get("sex") == "male" else "f", "age": c.get("age"),
                      "folder": c.get("folder", ""), "notes": c.get("notes", ""), "outfit": outfit,
                      "hair": os.path.splitext(os.path.basename(c.get("hair", "")))[0].lstrip("0123456789_"),
                      "status": st, "pic": pic, "pic_t": os.path.getmtime(pic) if pic else 0,
                      "same_head": s["characters"].get(c.get("head_from", ""), {}).get("name", "")})
    return {"path": path, "title": s.get("title", ""), "out_dir": s.get("out_dir", ""), "characters": chars}


def stories():
    out = []
    for f in sorted(os.listdir(os.path.join(kit.REPO, "stories")), reverse=True):
        if not f.endswith(".json"):
            continue
        p = os.path.join(kit.REPO, "stories", f)
        try:
            s = runner.load(p)
        except ValueError:
            continue
        if "status" not in s:
            continue  # stories made by hand before the app (e.g. krong): not run from here
        st = s.get("status", {})
        done = sum(1 for j in s["characters"] if str(st.get(j, {}).get("export", "")).startswith(("ok", "skip")))
        out.append({"path": p, "title": s.get("title", f), "count": len(s["characters"]), "done": done,
                    "t": os.path.getmtime(p), "app": "status" in s})
    return sorted(out, key=lambda x: -x["t"])


def api(path, q):
    if path == "/api/stories":
        return stories()
    if path == "/api/defaults":
        return {"out_root": kit.CFG["out_root"]}
    if path == "/api/parse":
        return planner.parse(q.get("text", ""))
    if path == "/api/create":
        p = runner.create_story(q["title"], q["rows"], q.get("out_root") or None)
        STATE["story"] = p
        return story_view(p)
    if path == "/api/story":
        return story_view(q["path"])
    if path == "/api/status":
        v = story_view(q["path"]) if q.get("path") else None
        with LOCK:
            return {"busy": busy(), "story": v, "log": STATE["log"][-60:], "image": STATE["image"]}
    if path == "/api/start":
        if busy():
            return {"ok": False, "msg": "กำลังทำงานอยู่"}
        STATE["log"] = []
        r = runner.Runner(q["path"], q.get("opts", {}), on_update)
        STATE.update(runner=r, story=q["path"], thread=threading.Thread(target=r.run, daemon=True))
        STATE["thread"].start()
        return {"ok": True}
    if path == "/api/stop":
        if STATE["runner"]:
            STATE["runner"].stop = True
        return {"ok": True}
    if path == "/api/reroll":
        if busy():
            return {"ok": False, "msg": "หยุดก่อน"}
        runner.reroll(q["path"], q["job"])
        return story_view(q["path"])
    if path == "/api/reset":
        if busy():
            return {"ok": False, "msg": "หยุดก่อน"}
        runner.reset(q["path"], q["job"], q.get("from", "fabric"))
        return story_view(q["path"])
    if path == "/api/open":
        target = q.get("dir") or kit.JOBS
        if os.path.isdir(target):
            os.startfile(target)
        return {"ok": True}
    raise KeyError(path)


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path in ("/", "/index.html"):
            return self._send(200, open(UI, "rb").read(), "text/html; charset=utf-8")
        if u.path == "/img":
            p = urllib.parse.parse_qs(u.query).get("p", [""])[0]
            real = os.path.realpath(p)
            if real.lower().startswith(os.path.realpath(kit.JOBS).lower()) and real.lower().endswith(".png") and os.path.exists(real):
                return self._send(200, open(real, "rb").read(), "image/png")
            return self._send(404, b"", "text/plain")
        self._send(404, b"", "text/plain")

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        q = json.loads(self.rfile.read(n) or b"{}")
        try:
            r = api(urllib.parse.urlparse(self.path).path, q)
            self._send(200, json.dumps(r, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")
        except Exception as e:
            self._send(500, json.dumps({"error": str(e)}, ensure_ascii=False).encode("utf-8"), "application/json")


def serve(port=0):
    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]
