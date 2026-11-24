"""Stage 4a: align the garment as TIGHT to the T-pose body as possible (before Blender push-out and skin weights).
  python tightfit.py --run <run> --placed placed_hy_v3.obj --body body_tpose.obj --out tight_hy
Searches 9 numbers around the garment centre: move x/y/z (cm), rotate x/y/z (deg), scale width/depth/height.
Cost = how far the covered skin is from the cloth (pulls it snug) + penalty for cloth deep inside the body.
A little skin poking through is allowed: the Blender push-out step fixes that. Writes <out>.obj (Y-up cm) + report."""
import argparse, json
from pathlib import Path
import numpy as np, trimesh
from scipy.spatial import cKDTree
from scipy.optimize import minimize
from scipy.spatial.transform import Rotation
from place import load_body

ap = argparse.ArgumentParser()
for k in ("run", "placed", "body", "out"): ap.add_argument("--" + k, required=True)
ap.add_argument("--allow_in", type=float, default=0.8, help="cm of skin poke-through tolerated before penalty")
a = ap.parse_args(); run = Path(a.run)
body = load_body(a.body); bv, bn = body.vertices, body.vertex_normals; bt = cKDTree(bv)
g = trimesh.load(run / a.placed, force="mesh", process=False)
G = np.c_[g.vertices[:, 0], -g.vertices[:, 2], g.vertices[:, 1]]          # Y-up -> Z-up cm
cen = G.mean(0); rng = np.random.default_rng(0)
gs = G[rng.choice(len(G), 6000, replace=False)] - cen
d0, _ = cKDTree(G).query(bv)
cov = bv[d0 < 5.0]                                                          # skin the shirt is meant to cover
cov = cov[rng.choice(len(cov), min(6000, len(cov)), replace=False)]

def tf(p, P):
    R = Rotation.from_euler("xyz", p[3:6], degrees=True).as_matrix()
    return (P * p[6:9]) @ R.T + cen + p[0:3]

def parts(p):
    P = tf(p, gs)
    gap, _ = cKDTree(P).query(cov)                                          # skin -> nearest cloth
    _, i = bt.query(P); sd = np.einsum("ij,ij->i", P - bv[i], bn[i])        # cloth depth vs skin
    return gap, sd

def cost(p):
    gap, sd = parts(p)
    return np.mean(np.minimum(gap, 6.0) ** 2) + 20 * np.mean(np.clip(-sd - a.allow_in, 0, None) ** 2)

def stats(p):
    gap, sd = parts(p)
    return dict(skin_to_cloth_median_cm=float(np.median(gap)), skin_to_cloth_p90_cm=float(np.percentile(gap, 90)),
                cloth_inside_frac=float((sd < 0).mean()), cloth_inside_p99_cm=float(np.percentile(np.clip(-sd, 0, None), 99)))

x0 = np.array([0, 0, 0, 0, 0, 0, 1, 1, 1.0])
r = minimize(cost, x0, method="Powell", options=dict(maxiter=4000, xtol=1e-3, ftol=1e-5),
             bounds=[(-6, 6)] * 3 + [(-12, 12)] * 3 + [(0.75, 1.15), (0.75, 1.15), (0.97, 1.03)])
P = tf(r.x, G - cen)
trimesh.Trimesh(np.c_[P[:, 0], P[:, 2], -P[:, 1]], g.faces, process=False).export(run / (a.out + ".obj"))
rep = dict(center=cen.tolist(), params=r.x.tolist(), move_cm=r.x[0:3].round(2).tolist(), rotate_deg=r.x[3:6].round(2).tolist(), scale=r.x[6:9].round(3).tolist(),
           before=stats(x0), after=stats(r.x), evals=int(r.nfev))
json.dump(rep, open(run / (a.out + "_report.json"), "w"), indent=1); print(json.dumps(rep))
