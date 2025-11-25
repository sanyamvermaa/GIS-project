import rasterio
import numpy as np
import json

# === Load AHP weights ===
with open("uhi_weights.json") as f:
    weights = json.load(f)

print("Loaded weights:", weights)

# === Input rasters ===
layers = {
    "LST": "LST_norm.tif",
    "NDVI": "NDVI_norm.tif",
    "Population": "Population_norm.tif"
}

mask_path = "Constraint_Mask.tif"
output = "Final_UHI_Mitigation_Map.tif"

# === Load template raster ===
with rasterio.open(layers['LST']) as src:
    profile = src.profile
    base = src.read(1).astype('float32')
    final = np.zeros_like(base, dtype='float32')

# === Weighted overlay ===
for name, path in layers.items():
    print(f"Adding {name} with weight {weights[name]}")
    with rasterio.open(path) as src:
        data = src.read(1).astype('float32')
    final += data * float(weights[name])

# === Apply constraint mask ===
with rasterio.open(mask_path) as src:
    mask = src.read(1).astype('float32')

final = final * mask

# === Save final map ===
profile.update(dtype=rasterio.float32, compress='lzw')

with rasterio.open(output, 'w', **profile) as dst:
    dst.write(final, 1)

print("\n🎉 FINAL MAP CREATED:", output)
