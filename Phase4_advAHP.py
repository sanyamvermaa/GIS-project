"""
Phase4_Advanced_AHP.py

Features:
- Compute AHP weights from pairwise comparisons (numpy eigenvector) + CR
- Compute Entropy weights from normalized rasters (data-driven)
- Combine weights: hybrid = alpha*AHP + (1-alpha)*Entropy
- Monte Carlo sensitivity: perturb pairwise matrix, recompute AHP, combine, produce ensemble overlays
- Save outputs:
   - uhi_weights_combined.json
   - weight_ensemble_stats.csv
   - Final_UHI_Ensemble_mean.tif
   - Final_UHI_Ensemble_std.tif

Requirements:
pip install numpy rasterio pandas scipy
"""

import json
import math
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
import pandas as pd
from scipy.linalg import eig
import os
import sys
from datetime import datetime

# ========== CONFIG ==========
CRITERIA = ["LST", "NDVI", "Population"]   # adjust if needed
# Pairwise comparisons dictionary: (i,j) -> value meaning i/j = value
# Example for 3 criteria: LST vs NDVI = 3 means LST is 3x more important than NDVI
PAIRWISE = {
    ("LST", "NDVI"): 3.0,
    ("LST", "Population"): 2.0,
    ("NDVI", "Population"): 0.5
}
ALPHA = 0.7   # weight to give to AHP; hybrid = alpha*AHP + (1-alpha)*Entropy
# file paths (must exist)
LST_PATH = "LST_norm.tif"
NDVI_PATH = "NDVI_norm.tif"
POP_PATH = "Population_norm.tif"
MASK_PATH = "Constraint_Mask.tif"   # used to exclude masked pixels in entropy
OUTPUT_DIR = "."
# Monte Carlo settings
MC_SAMPLES = 150        # number of perturbed AHP matrices to sample (reduce if slow)
PERTURB_SIGMA = 0.12    # standard deviation of log-normal multiplicative noise on pairwise values
ENTROPY_SAMPLE_SIZE = None   # None = use all pixels; or int (e.g., 200000) to sample for entropy
# ============================

# Helper: build full pairwise matrix from PAIRWISE dictionary
def build_pairwise_matrix(criteria, comparisons):
    n = len(criteria)
    M = np.ones((n, n), dtype=float)
    idx = {c: i for i, c in enumerate(criteria)}
    # fill from comparisons (assume reciprocal if not given)
    for (a, b), v in comparisons.items():
        i, j = idx[a], idx[b]
        M[i, j] = float(v)
        M[j, i] = 1.0 / float(v)
    return M

# Compute principal eigenvector (normalized) -> AHP weights
def ahp_weights_from_matrix(M):
    # power method or eigen decomposition
    vals, vecs = eig(M)
    # eigenvalues may be complex due to numeric error; take real parts
    eigvals = np.real(vals)
    eigvecs = np.real(vecs)
    # principal eigenvector = eigenvector of max eigenvalue
    idx = np.argmax(eigvals)
    w = eigvecs[:, idx]
    w = np.abs(w)
    w = w / np.sum(w)
    lambda_max = eigvals[idx]
    return w, float(lambda_max)

# Consistency Ratio (CR) calculation
def consistency_ratio(M, lambda_max):
    n = M.shape[0]
    CI = (lambda_max - n) / (n - 1) if n > 1 else 0.0
    # Random Index RI table (Saaty) for n = 1..10
    RI_table = {1:0.00, 2:0.00, 3:0.58, 4:0.90, 5:1.12, 6:1.24, 7:1.32, 8:1.41, 9:1.45, 10:1.49}
    RI = RI_table.get(n, 1.49)
    CR = CI / RI if RI != 0 else 0.0
    return CI, CR

