"""
Phase 6: Point Query & Radius Check
-----------------------------------
This script allows you to input a Latitude/Longitude coordinate 
(e.g., a specific Ward location) and a search radius (in meters).

It checks the 'Final_UHI_Mitigation_Map_Hybrid.tif' to see if 
any pixels within that radius have a score > 4 (High Priority).

Usage:
    Run the script and follow the prompts.
"""

import rasterio
import numpy as np
import math

# === Configuration ===
INPUT_MAP = "Final_Map_Clipped.tif"
THRESHOLD_SCORE = 6.0  # The value you are looking for

def check_location(lat, lon, radius_meters):
    print(f"\n--- Checking Location: {lat}, {lon} (Radius: {radius_meters}m) ---")
    
    with rasterio.open(INPUT_MAP) as src:
        # 1. Convert Lat/Lon to Raster Coordinate System (Row/Col)
        # Note: src.index() works for EPSG:4326 files automatically
        try:
            row, col = src.index(lon, lat)
        except IndexError:
            print("❌ Error: These coordinates are outside the map boundary!")
            return

        # 2. Calculate Radius in Pixels
        # Get resolution in degrees (approximate)
        # 1 degree lat approx = 111,320 meters
        res_x = src.res[0] # Pixel width in degrees
        degrees_per_meter = 1 / 111320 
        
        # Convert search radius (meters) -> radius (degrees) -> radius (pixels)
        radius_deg = radius_meters * degrees_per_meter
        radius_pixels = int(radius_deg / res_x)
        
        # Ensure at least 1 pixel is checked
        if radius_pixels < 1: radius_pixels = 1
        
        print(f"ℹ️ Search Window: +/- {radius_pixels} pixels around center.")

        # 3. Read the Window of Data
        # We calculate the start/end rows and cols, clamping to image boundaries
        row_start = max(0, row - radius_pixels)
        row_end = min(src.height, row + radius_pixels + 1)
        col_start = max(0, col - radius_pixels)
        col_end = min(src.width, col + radius_pixels + 1)

        # Read specific window (much faster than reading whole file)
        window = rasterio.windows.Window.from_slices((row_start, row_end), (col_start, col_end))
        data = src.read(1, window=window)

        # 4. Analyze the Data
        # Filter out NoData or masked values (usually 0 or very small)
        valid_data = data[data > 0.001] 

        if valid_data.size == 0:
            print("⚠️ Area contains no valid data (likely outside boundary or masked).")
            return

        max_score = np.max(valid_data)
        avg_score = np.mean(valid_data)
        
        # Count how many pixels exceed threshold
        high_priority_pixels = valid_data[valid_data > THRESHOLD_SCORE]
        count = high_priority_pixels.size

        # 5. Report Results
        print("\n📊 RESULTS:")
        print(f"   Max Score Found: {max_score:.2f}")
        print(f"   Avg Score in Radius: {avg_score:.2f}")
        
        
# === Interactive Run Section ===
if __name__ == "__main__":
    # Example coordinates (Center of Bengaluru roughly)
    # You can change these or use input()
    print("Please enter coordinates:")
    try:
        in_lat = float(input("Enter Latitude (e.g., 12.9716): "))
        in_lon = float(input("Enter Longitude (e.g., 77.5946): "))
        in_rad = float(input("Enter Search Radius in meters (e.g., 500): "))
        
        check_location(in_lat, in_lon, in_rad)
        
    except ValueError:
        print("Invalid number entered. Please restart.")