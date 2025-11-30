import rasterio
import numpy as np

raster_path = "Final_Map_Clipped.tif"

with rasterio.open(raster_path) as src:
    band = src.read(1)   # read first band
    
    # Mask out NoData values
    if src.nodata is not None:
        data = band[band != src.nodata]
    else:
        data = band
    
    print("Raster Information")
    print("----------------------------")
    print("CRS:", src.crs)
    print("Bounds:", src.bounds)
    print("Width x Height:", src.width, "x", src.height)
    
    print("\nPixel Statistics")
    print("----------------------------")
    print("Min Pixel Value:", np.min(data))
    print("Max Pixel Value:", np.max(data))
    print("Mean Pixel Value:", np.mean(data))