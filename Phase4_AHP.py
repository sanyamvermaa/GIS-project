import ahpy
import json

# === Pairwise comparisons WITHOUT socio ===
uhi_comparisons = {
    ('LST', 'NDVI'): 3,
    ('LST', 'Population'): 2,
    ('NDVI', 'Population'): 0.5
}

uhi = ahpy.Compare('UHI', uhi_comparisons, precision=4)

print("\n📌 AHP Weights:")
print(uhi.local_weights) # <--- FIX 1: Use .local_weights

print("\n📌 Consistency Ratio:")
print(uhi.consistency_ratio)

# Save weights
with open("uhi_weights.json", "w") as f:
    json.dump(uhi.local_weights, f, indent=4) # <--- FIX 2: Use .local_weights

print("\n✅ Weights saved to uhi_weights.json")