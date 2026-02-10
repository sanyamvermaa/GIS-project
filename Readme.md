```text
Urban Heat Island (UHI) Mitigation Suitability Analysis - Bengaluru

This project utilizes a Hybrid Multi-Criteria Decision Making (MCDM) approach combined with Monte Carlo Simulation to identify priority areas for Urban Heat Island mitigation in Bengaluru Urban. The analysis integrates satellite imagery (LST, NDVI), demographic data (Population), and land use data to produce scientifically robust suitability maps.

📂 Project Directory Structure

📦 GIS Project Root
 ┣ 📂 IntialData (Raw Inputs)
 ┃ ┣ 📜 Bengaluru_AOI.geojson          # Study area boundary
 ┃ ┣ 📜 Bengaluru_LST_2024.tif         # Land Surface Temperature (Landsat 8)
 ┃ ┣ 📜 Bengaluru_NDVI_2024.tif        # Vegetation Index (Landsat 8)
 ┃ ┣ 📜 Bengaluru_LULC_2024.tif        # Land Use Land Cover (ESA)
 ┃ ┗ 📜 bengaluru_pop_100m_epsg4326.tif # Population Density (WorldPop)
 ┃
 ┣ 📂 ppdData (Preprocessed - After Phase 2)
 ┃ ┣ 📜 Bengaluru_LST_2024_CRS_Clean.tif
 ┃ ┣ 📜 Bengaluru_LULC_2024_Resampled_Clean.tif
 ┃ ┗ 📜 ... (Other aligned/cleaned rasters)
 ┃
 ┣ 📂 finalNormalizedData (After Phase 3)
 ┃ ┣ 📜 LST_norm.tif                   # Normalized Temp (1-10)
 ┃ ┣ 📜 NDVI_norm.tif                  # Normalized Vegetation (1-10)
 ┃ ┣ 📜 Population_norm.tif            # Normalized Population (1-10)
 ┃ ┗ 📜 Constraint_Mask.tif            # Soft mask (1.0 = Suitable, 0.0001 = Restricted)
 ┃
 ┣ 📂 finalOutput (Results - After Phase 4/5)
 ┃ ┣ 📜 Final_UHI_Mitigation_Map_Hybrid.tif  # MAIN RESULT (Priority Map)
 ┃ ┣ 📜 Final_UHI_Ensemble_mean.tif          # Monte Carlo Average
 ┃ ┣ 📜 Final_UHI_Ensemble_std.tif           # Uncertainty/Confidence Map
 ┃ ┣ 📜 uhi_weights_combined.json            # Calculated Weights & Consistency Ratio
 ┃ ┗ 📜 weight_ensemble_stats.csv            # Monte Carlo Statistics
 ┃
 ┣ 📜 Phase2_Preprocessing.py    # Aligns CRS, Resamples to 30m grid
 ┣ 📜 Phase3_Normalization.py    # Scales data to 1-10 range
 ┣ 📜 Phase3_Pop_Normalize.py    # Handles Population raster specifics
 ┣ 📜 phase3b_updatemask.py      # Creates soft mask (0 -> 0.0001) for buildings
 ┣ 📜 Phase4.py                  # Core Logic: AHP + Entropy + Monte Carlo
 ┗ 📜 Phase5.py                  # (Optional) Separate overlay generation


🚀 Key Methodologies

Hybrid Weighting: Combines expert judgment (AHP) with objective data variance (Entropy Weighting) to determine the importance of Temperature vs. Vegetation vs. Population.

Monte Carlo Simulation: Runs the model 150 times with slight variations in expert judgment to quantify uncertainty and prove robustness.

Soft Constraint Masking: Instead of deleting built-up areas (binary 0), assigns them a minimal score (0.0001) to maintain data integrity while prioritizing open spaces.

🛠️ Installation & Requirements

Ensure you have Python 3.8+ installed. Install the required geospatial libraries:

pip install numpy rasterio pandas scipy


▶️ How to Run the Analysis

Execute the scripts in the following order to reproduce the results:

Step 1: Preprocessing

Aligns all raw satellite data to a common 30m grid and CRS (EPSG:4326).

python Phase2_Preprocessing.py


Step 2: Normalization

Converts raw values (Degrees Celsius, Population Count) into a standardized 1–10 suitability score.

python Phase3_Normalization.py
python Phase3_Pop_Normalize.py


Step 3: Mask Update

Converts the binary exclusion mask into a "soft" decimal mask to handle built-up areas correctly.

python phase3b_updatemask.py


Step 4: Advanced Analysis (The Core)

Calculates Hybrid Weights (AHP + Entropy), runs the Monte Carlo simulation, and generates the final maps.

python Phase4.py


📊 Outputs Explanation

Final_UHI_Mitigation_Map_Hybrid.tif: The Primary Output. Red pixels indicate high-priority areas for intervention (Hot + Crowded + Low Vegetation).

Final_UHI_Ensemble_std.tif: The Confidence Map. Shows where the model is uncertain. Low values (Dark) = High Confidence.

uhi_weights_combined.json: Contains the mathematical proof of the weights used, including the Consistency Ratio (CR) to validate expert logic.

```
