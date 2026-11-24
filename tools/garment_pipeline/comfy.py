"""Tiny ComfyUI HTTP client shared by the garment pipeline stages."""
import json, time, urllib.request, urllib.parse, shutil
from pathlib import Path

QWEN_URL = "http://127.0.0.1:8193"          # Tidmunz portable ComfyUI (Qwen-Image-Edit 2511 GGUF)
QWEN_ROOT = Path(r"E:\TidmunzLocalAI\ComfyUI_windows_portable\ComfyUI")
TRELLIS_URL = "http://127.0.0.1:8188"       # StableGen ComfyUI (native TRELLIS.2)
TRELLIS_ROOT = Path(r"E:\StableGen\ComfyUI")


def req(base, path, data=None, timeout=60):
    r = urllib.request.Request(base + path, data=None if data is None else json.dumps(data).encode(),
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=timeout) as f:
        body = f.read()
        return json.loads(body) if body else None


def wait_ready(base, tries=240):
    for _ in range(tries):
        try:
            return req(base, "/object_info", timeout=30)
        except Exception:
            time.sleep(2)
    raise RuntimeError("ComfyUI not reachable at " + base)


def run(base, graph, timeout=3600, label="job"):
    """Queue a prompt graph, wait, return the history entry (raises on execution error)."""
    pid = req(base, "/prompt", {"prompt": graph, "client_id": "garment-pipeline"})["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < timeout:
        h = req(base, "/history/" + pid)
        if h and pid in h:
            e = h[pid]
            st = e.get("status", {})
            if st.get("status_str") == "error":
                msgs = [m for m in st.get("messages", []) if m[0] == "execution_error"]
                raise RuntimeError(f"{label} failed: {json.dumps(msgs)[:2000]}")
            if st.get("completed", True):
                print(f"[{label}] done in {time.time() - t0:.0f}s", flush=True)
                return e
        time.sleep(2)
    raise TimeoutError(label)


def outputs(entry, root, kind="images"):
    """Absolute paths of files a finished prompt wrote (images or 3d)."""
    files = []
    for node in entry["outputs"].values():
        for key, items in node.items():
            if not isinstance(items, list):
                continue
            for it in items:
                if isinstance(it, dict) and "filename" in it:
                    files.append(Path(root) / it.get("type", "output") / it.get("subfolder", "") / it["filename"])
    return files


def node(t, **kw):
    return {"class_type": t, "inputs": kw}


def stage_input(src, root, name):
    dst = Path(root) / "input" / name
    shutil.copyfile(src, dst)
    return name