# Read rasters aligned to a template raster (LST)
def read_and_align_rasters(template_path, paths, mask_path=None):
    with rasterio.open(template_path) as t:
        template_meta = t.meta.copy()
        template_transform = t.transform
        template_crs = t.crs
        template_shape = (t.height, t.width)
    arrays = []
    for p in paths:
        if not os.path.exists(p):
            raise FileNotFoundError(p)
        with rasterio.open(p) as src:
            dst = np.zeros(template_shape, dtype='float32')
            reproject(
                source=src.read(1),
                destination=dst,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=template_transform,
                dst_crs=template_crs,
                resampling=Resampling.bilinear
            )
            arrays.append(dst)
    mask = None
    if mask_path and os.path.exists(mask_path):
        with rasterio.open(mask_path) as src:
            mask_arr = np.zeros(template_shape, dtype='float32')
            reproject(
                source=src.read(1),
                destination=mask_arr,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=template_transform,
                dst_crs=template_crs,
                resampling=Resampling.nearest
            )
            mask = mask_arr
    return arrays, template_meta, mask

# Entropy weighting (classic) across alternatives = pixels
def entropy_weights_from_arrays(arrays, mask=None, sample_size=None):
    # arrays: list of 2D arrays (same shape)
    # flatten and remove masked pixels (mask==0)
    shape = arrays[0].shape
    n_pix = shape[0]*shape[1]
    stacked = np.stack([a.flatten() for a in arrays], axis=1)  # shape (n_pix, n_criteria)
    if mask is not None:
        mask_flat = mask.flatten()
        valid_idx = np.where(mask_flat != 0)[0]
        if sample_size:
            if valid_idx.size > sample_size:
                valid_idx = np.random.choice(valid_idx, size=sample_size, replace=False)
    else:
        valid_idx = np.arange(n_pix)
        if sample_size and valid_idx.size > sample_size:
            valid_idx = np.random.choice(valid_idx, size=sample_size, replace=False)
    data = stacked[valid_idx, :].astype(float)
    # ensure non-negative and shift if needed
    data[data < 0] = 0.0
    # avoid all-zero columns
    col_sums = data.sum(axis=0)
    # if any column sums are zero, add tiny epsilon
    col_sums[col_sums == 0] = 1e-12
    P = data / col_sums  # p_ij where sum_i p_ij = 1
    # avoid log(0)
    eps = 1e-12
    P_safe = np.where(P <= 0, eps, P)
    m = P.shape[0]
    k = 1.0 / math.log(m)
    e = -k * np.sum(P * np.log(P_safe), axis=0)
    d = 1 - e
    w = d / np.sum(d)
    return np.array(w)

# Weighted overlay given weight vector and raster arrays
def overlay_weighted(arrays, weights):
    out = np.zeros_like(arrays[0], dtype='float32')
    for w, arr in zip(weights, arrays):
        out += arr * float(w)
    return out

# Save raster
def save_raster(path, arr, meta):
    out_meta = meta.copy()
    out_meta.update(dtype='float32', count=1, compress='lzw')
    with rasterio.open(path, 'w', **out_meta) as dst:
        dst.write(arr.astype('float32'), 1)

# Monte Carlo: perturb pairwise matrix values multiplicatively (lognormal noise)
def perturb_pairwise_matrix(base_matrix, sigma=0.12):
    # base_matrix is full reciprocal matrix with diag=1
    n = base_matrix.shape[0]
    M = base_matrix.copy()
    for i in range(n):
        for j in range(i+1, n):
            base = M[i,j]
            noise = math.exp(np.random.normal(loc=0.0, scale=sigma))  # multiplicative >0
            new = base * noise
            M[i,j] = new
            M[j,i] = 1.0 / new
    # diag keep 1
    np.fill_diagonal(M, 1.0)
    return M

