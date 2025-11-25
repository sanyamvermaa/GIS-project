"""
Urban Heat Island (UHI) Project
Phase 3: Normalization & Constraint Mask Creation
------------------------------------------------
This script:
1. Normalizes LST and NDVI rasters to a 1–10 scale
2. Creates a binary constraint mask from LULC
3. Saves outputs for AHP/Weighted Overlay analysis

Author: Sanyam Verma
Date: November 2025
"""

import rasterio
import numpy as np

# === Step 1: Define file paths ===
LST_PATH = "Bengaluru_LST_2024_CRS_Clean.tif"
NDVI_PATH = "Bengaluru_NDVI_2024_CRS_Clean.tif"
LULC_PATH = "Bengaluru_LULC_2024_Resampled_Clean.tif"

# === Step 2: Define normalization function ===
def normalize(array, inverse=False):
    """Normalize array values to a 1–10 scale."""
    arr = array.astype(float)
    arr_min, arr_max = np.nanmin(arr), np.nanmax(arr)
    norm = (arr - arr_min) / (arr_max - arr_min) * 9 + 1  # scale to 1–10
    if inverse:
        norm = 11 - norm  # flip scale if needed
    return np.clip(norm, 1, 10)

# === Step 3: Normalize LST (direct) ===
with rasterio.open(LST_PATH) as src:
    lst = src.read(1)
    profile = src.profile
lst_norm = normalize(lst)
with rasterio.open("LST_norm.tif", "w", **profile) as dst:
    dst.write(lst_norm.astype("float32"), 1)
print("✅ LST normalized → LST_norm.tif")

# === Step 4: Normalize NDVI (inverse: greener = cooler = lower score) ===
with rasterio.open(NDVI_PATH) as src:
    ndvi = src.read(1)
    profile = src.profile
ndvi_norm = normalize(ndvi, inverse=True)
with rasterio.open("NDVI_norm.tif", "w", **profile) as dst:
    dst.write(ndvi_norm.astype("float32"), 1)
print("✅ NDVI normalized (inverse) → NDVI_norm.tif")

# === Step 5: Create Constraint Mask from LULC ===
# Rule: Built-up (80) → 0, Water (50) → 0, others → 1
with rasterio.open(LULC_PATH) as src:
    lulc = src.read(1)
    profile = src.profile

mask = np.ones_like(lulc, dtype="uint8")
mask[(lulc == 50) | (lulc == 80)] = 0  # unsuitable
with rasterio.open("Constraint_Mask.tif", "w", **profile) as dst:
    dst.write(mask, 1)
print("✅ Constraint mask created → Constraint_Mask.tif")

# === Step 6: Quick checks ===
print("\n--- Verification ---")
print("LST_norm range:", np.nanmin(lst_norm), "to", np.nanmax(lst_norm))
print("NDVI_norm range:", np.nanmin(ndvi_norm), "to", np.nanmax(ndvi_norm))
print("Constraint mask unique values:", np.unique(mask))
print("\n🎯 Normalization & Mask creation complete.")
print("Next: Phase 4 → AHP Weighting & Weighted Overlay.")
