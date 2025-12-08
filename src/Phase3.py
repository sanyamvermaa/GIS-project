import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import numpy as np

# Paths
pop_path = "bengaluru_pop_100m_epsg4326.tif"
template_path = "LST_norm.tif"      # 30 m template
output_path = "Population_norm.tif"

# Load template (for CRS, transform, shape)
with rasterio.open(template_path) as t:
    template_meta = t.meta.copy()
    template_transform = t.transform
    template_crs = t.crs
    template_shape = (t.height, t.width)

# Read and resample population raster to match template
with rasterio.open(pop_path) as src:
    pop_data = src.read(1)
    pop_meta = src.meta.copy()

    resampled = np.zeros(template_shape, dtype='float32')

    reproject(
        source=pop_data,
        destination=resampled,
        src_transform=src.transform,
        src_crs=src.crs,
        dst_transform=template_transform,
        dst_crs=template_crs,
        resampling=Resampling.bilinear
    )

# Normalize to 1–10 scale
arr = resampled.astype(float)
arr[arr < 0] = 0  # safety
valid = arr[arr > 0]

if valid.size > 0:
    mn = valid.min()
    mx = valid.max()
    norm = (arr - mn) / (mx - mn) * 9 + 1
    norm = np.clip(norm, 1, 10)
else:
    norm = arr

# Save Population_norm.tif
template_meta.update(dtype='float32', compress='lzw')

with rasterio.open(output_path, 'w', **template_meta) as dst:
    dst.write(norm.astype('float32'), 1)

print("Population_norm.tif created successfully!")