# Main run
def main():
    print("Phase4_Advanced_AHP started:", datetime.now())
    criteria = CRITERIA
    # 1. Build baseline AHP matrix
    base_M = build_pairwise_matrix(criteria, PAIRWISE)
    w_ahp, lambda_max = ahp_weights_from_matrix(base_M)
    CI, CR = consistency_ratio(base_M, lambda_max)
    print("Baseline AHP weights:", dict(zip(criteria, w_ahp)))
    print("Lambda_max:", lambda_max, "CI:", CI, "CR:", CR)
    if CR > 0.1:
        print("Warning: Consistency Ratio > 0.1 (consider revising pairwise judgments)")

    # 2. Read rasters and align
    rasters, meta, mask = read_and_align_rasters(LST_PATH, [LST_PATH, NDVI_PATH, POP_PATH], MASK_PATH)
    # order: LST, NDVI, POP (should match CRITERIA order)
    # 3. Entropy weights
    print("Computing entropy weights (may sample pixels to save memory)...")
    ent_w = entropy_weights_from_arrays(rasters, mask=mask, sample_size=ENTROPY_SAMPLE_SIZE)
    print("Entropy weights:", dict(zip(criteria, ent_w)))

    # 4. Combined baseline weights
    combined = ALPHA * w_ahp + (1.0 - ALPHA) * ent_w
    combined = combined / combined.sum()
    print("Combined (hybrid) weights:", dict(zip(criteria, combined)))

    # Save baseline weights
    out_weights = {
        "AHP_weights": dict(zip(criteria, w_ahp.tolist())),
        "Entropy_weights": dict(zip(criteria, ent_w.tolist())),
        "Combined_weights": dict(zip(criteria, combined.tolist())),
        "consistency": {"lambda_max": lambda_max, "CI": CI, "CR": CR},
        "meta": {"alpha": ALPHA}
    }
    with open(os.path.join(OUTPUT_DIR, "uhi_weights_combined.json"), "w") as f:
        json.dump(out_weights, f, indent=2)
    print("Saved combined weights to uhi_weights_combined.json")

    # 5. Monte Carlo ensemble (sensitivity)
    print(f"Running Monte Carlo with {MC_SAMPLES} samples (sigma={PERTURB_SIGMA})...")
    mean_overlay = None
    sq_overlay = None
    weights_records = []
    base_full = base_M
    for k in range(MC_SAMPLES):
        M_pert = perturb_pairwise_matrix(base_full, sigma=PERTURB_SIGMA)
        w_k, lam = ahp_weights_from_matrix(M_pert)
        # compute combined
        comb_k = ALPHA * w_k + (1.0 - ALPHA) * ent_w
        comb_k = comb_k / comb_k.sum()
        # compute overlay
        out_k = overlay_weighted(rasters, comb_k)
        # apply mask (mask==0 -> 0)
        if mask is not None:
            out_k = out_k * (mask != 0)
        if mean_overlay is None:
            mean_overlay = np.zeros_like(out_k, dtype='float64')
            sq_overlay = np.zeros_like(out_k, dtype='float64')
        mean_overlay += out_k
        sq_overlay += out_k*out_k
        weights_records.append(dict(zip(criteria, comb_k.tolist())))
        if (k+1) % 25 == 0:
            print(f"MC sample {k+1}/{MC_SAMPLES}...")
    mean_overlay /= float(MC_SAMPLES)
    var_overlay = (sq_overlay / float(MC_SAMPLES)) - (mean_overlay*mean_overlay)
    std_overlay = np.sqrt(np.maximum(var_overlay, 0.0))

    # Save ensemble statistics raster
    mean_path = os.path.join(OUTPUT_DIR, "Final_UHI_Ensemble_mean.tif")
    std_path = os.path.join(OUTPUT_DIR, "Final_UHI_Ensemble_std.tif")
    save_raster(mean_path, mean_overlay.astype('float32'), meta)
    save_raster(std_path, std_overlay.astype('float32'), meta)
    print("Saved mean/std ensemble rasters:", mean_path, std_path)

    # Save weight ensemble CSV summary (mean, std per criterion)
    dfw = pd.DataFrame(weights_records)
    stats = dfw.agg(['mean', 'std']).transpose().reset_index().rename(columns={'index':'criterion'})
    stats.to_csv(os.path.join(OUTPUT_DIR, "weight_ensemble_stats.csv"), index=False)
    # Also save the full weight draws if desired
    dfw.to_csv(os.path.join(OUTPUT_DIR, "weight_ensemble_draws.csv"), index=False)
    print("Saved weight ensemble stats and draws.")

    # Also save one final map using baseline combined weights (for usual use)
    final_map_path = os.path.join(OUTPUT_DIR, "Final_UHI_Mitigation_Map_Hybrid.tif")
    final_map = overlay_weighted(rasters, combined)
    if mask is not None:
        final_map = final_map * (mask != 0)
    save_raster(final_map_path, final_map.astype('float32'), meta)
    print("Saved baseline hybrid final map:", final_map_path)
    print("Phase4_Advanced_AHP finished:", datetime.now())

if __name__ == "__main__":
    main()
