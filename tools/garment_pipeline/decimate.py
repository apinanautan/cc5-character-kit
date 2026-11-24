"""Stage 3: shape-preserving polygon reduction (MeshLab quadric edge collapse) with measured error.

  python decimate.py --run <run dir> --raw raw_1024_s0.glb [--targets 100000,60000,40000]

For each target: clean (merge, drop debris, fix non-manifold) -> quadric edge collapse with boundary
(opening) preservation, normal preservation and optimal placement -> Hausdorff distance to the raw mesh.
Accepts the smallest target whose error stays under the limits (fraction of garment size):
mean < 0.05 %, 99th percentile < 0.3 %. Writes dec_<N>.ply + decimate_report.json. Raw file is never touched.
"""
import argparse, json
from pathlib import Path
import numpy as np
import pymeshlab as ml
import trimesh
from scipy.spatial import cKDTree

LIMIT_MEAN, LIMIT_P99 = 0.0005, 0.003


def clean(ms):
    ms.meshing_merge_close_vertices(threshold=ml.PercentageValue(0.01))
    ms.meshing_remove_duplicate_faces(); ms.meshing_remove_null_faces()
    ms.meshing_remove_connected_component_by_face_number(mincomponentsize=200)
    # no non-manifold "repair": it deletes faces and punches holes into the AI shell
    ms.meshing_remove_unreferenced_vertices()


def topo(m):
    e = np.sort(m.edges, axis=1); _, c = np.unique(e, axis=0, return_counts=True)
    return {"faces": int(len(m.faces)), "verts": int(len(m.vertices)), "boundary_edges": int((c == 1).sum()),
            "nonmanifold_edges": int((c > 2).sum())}


def deviation(ref, test, n=400000):
    """symmetric surface distance stats, as a fraction of the bbox diagonal"""
    diag = np.linalg.norm(ref.bounds[1] - ref.bounds[0])
    pa, _ = trimesh.sample.sample_surface(ref, n, seed=1); pb, _ = trimesh.sample.sample_surface(test, n, seed=2)
    da, _ = cKDTree(pb).query(pa); db, _ = cKDTree(pa).query(pb)
    d = np.concatenate([da, db]) / diag
    return {"mean": float(d.mean()), "p99": float(np.percentile(d, 99)), "max": float(d.max())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True); ap.add_argument("--raw", required=True)
    ap.add_argument("--targets", default="100000,60000,40000")
    a = ap.parse_args()
    run = Path(a.run); raw = run / a.raw
    ref = trimesh.load(raw, force="mesh")
    ms = ml.MeshSet()
    ply = run / "_raw.ply"; ref.export(ply)
    clean_ply = run / "clean_raw.ply"
    if clean_ply.exists():
        ms.load_new_mesh(str(clean_ply)); ply.unlink()
    else:
        ms.load_new_mesh(str(ply)); ply.unlink()
        clean(ms)
        ms.save_current_mesh(str(clean_ply))
    report = {"raw": topo(ref), "clean": None, "candidates": {}}
    report["clean"] = topo(trimesh.load(run / "clean_raw.ply"))
    base = ms.current_mesh_id()
    chosen = None
    for t in sorted((int(x) for x in a.targets.split(",")), reverse=True):
        # cascade: each level is reduced from the previous one (one expensive pass instead of N)
        ms.meshing_decimation_quadric_edge_collapse(targetfacenum=t, qualitythr=0.6, preserveboundary=True,
                                                    boundaryweight=1.0, preservenormal=True, preservetopology=False,
                                                    optimalplacement=True, planarquadric=True, planarweight=0.002,
                                                    autoclean=True)
        out = run / f"dec_{t}.ply"; ms.save_current_mesh(str(out))
        m = trimesh.load(out)
        r = {**topo(m), **{"err_" + k: v for k, v in deviation(ref, m).items()}}
        r["pass"] = r["err_mean"] < LIMIT_MEAN and r["err_p99"] < LIMIT_P99
        report["candidates"][t] = r
        print(t, json.dumps(r), flush=True)
        if r["pass"]: chosen = t
    report["chosen"] = chosen
    report["limits"] = {"mean": LIMIT_MEAN, "p99": LIMIT_P99}
    json.dump(report, open(run / "decimate_report.json", "w"), indent=1)
    print("CHOSEN", chosen)


if __name__ == "__main__":
    main()
