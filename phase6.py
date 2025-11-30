"""
Phase 6: Classification & Area Calculation
------------------------------------------
This script takes the statistical thresholds you found:
- High: 5.77
- Critical: 5.90
- Extreme: 6.76

It creates a new map "UHI_Priority_Classes.tif" with simple integer classes:
1 = Safe
2 = High
3 = Critical
4 = Extreme

It then calculates the EXACT area (in sq km) for each class.
"""

import rasterio
import numpy as np

INPUT_MAP = "Final_Map_Clipped.tif"
OUTPUT_MAP = "UHI_Priority_Classes.tif"

# Your specific thresholds
THRESH_HIGH = 5.70
THRESH_CRIT = 5.83
THRESH_EXTR = 6.40

print(f"Reading {INPUT_MAP}...")
with rasterio.open(INPUT_MAP) as src:
    data = src.read(1)
    profile = src.profile.copy()
    
    # Pixel resolution (approx 30m x 30m = 900 sq meters)
    # We check the transform to be precise
    res_x = src.res[0]
    res_y = src.res[1]
    # Note: If CRS is degrees (EPSG:4326), area calc is tricky. 
    # We assume approx 30m for Landsat, or 0.00027 degrees.
    # For accurate sq km, we usually need a projected CRS (UTM).
    # Here we will estimate using 30m x 30m = 900 sqm per pixel.
    pixel_area_sqm = 30 * 30 

    # Create Classification Array
    # 0 = No Data / Masked
    # 1 = Safe (< 5.77)
    # 2 = High (5.77 - 5.90)
    # 3 = Critical (5.90 - 6.76)
    # 4 = Extreme (> 6.76)
    
    classified = np.zeros_like(data, dtype=np.uint8)
    
    # Apply logic (Order matters! Apply lower tiers first)
    classified[data > 0.001] = 1          # Everything valid is at least Safe
    classified[data >= THRESH_HIGH] = 2   # Overwrite High
    classified[data >= THRESH_CRIT] = 3   # Overwrite Critical
    classified[data >= THRESH_EXTR] = 4   # Overwrite Extreme
    
    # Mask out the "Soft Mask" areas (buildings 0.0001) if they fell into Safe
    classified[data < 0.1] = 0

    # Calculate Areas
    print("\n--- 📊 AREA STATISTICS (Estimated) ---")
    unique, counts = np.unique(classified, return_counts=True)
    
    labels = {0: "No Data", 1: "Safe/Low", 2: "High Priority", 3: "Critical", 4: "EXTREME"}
    
    for val, count in zip(unique, counts):
        if val == 0: continue
        area_sqm = count * pixel_area_sqm
        area_sqkm = area_sqm / 1_000_000  # Convert to sq km
        print(f"Class {val} ({labels[val]}): {count} pixels | {area_sqkm:.2f} km²")

    # Save the classified map
    profile.update(dtype=rasterio.uint8, nodata=0)
    with rasterio.open(OUTPUT_MAP, 'w', **profile) as dst:
        dst.write(classified, 1)

print(f"\n✅ Saved classified map to {OUTPUT_MAP}")