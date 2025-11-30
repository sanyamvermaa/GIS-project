import rasterio
import numpy as np

INPUT_MAP = "/Users/sanyam/Desktop/GIS project /finalOutput/Final_Map_Clipped.tif"

with rasterio.open(INPUT_MAP) as src:
    data = src.read(1)
    
    # 1. Flatten the data and remove masked values (0 or 0.0001)
    # We only want to analyze the "Valid" urban pixels
    valid_pixels = data[data > 0.0001]  
    
    if valid_pixels.size == 0:
        print("Error: No valid data found.")
    else:
        # 2. Calculate Statistics
        mean_val = np.mean(valid_pixels)
        std_val = np.std(valid_pixels)
        
        # 3. Calculate Percentiles
        p90 = np.percentile(valid_pixels, 90) # Top 10%
        p95 = np.percentile(valid_pixels, 95) # Top 5% (The worst of the worst)
        p99 = np.percentile(valid_pixels, 99) # Top 1%
        
        print("-" * 30)
        print(f"📊 STATISTICS FOR {INPUT_MAP}")
        print("-" * 30)
        print(f"Minimum Value: {np.min(valid_pixels):.2f}")
        print(f"Maximum Value: {np.max(valid_pixels):.2f}")
        print(f"Mean (Average): {mean_val:.2f}")
        print("-" * 30)
        print("Recommended Hotspot Thresholds:")
        print(f"🔸 High Priority (>90th percentile):  {p90:.2f}")
        print(f"🚨 Critical (>95th percentile):       {p95:.2f}")
        print(f"🔥 Extreme (>99th percentile):        {p99:.2f}")
        print("-" * 30)