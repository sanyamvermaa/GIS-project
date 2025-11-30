# Define sites based on Mitigation Priority
sites = [
    # --- HIGH PRIORITY (Hot, Dense, Industrial/Commercial) ---
    # Strategy: Needs Cool Roofs / Green Corridors immediately
    {"Name": "Peenya Industrial Area", "Lat": 13.0329, "Lon": 77.5273, "Priority": "High", "Color": "red"},
    {"Name": "Chickpet (Core City)",   "Lat": 12.9719, "Lon": 77.5772, "Priority": "High", "Color": "red"},
    {"Name": "Shivajinagar",           "Lat": 12.9857, "Lon": 77.6057, "Priority": "High", "Color": "red"},
    {"Name": "Electronic City Ph-1",   "Lat": 12.8452, "Lon": 77.6602, "Priority": "High", "Color": "red"},

    # --- MEDIUM PRIORITY (Warning Zones, Mixed Use) ---
    # Strategy: Prevent further heating, increase street trees
    {"Name": "Whitefield",             "Lat": 12.9698, "Lon": 77.7500, "Priority": "Medium", "Color": "orange"},
    {"Name": "Indiranagar",            "Lat": 12.9716, "Lon": 77.6412, "Priority": "Medium", "Color": "orange"},
    {"Name": "HSR Layout",             "Lat": 12.9121, "Lon": 77.6446, "Priority": "Medium", "Color": "orange"},
    {"Name": "Yelahanka New Town",     "Lat": 13.1007, "Lon": 77.5963, "Priority": "Medium", "Color": "orange"},
    {"Name": "Kengeri Satellite",      "Lat": 12.9177, "Lon": 77.4833, "Priority": "Medium", "Color": "orange"},

    # --- LOW PRIORITY (Existing Cool Islands / Water) ---
    # Strategy: Preservation (Don't build here)
    {"Name": "Cubbon Park",            "Lat": 12.9763, "Lon": 77.5929, "Priority": "Low", "Color": "green"},
    {"Name": "Lalbagh",                "Lat": 12.9507, "Lon": 77.5848, "Priority": "Low", "Color": "green"},
    {"Name": "Ulsoor Lake",            "Lat": 12.9830, "Lon": 77.6220, "Priority": "Low", "Color": "green"},
    {"Name": "GKVK Campus",            "Lat": 13.0760, "Lon": 77.5770, "Priority": "Low", "Color": "green"},
    {"Name": "Turahalli Forest",       "Lat": 12.8930, "Lon": 77.5300, "Priority": "Low", "Color": "green"},
]

# Create Map centered on Bengaluru
m = folium.Map(location=[12.97, 77.59], zoom_start=11, tiles="OpenStreetMap")

# Add markers
for s in sites:
    folium.Marker(
        [s["Lat"], s["Lon"]],
        popup=f'<b>{s["Name"]}</b><br>Priority: {s["Priority"]}',
        tooltip=s["Name"],
        icon=folium.Icon(color=s["Color"], icon="info-sign")
    ).add_to(m)

# Add a Legend (HTML overlay)
legend_html = '''
     <div style="position: fixed; 
     bottom: 50px; left: 50px; width: 160px; height: 130px; 
     border:2px solid grey; z-index:9999; font-size:14px;
     background-color:white; opacity:0.9; padding: 10px;">
     <b>Mitigation Priority</b><br>
     <i class="fa fa-map-marker" style="color:red"></i> High Suitability<br>
     <i class="fa fa-map-marker" style="color:orange"></i> Medium Suitability<br>
     <i class="fa fa-map-marker" style="color:green"></i> Low (Preserve)<br>
     </div>
     '''
m.get_root().html.add_child(folium.Element(legend_html))

# Save
m.save("bengaluru_suitability_sites.html")
print("Map saved as bengaluru_suitability_sites.html")