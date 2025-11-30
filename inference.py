"""
analyze_uhi_tif_files.py
ADVANCED ANALYSIS OF 3 FINAL UHI GEOTIFF FILES
(0 VALUES ARE IGNORED IN ALL METRICS)
"""

import rasterio
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("ADVANCED TIF FILE ANALYSIS - UHI FINAL OUTPUTS (0-values ignored)")
print("=" * 80)

# ---------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------
HYBRID_PATH = "Final_Map_Clipped.tif"
MEAN_PATH   = "/Users/sanyam/Desktop/GIS project /finalOutput/Final_UHI_Ensemble_mean.tif"
STD_PATH    = "/Users/sanyam/Desktop/GIS project /finalOutput/Final_UHI_Ensemble_std.tif"

OUTPUT_DIR   = "."
PIXEL_SIZE_M = 30           # adjust if different
PIXEL_AREA_KM2 = (PIXEL_SIZE_M ** 2) / (1000 ** 2)

# ---------------------------------------------------------------------
# PHASE 1: LOAD ALL 3 MAPS
# ---------------------------------------------------------------------
print("\n[PHASE 1/6] Loading 3 GeoTIFF files...")

try:
    with rasterio.open(HYBRID_PATH) as src:
        hybrid_map  = src.read(1)
        hybrid_meta = src.meta
    print(f"    ✓ Loaded: {HYBRID_PATH}")
except FileNotFoundError:
    print(f"    ✗ ERROR: {HYBRID_PATH} not found")
    exit(1)

try:
    with rasterio.open(MEAN_PATH) as src:
        mean_map = src.read(1)
    print(f"    ✓ Loaded: {MEAN_PATH}")
except FileNotFoundError:
    print(f"    ⚠ Warning: {MEAN_PATH} not found")
    mean_map = None

try:
    with rasterio.open(STD_PATH) as src:
        std_map = src.read(1)
    print(f"    ✓ Loaded: {STD_PATH}")
except FileNotFoundError:
    print(f"    ⚠ Warning: {STD_PATH} not found")
    std_map = None

# ---------------------------------------------------------------------
# PHASE 2: HYBRID MAP ANALYSIS (0-values ignored)
# ---------------------------------------------------------------------
print("\n[PHASE 2/6] Analyzing Hybrid UHI Map (non-zero pixels only)...")

# valid where not NaN AND not 0
valid_mask_hybrid = (~np.isnan(hybrid_map)) & (hybrid_map != 0)
valid_hybrid      = hybrid_map[valid_mask_hybrid]

total_pixels = hybrid_map.size
valid_pixels = valid_hybrid.size
invalid_pixels = total_pixels - valid_pixels

# TOTAL AREA CONSIDERED (only non-zero pixels)
total_area_km2 = valid_pixels * PIXEL_AREA_KM2
total_area_m2  = total_area_km2 * 1_000_000
total_area_ha  = total_area_km2 * 100
total_area_ac  = total_area_km2 * 247.105

hybrid_stats = {
    'Total_Pixels': total_pixels,
    'Valid_Pixels': valid_hybrid.size,
    'Min':  np.nanmin(valid_hybrid),
    'Max':  np.nanmax(valid_hybrid),
    'Mean': np.nanmean(valid_hybrid),
    'Median': np.nanmedian(valid_hybrid),
    'Std_Dev': np.nanstd(valid_hybrid),
    'Total_Area_km2': total_area_km2,
}

print("    Hybrid Map Statistics (value != 0):")
for key, val in hybrid_stats.items():
    if isinstance(val, float):
        print(f"      {key:.<25} {val:.6f}")
    else:
        print(f"      {key:.<25} {val:,}")

print("\n    TOTAL AREA CONSIDERED (non-zero pixels only):")
print(f"      Pixels used:.............. {valid_pixels:,} of {total_pixels:,}")
print(f"      Area:..................... {total_area_km2:,.2f} km²")
print(f"                                {total_area_m2:,.0f} m²")
print(f"                                {total_area_ha:,.0f} hectares")
print(f"                                {total_area_ac:,.0f} acres")

# ---------------------------------------------------------------------
# PHASE 3: MAP COMPARISON (0-values ignored in both)
# ---------------------------------------------------------------------
print("\n[PHASE 3/6] Comparing Hybrid vs Ensemble Mean (non-zero only)...")

pearson_r = None
pct_agree_10 = None

