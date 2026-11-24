"""Conservative hair QC gate for modern Thai CC5 stories.

This is a technical and prior-review screen, not an assertion that visual QA passed.
Never deletes assets. Past scene files remain untouched.
"""
import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCAN = ROOT / "runs" / "wardrobe_scan"
PROHIBITED_NOTES = ("textures missing", "hangs cc5", "broken texture",
                    "cannot dye", "missing texture", "invalid mesh", "load failed")
SUPPORTED = {".rlhair", ".cchair"}

@lru_cache(maxsize=1)
def previous_visual_review():
    """Map asset path to previous lookbook review, if one exists."""
    matches = {}
    try:
        candidates = json.loads((SCAN / "cand_custom_hair.json").read_text(encoding="utf-8"))
        for filename in ("hair_catalog_part_000_078.json", "hair_catalog_part_079_157.json"):
            for item in json.loads((SCAN / filename).read_text(encoding="utf-8")):
                idx = int(item["id"])
                if not 0 <= idx < len(candidates):
                    continue
                path = str(candidates[idx]["path"]).casefold()
                matches[path] = item
    except (OSError, ValueError, TypeError, KeyError):
        pass
    return matches

def assess(entry):
    """(status, reason): eligible_for_draft | needs_review | rejected."""
    path = str(entry.get("path") or "")
    if not path:
        return "rejected", "missing path"
    if entry.get("bad"):
        return "rejected", "existing bad flag"
    if not Path(path).is_file():
        return "rejected", "source file missing"
    if Path(path).suffix.casefold() not in SUPPORTED:
        return "rejected", "not a standalone head-hair asset"
    note = str(entry.get("note") or "").casefold()
    if any(reason in note for reason in PROHIBITED_NOTES):
        return "rejected", "recorded technical defect: " + note[:100]
    previous = previous_visual_review().get(path.casefold())
    if previous:
        if previous.get("verdict") != "ok" or not previous.get("thai_story_ok", False):
            return "rejected", "previous visual QA "+str(previous.get("verdict"))+": "+str(previous.get("problems", ""))[:100]
    if not entry.get("checked"):
        return "needs_review", "not yet checked in CC5"
    return "eligible_for_draft", "technically screened; final multi-angle visual QA still required"

def safe_for_autopick(entry):
    return assess(entry)[0] == "eligible_for_draft"
