import rasterio
import geopandas as gpd
from rasterio.mask import mask

# 1. Load the Shapefile ("The Cookie Cutter")
aoi = gpd.read_file("/Users/sanyam/Desktop/GIS project /IntialData/Intiial dataset/Bengaluru_AOI.geojson")

# 2. Open the Map & Clip It
with rasterio.open("/Users/sanyam/Desktop/GIS project /finalOutput/Final_UHI_Ensemble_mean.tif") as src:
    # This one line does the actual clipping!
    out_image, out_transform = mask(src, aoi.geometry, crop=True)
    out_meta = src.meta.copy()

# 3. Save the Result
out_meta.update({
    "height": out_image.shape[1],
    "width": out_image.shape[2],
    "transform": out_transform
})

with rasterio.open("EnsembLeMeanClipped.tif", "w", **out_meta) as dest:
    dest.write(out_image)

print("✅ Clipped map saved!")