if mean_map is not None:
    valid_idx = (~np.isnan(hybrid_map)) & (~np.isnan(mean_map)) & \
                (hybrid_map != 0) & (mean_map != 0)

    hybrid_flat = hybrid_map[valid_idx]
    mean_flat   = mean_map[valid_idx]

    pearson_r, pearson_p   = pearsonr(hybrid_flat, mean_flat)
    spearman_r, spearman_p = spearmanr(hybrid_flat, mean_flat)

    diff_map  = np.abs(hybrid_flat - mean_flat)
    mean_diff = np.mean(diff_map)
    max_diff  = np.max(diff_map)
    pct_agree_10 = np.sum(diff_map < 0.1) / len(diff_map) * 100

    print("    Correlation Analysis (valid & non-zero pixels):")
    print(f"      Pearson r:..................... {pearson_r:.6f}")
    print(f"      Spearman r:................... {spearman_r:.6f}")
    print(f"      Mean abs diff:................ {mean_diff:.6f}")
    print(f"      Max  abs diff:................ {max_diff:.6f}")
    print(f"      % of pixels agreeing (<0.1):.. {pct_agree_10:.2f}%")

    if pearson_r > 0.95:
        print("      ✓ EXCELLENT agreement")
    elif pearson_r > 0.90:
        print("      ✓ GOOD agreement")
    else:
        print("      ⚠ Moderate agreement")

# ---------------------------------------------------------------------
# PHASE 4: UNCERTAINTY ANALYSIS (0-values ignored)
# ---------------------------------------------------------------------
print("\n[PHASE 4/6] Analyzing Ensemble Uncertainty (non-zero only)...")

if std_map is not None:
    valid_mask_std = (~np.isnan(std_map)) & (std_map != 0)
    valid_std      = std_map[valid_mask_std]

    std_stats = {
        'Mean_Uncertainty':   np.nanmean(valid_std),
        'Median_Uncertainty': np.nanmedian(valid_std),
    }

    print("    Uncertainty Statistics (value != 0):")
    for key, val in std_stats.items():
        print(f"      {key:.<30} {val:.6f}")

    p33 = np.nanpercentile(valid_std, 33)
    p67 = np.nanpercentile(valid_std, 67)

    high_conf = np.sum(valid_std < p33) / valid_std.size * 100   # low std
    med_conf  = np.sum((valid_std >= p33) & (valid_std < p67)) / valid_std.size * 100
    low_conf  = np.sum(valid_std >= p67) / valid_std.size * 100  # high std

    print("    Confidence Distribution (non-zero pixels):")
    print(f"      High Confidence:.... {high_conf:.2f}%")
    print(f"      Medium Confidence:.. {med_conf:.2f}%")
    print(f"      Low Confidence:..... {low_conf:.2f}%")

# ---------------------------------------------------------------------
# PHASE 5: HOTSPOT ANALYSIS (0-values ignored)
# ---------------------------------------------------------------------
print("\n[PHASE 5/6] Cross-Map Hotspot Validation (non-zero only)...")

percentiles = [90, 95, 99]
hotspot_data = []

for pct in percentiles:
    threshold = np.nanpercentile(valid_hybrid, pct)
    hotspot_pixels = np.sum(valid_hybrid >= threshold)
    hotspot_area_km2 = hotspot_pixels * PIXEL_AREA_KM2

    hotspot_data.append({
        'Percentile': f"Top {100 - pct}%",
        'Threshold': threshold,
        'Pixels': hotspot_pixels,
        'Area_km2': hotspot_area_km2,
    })

    print(f"    Top {100 - pct}%: {hotspot_area_km2:.2f} km² (threshold = {threshold:.4f})")

hotspot_df  = pd.DataFrame(hotspot_data)
hotspot_csv = f"{OUTPUT_DIR}/06_Cross_Map_Hotspot_Validation.csv"
hotspot_df.to_csv(hotspot_csv, index=False)
print(f"    ✓ Saved: {hotspot_csv}")

# ---------------------------------------------------------------------
# PHASE 6: FINAL SUMMARY
# ---------------------------------------------------------------------
print("\n[PHASE 6/6] Analysis Complete!")

print("\n" + "=" * 80)
print("✅ ANALYSIS COMPLETE (0-values ignored; total area reported)")
print("=" * 80)
print("\nGenerated Files:")
print("  ✓ 06_Cross_Map_Hotspot_Validation.csv")
print("=" * 80)