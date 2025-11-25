import ahpy
import json

# === Pairwise comparisons ===
# Modify these based on your expert judgement

uhi_comparisons = {
    ('LST', 'NDVI'): 3,          # LST moderately more important
    ('LST', 'Population'): 2,    # slightly more important
    ('LST', 'Socio'): 4,         # strongly more important
    ('NDVI', 'Population'): 0.5, # Pop more important than NDVI
    ('NDVI', 'Socio'): 0.333,    # Socio more important than NDVI
    ('Population', 'Socio'): 2
}

uhi = ahpy.Compare('UHI', uhi_comparisons, precision=4)

print("\n📌 AHP Weights:")
print(uhi.weights)

print("\n📌 Consistency Ratio:")
print(uhi.consistency_ratio)

# Save weights
with open("uhi_weights.json", "w") as f:
    json.dump(uhi.weights, f, indent=4)

print("\n✅ Weights saved to uhi_weights.json")
