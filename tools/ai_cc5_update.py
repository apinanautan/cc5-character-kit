"""GitHub release checks and allowlisted Ai-cc5 upgrades."""

import io
import json
import re
import time
import urllib.error
import urllib.request
import zipfile

from ai_cc5_state import atomic, load, save

REPO = "apinanautan/cc5-character-kit"
VERSION = "AI_CC5_VERSION"
FILES = (
    "Ai-cc5.cmd", "tools/ai_cc5.py", "tools/ai_cc5_state.py", "tools/ai_cc5_update.py",
    "tools/ai_cc5_continue.py", "tools/ai_cc5_progress.py", "tools/ai_cc5_ocr.ps1", "tools/cc5_gui.ps1",
    "tools/cc5_popup_guard.ps1", "cc5/probes/open_path.py", "cc5/texture_ready.py", "tools/job_tidy.py", "cc5/build.py",
    VERSION,
)
MAX_DOWNLOAD = 32 * 1024 * 1024


def version(root):
    return (root / VERSION).read_text(encoding="ascii").strip()


def semver(tag):
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", tag)
    if not match:
        raise ValueError(f"unsupported release tag {tag}")
    return tuple(map(int, match.groups()))


def get(url, limit, timeout):
    request = urllib.request.Request(url, headers={"User-Agent": "Ai-cc5"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError("release exceeds download limit")
    return data


def install(root, archive, tag):
    with zipfile.ZipFile(io.BytesIO(archive)) as package:
        names = package.namelist()
        if not names:
            raise ValueError("empty release")
        prefix = names[0].split("/")[0] + "/"
        payload = {}
        for relative in FILES:
            name = prefix + relative
            if names.count(name) != 1 or package.getinfo(name).file_size > 2 * 1024 * 1024:
                raise ValueError(f"missing, duplicated or oversized release file {relative}")
            target = root / relative
            if target.resolve() != root.resolve() / relative:
                raise ValueError(f"release target is redirected: {relative}")
            payload[target] = package.read(name)
        if semver(payload[root / VERSION].decode("ascii").strip()) != semver(tag):
            raise ValueError("release tag and version do not match")
    originals = {path: path.read_bytes() if path.exists() else None for path in payload}
    changed = []
    try:
        for path, data in payload.items():
            atomic(path, data)
            changed.append(path)
    except OSError:
        for path in reversed(changed):
            if originals[path] is None:
                path.unlink(missing_ok=True)
            else:
                atomic(path, originals[path])
        raise


def check(root, explicit=False):
    receipt = root / "runs" / ".ai_cc5_update.json"
    cached = load(receipt, {})
    if time.time() - cached.get("checked", 0) >= 600:
        cached = {"checked": time.time()}
        save(receipt, cached)
        try:
            release = json.loads(get(f"https://api.github.com/repos/{REPO}/releases/latest", 256 * 1024, 4))
            cached["tag"] = release["tag_name"]
            semver(cached["tag"])
        except urllib.error.HTTPError as exc:
            cached["error"] = "ยังไม่มี GitHub Release" if exc.code == 404 else f"GitHub HTTP {exc.code}"
        except (ValueError, OSError, KeyError) as exc:
            cached["error"] = str(exc)
        save(receipt, cached)
    if cached.get("error") or not cached.get("tag"):
        return (cached.get("error", "กำลังตรวจ release") if explicit else ""), False
    tag = cached["tag"]
    if semver(tag) <= semver(version(root)):
        return (f"ใช้รุ่นล่าสุดแล้ว ({version(root)})" if explicit else ""), True
    if not explicit:
        return f"มีรุ่น {tag} ใช้ Ai-cc5 update", True
    archive = get(f"https://codeload.github.com/{REPO}/zip/refs/tags/{tag}", MAX_DOWNLOAD, 15)
    install(root, archive, tag)
    return f"อัปเดต Ai-cc5 เป็น {tag} แล้ว", True
