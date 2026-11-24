"""Clean recoverable staging after a successful CC5 build."""

import json
import os
import re
from pathlib import Path


def _save(directory, job):
    pending = directory / ".job.tidy.tmp"
    try:
        pending.write_text(json.dumps(job, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(pending, directory / "job.json")
    finally:
        pending.unlink(missing_ok=True)


def tidy(here, job, name, log):
    directory = Path(here).resolve()
    if any(line.startswith("FAIL") or "BATCH FAIL" in line for line in log):
        return "kept everything (a step failed)"
    if Path(name).name != name or not (directory / (name + ".ccProject")).is_file():
        return "kept everything (no .ccProject)"

    originals = job.get("original_asset_paths", [])
    sources = {}
    for item in job["items"]:
        match = re.match(r"item(\d+)\.", item)
        if match and int(match[1]) < len(originals):
            sources[item] = originals[int(match[1])]
    if "hair.rlHair" in job["items"] and job.get("hair_source"):
        sources["hair.rlHair"] = job["hair_source"]
    sources.update(job.get("sources") or {})

    copies = {}
    for item, original in sources.items():
        if not original or not re.fullmatch(r"(?:item\d+|new\d+|hair)\.[\w]+", item, re.I):
            continue
        source, copy = Path(original), directory / item
        if (source.is_absolute() and source.is_file() and copy.is_file()
                and copy.resolve() == copy and source.resolve() != copy
                and source.stat().st_size == copy.stat().st_size):
            copies[item] = original

    job["items"] = [copies.get(item, item) for item in job["items"]]
    fabrics = job.get("fabrics", {})
    for item, original in copies.items():
        if item in fabrics:
            fabrics[original] = fabrics.pop(item)
    # If interrupted, job.json already points to originals and retains the copy records for retry.
    job["sources"] = sources
    if copies:
        _save(directory, job)
    freed = 0
    for item in copies:
        copy = directory / item
        freed += copy.stat().st_size
        copy.unlink()
        sources.pop(item, None)
    layers = directory / "layer_fix"
    if layers.is_dir() and layers.resolve() == layers:
        for obj in layers.rglob("*.obj"):
            if obj.is_file() and obj.resolve() == obj:
                freed += obj.stat().st_size
                obj.unlink()
    if not sources:
        job.pop("sources", None)
    _save(directory, job)
    return "freed %.0f MB" % (freed / 1e6)
