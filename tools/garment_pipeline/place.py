"""Stage 4a: put the decimated garment on the CC5 body automatically (no Blender, CC5 can stay open).

  python place.py --run <run dir> --mesh dec_30000.ply --body <body_tpose.obj from CC5, Z-up cm>

TRELLIS output is unit-size, Y-up. We rotate it to CC's Z-up, then search uniform scale + offset (and a small
x/z stretch) so that: the collar sits at the base of the neck, the shirt is centred on the torso, as few garment
points as possible are inside the body, and the shirt stays close to the body (no floating).
Writes placed.obj (Y-up cm, the axis CC5 imports OBJ with) and place_report.json.
"""
import argparse, json
from pathlib import Path
import numpy as np
import trimesh
from scipy.spatial import cKDTree
from scipy.optimize import minimize


def load_body(path):
    """CC_Base_Body group from the CC5 OBJ export (Z-up, cm)."""
    V, F, cur, keep = [], [], None, []
    for line in open(path, encoding="utf-8", errors="ignore"):
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("g ") or line.startswith("o "):
            cur = line.split(None, 1)[1].strip()
        elif line.startswith("f ") and cur and cur.startswith("CC_Base_Body"):
            keep.append([int(t.split("/")[0]) - 1 for t in line.split()[1:]])
    tri = [[f[0], f[i], f[i + 1]] for f in keep for i in range(1, len(f) - 1)]
    m = trimesh.Trimesh(np.array(V), np.array(tri), process=False)
    m.remove_unreferenced_vertices()
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True); ap.add_argument("--mesh", required=True)
    ap.add_argument("--body", required=True); ap.add_argument("--ease", type=float, default=0.6)
    ap.add_argument("--out", default="placed")
    a = ap.parse_args()
    run = Path(a.run)
    body = load_body(a.body)
    g = trimesh.load(run / a.mesh, force="mesh")
    parts = g.split(only_watertight=False)                     # drop TRELLIS floater crumbs, keep the shirt
    g = max(parts, key=lambda c: len(c.faces))
    G = g.vertices.copy()
    G = np.c_[G[:, 0], -G[:, 2], G[:, 1]]           # glTF Y-up (front +Z) -> CC Z-up (front -Y)
    # --- body landmarks (T-pose) ---
    bv = body.vertices; H = bv[:, 2].max()
    torso = bv[np.abs(bv[:, 0]) < 0.12 * H]
    neck_z = 0.82 * H                                # base of neck on a CC body
    sh = bv[(bv[:, 2] > 0.78 * H) & (bv[:, 2] < 0.83 * H)]
    # --- garment landmarks ---
    gz = G[:, 2]; top = gz.max()
    core = G[np.abs(G[:, 0] - np.median(G[:, 0])) < 0.15 * np.ptp(G[:, 0])]
    # initial scale: garment torso width ~ body torso width at chest (+ease)
    chest = bv[(bv[:, 2] > 0.70 * H) & (bv[:, 2] < 0.74 * H) & (np.abs(bv[:, 0]) < 0.14 * H)]
    gch = core[(core[:, 2] > top - 0.35 * np.ptp(gz)) & (core[:, 2] < top - 0.25 * np.ptp(gz))]
    s0 = (neck_z + 0.02 * H - 0.50 * H) / np.ptp(gz)      # collar top -> hem = base of neck -> hip
    G0c = np.array([np.median(core[:, 0]), np.median(core[:, 1]), top])
    G0 = G - G0c

    bt = cKDTree(bv); bn = body.vertex_normals
    sample = G0[np.random.default_rng(0).choice(len(G0), min(8000, len(G0)), replace=False)]

    def apply(p, pts):
        s, sx, sy, tx, ty, tz = p
        return pts * np.array([s * sx, s * sy, s]) + np.array([tx, ty, tz])

    def cost(p, detail=False):
        P = apply(p, sample)
        d, i = bt.query(P)
        sd = np.einsum("ij,ij->i", P - bv[i], bn[i])        # signed distance (+ outside)
        inside = np.clip(a.ease - sd, 0, None)
        far = np.clip(sd - 4.0, 0, None)                      # more than 4 cm away = floating
        c = (inside ** 2).mean() * 50 + (far ** 2).mean() * 0.5 + 0.02 * ((p[1] - 1) ** 2 + (p[2] - 1) ** 2) * 100
        if detail:
            return {"inside_frac": float((sd < 0).mean()), "inside_p99_cm": float(np.percentile(np.clip(-sd, 0, None), 99)),
                    "median_gap_cm": float(np.median(sd)), "floating_frac": float((sd > 4).mean())}
        return c

    # one direct landmark fit + a quick 1-D search on scale/height (seconds, not minutes)
    x = [s0, 1, 1, 0, float(np.median(torso[:, 1])), neck_z + 0.02 * H]
    best_c = cost(x)
    for i, step in ((4, 1.0), (4, 0.3)):            # only front/back; size and collar height come from the body
        for _ in range(12):
            moved = False
            for sgn in (1, -1):
                y = list(x); y[i] += sgn * step
                c = cost(y)
                if c < best_c: x, best_c, moved = y, c, True
            if not moved: break
    # sleeves must sit ON the T-pose arms: lift/lower so sleeve top = arm top + ease
    P1 = apply(x, sample); half = np.ptp(P1[:, 0]) / 2
    sl = P1[np.abs(P1[:, 0]) > 0.7 * half]
    arm = bv[(np.abs(bv[:, 0]) > np.abs(sl[:, 0]).min()) & (np.abs(bv[:, 0]) < np.abs(sl[:, 0]).max()) & (bv[:, 2] > 0.7 * H)]
    x[5] += arm[:, 2].max() + a.ease - sl[:, 2].max()
    class R: pass
    best = R(); best.x = x
    P = apply(best.x, G0)
    out = trimesh.Trimesh(np.c_[P[:, 0], P[:, 2], -P[:, 1]], g.faces, process=False)   # Z-up -> Y-up for CC5
    out.export(run / (a.out + ".obj"))
    rep = {"center": [float(v) for v in G0c], "params": dict(zip(["scale", "sx", "sy", "tx", "ty", "tz"], map(float, best.x))), **cost(best.x, True),
           "faces": int(len(g.faces)), "garment_height_cm": float(np.ptp(P[:, 2])), "span_cm": float(np.ptp(P[:, 0]))}
    json.dump(rep, open(run / (a.out + "_report.json"), "w"), indent=1)
    print("PLACED", json.dumps(rep))


if __name__ == "__main__":
    main()
