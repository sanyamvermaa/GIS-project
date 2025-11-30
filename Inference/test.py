import rasterio
import numpy as np
import csv
import re
import ast 

# === Configuration ===
INPUT_MAP = "/Users/sanyam/Desktop/GIS project /finalOutput/Final_Map_Clipped.tif"
INPUT_LOCATIONS_FILE = "locations.txt"
OUTPUT_CSV = "UHI_Analysis_Results.csv"

def parse_chat_log(filename):
    """
    Reads a messy text file, extracts the JSON/Dict part from lines
    like '[Time] Name: {"Key": "Value"}', and returns a list of dicts.
    """
    clean_data = []
    
    print(f"📂 Reading locations from {filename}...")
    
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        line = line.strip()
        if not line: continue

        # Regex to find the part starting with { and ending with }
        match = re.search(r'(\{.*\})', line)
        
        if match:
            dict_str = match.group(1)
            try:
                # Fix for common broken quote error (e.g., "radius": "1000})
                if dict_str.endswith('"}') is False and dict_str.endswith('}') is True:
                     if dict_str[-2] != '"' and dict_str[-2].isdigit():
                         dict_str = dict_str[:-1] + '"}'

                data = ast.literal_eval(dict_str)
                clean_data.append(data)
            except Exception as e:
                print(f"⚠️  Skipping Line {i+1} (Syntax Error): {line}")
        else:
            print(f"⚠️  Skipping Line {i+1} (No data found): {line}")

    return clean_data

def analyze_location(src, name, lat, lon, radius_meters):
    """
    Performs the raster analysis for a single location.
    Returns a dictionary of results (Max and Avg only).
    """
    result = {
        "Name": name,
        "Lat": lat,
        "Lon": lon,
        "Radius_m": radius_meters,
        "Max_Score": None,
        "Avg_Score": None,
        "Status": "Error"
    }

    try:
        # 1. Convert Lat/Lon to Row/Col
        row, col = src.index(lon, lat)
    except IndexError:
        result["Status"] = "Out of Bounds"
        return result

    # 2. Calculate Radius in Pixels
    res_x = src.res[0] 
    degrees_per_meter = 1 / 111320 
    radius_deg = radius_meters * degrees_per_meter
    radius_pixels = int(radius_deg / res_x)
    if radius_pixels < 1: radius_pixels = 1

    # 3. Read Window
    row_start = max(0, row - radius_pixels)
    row_end = min(src.height, row + radius_pixels + 1)
    col_start = max(0, col - radius_pixels)
    col_end = min(src.width, col + radius_pixels + 1)

    window = rasterio.windows.Window.from_slices((row_start, row_end), (col_start, col_end))
    data = src.read(1, window=window)

    # 4. Analyze
    valid_data = data[data > 0.001] # Filter NoData

    if valid_data.size == 0:
        result["Status"] = "No Valid Data"
        return result

    # Calculate stats without thresholding
    result["Max_Score"] = round(float(np.max(valid_data)), 2)
    result["Avg_Score"] = round(float(np.median(valid_data)), 2)
    result["Status"] = "Success"

    return result

# === Main Execution ===
if __name__ == "__main__":
    # 1. Parse the input file
    locations = parse_chat_log(INPUT_LOCATIONS_FILE)
    
    if not locations:
        print("❌ No valid locations found to process.")
        exit()

    results_list = []

    # 2. Open Raster and Loop
    print(f"\n🌍 Processing {len(locations)} locations against {INPUT_MAP}...")
    
    try:
        with rasterio.open(INPUT_MAP) as src:
            for loc in locations:
                name = loc.get("Name", "Unknown")
                try:
                    lat = float(loc.get("Lat"))
                    lon = float(loc.get("Lon"))
                    rad = float(loc.get("radius", 500)) 
                except ValueError:
                    print(f"❌ Data Error for '{name}': Lat/Lon/Radius must be numbers.")
                    continue

                print(f"   -> Checking: {name}...")
                
                res = analyze_location(src, name, lat, lon, rad)
                results_list.append(res)
                
    except FileNotFoundError:
        print(f"❌ Error: Could not find map file: {INPUT_MAP}")
        exit()

    # 3. Save Results to CSV
    if results_list:
        keys = results_list[0].keys()
        with open(OUTPUT_CSV, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(results_list)
        
        print(f"\n✅ Processing Complete!")
        print(f"📊 Results saved to: {OUTPUT_CSV}")
        
        # Print a quick preview
        print("-" * 60)
        print(f"{'Location':<25}  | {'Avg Score':<10}")
        print("-" * 60)
        for r in results_list:
            if r['Status'] == 'Success':
                print(f"{r['Name']:<25} | {r['Avg_Score']:<10}")
        print("-" * 60)