"""
Phase 3b: Constraint Mask Update (Hard 0 -> Soft 0.0001)
--------------------------------------------------------
This script reads the existing binary mask (0/1) and converts it 
to a float raster where:
- 1 (Suitable)  -> 1.0
- 0 (Unsuitable) -> 0.0001 (Very low priority, but not NoData)

This allows buildings to receive a computed score, but it will be 
drastically reduced by this factor.
"""

import rasterio
import numpy as np

INPUT_MASK = "/Users/sanyam/Desktop/GIS project /finalNormalizedData(afterPhase3)/Constraint_Mask.tif"
OUTPUT_MASK = "/Users/sanyam/Desktop/GIS project /finalNormalizedData(afterPhase3)/Constraint_Mask.tif"  # Overwriting the file (safe to do)

print(f"Reading {INPUT_MASK}...")

with rasterio.open(INPUT_MASK) as src:
    # Read the data
    mask_data = src.read(1)
    profile = src.profile.copy()

    # Create a new float array
    # We convert the integer mask to float32 to hold decimal values
    new_mask = mask_data.astype('float32')

    # TRANSFORM LOGIC:
    # Find everywhere that is currently 0, and make it 0.0001
    # We assume anything that isn't 0 is valid (1)
    new_mask[new_mask == 0] = 0.0001
    
    # Ensure valid areas are exactly 1.0
    new_mask[new_mask >= 1] = 1.0

    # Update metadata to ensure it saves as a decimal file (float32)
    profile.update(dtype='float32', nodata=None)

    print("Updating values...")
    print(f"Old unique values: {np.unique(mask_data)}")
    print(f"New unique values: {np.unique(new_mask)}")

    # Save
    with rasterio.open(OUTPUT_MASK, 'w', **profile) as dst:
        dst.write(new_mask, 1)

print(f"✅ Successfully updated {OUTPUT_MASK} to use 0.0001 instead of 0.")
print("You can now run Phase 4.")