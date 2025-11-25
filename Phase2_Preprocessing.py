"""
Urban Heat Island (UHI) Project
Phase 2: Preprocessing & Data Alignment
---------------------------------------
This script:
1. Assigns CRS to Landsat LST & NDVI GeoTIFFs (EPSG:4326)
2. Resamples LULC GeoTIFF to 30m (to match LST/NDVI)
3. Cleans NaN / no-data pixels
4. Prints diagnostic summary

Author: Sanyam Verma
Date: November 2025
"""

# === Imports ===
import rasterio
from rasterio.enums import Resampling
import numpy as np
import os

# === Step 0: Define file paths ===
# Make sure these are in the same folder as this script
LST_PATH = "Bengaluru_LST_2024.tif"
NDVI_PATH = "Bengaluru_NDVI_2024.tif"
LULC_PATH = "Bengaluru_LULC_2024.tif"

# === Step 1: Assign CRS to LST and NDVI ===
def assign_crs(input_path, output_path, crs_code="EPSG:4326"):
    with rasterio.open(input_path) as src:
        profile = src.profile
        data = src.read(1)
        profile.update(crs=crs_code)

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(data, 1)
    print(f"✅ CRS {crs_code} assigned to {output_path}")

assign_crs(LST_PATH, "Bengaluru_LST_2024_CRS.tif")
assign_crs(NDVI_PATH, "Bengaluru_NDVI_2024_CRS.tif")

# === Step 2: Resample LULC to match LST resolution (30 m) ===
def resample_raster(input_path, reference_path, output_path):
    with rasterio.open(reference_path) as ref:
        new_transform = ref.transform
        new_crs = ref.crs
        new_shape = (ref.height, ref.width)

    with rasterio.open(input_path) as src:
        data = src.read(
            out_shape=(src.count, new_shape[0], new_shape[1]),
            resampling=Resampling.nearest
        )
        profile = src.profile
        profile.update({
            'transform': new_transform,
            'crs': new_crs,
            'height': new_shape[0],
            'width': new_shape[1]
        })

    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(data)
    print(f"✅ Resampled {input_path} → {output_path}")

resample_raster(
    LULC_PATH,
    "Bengaluru_LST_2024_CRS.tif",
    "Bengaluru_LULC_2024_Resampled.tif"
)

# === Step 3: Clean NaN / No-Data pixels ===
def clean_nodata(input_path, output_path):
    with rasterio.open(input_path) as src:
        data = src.read(1)
        data = np.nan_to_num(data, nan=0)
        profile = src.profile

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(data, 1)
    print(f"✅ Cleaned no-data pixels in {output_path}")

for f in [
    "Bengaluru_LST_2024_CRS.tif",
    "Bengaluru_NDVI_2024_CRS.tif",
    "Bengaluru_LULC_2024_Resampled.tif"
]:
    clean_nodata(f, f.replace(".tif", "_Clean.tif"))

# === Step 4: Diagnostics — Check alignment and stats ===
def check_stats(files):
    for f in files:
        with rasterio.open(f) as src:
            data = src.read(1, masked=True)
            print("\n---", os.path.basename(f), "---")
            print("CRS:", src.crs)
            print("Resolution:", src.res)
            print("Shape (rows, cols):", (src.height, src.width))
            print("Data type:", data.dtype)
            print("Min:", np.nanmin(data), "Max:", np.nanmax(data))

check_stats([
    "Bengaluru_LST_2024_CRS_Clean.tif",
    "Bengaluru_NDVI_2024_CRS_Clean.tif",
    "Bengaluru_LULC_2024_Resampled_Clean.tif"
])

print("\n🎯 All files aligned and cleaned successfully.")
print("✅ You can now move to Phase 3: Normalization & Mask Creation.")
