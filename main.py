import pandas as pd
from datetime import datetime

# Load the Parquet data
data = pd.read_parquet("sum2021B_MAP.parquet")

device_ids = list(set(data["device_id"]))
timestamps = list(set(data["created"]))

formatted_time = datetime.strptime(str(timestamps[0]), "%Y-%m-%d %H:%M:%S.%f")

from_time = datetime(
    2021,
    1,
    4,
).strftime("%Y-%m-%d %H:%M:%S.%f")
to_time = datetime(2021, 2, 1).strftime("%Y-%m-%d %H:%M:%S.%f")

# Apply filters
filtered_data = data[
    (data["device_id"] == device_ids[0])
    & (data["created"] >= from_time)
    & (data["created"] <= to_time)
]

# Extract latitude and longitude columns
latitude = filtered_data["latitude"]
longitude = filtered_data["longitude"]

# Create list of tuples
coordinates = list(zip(latitude, longitude))


import matplotlib.pyplot as plt

# Create scatter plot
plt.scatter(longitude, latitude, s=10)
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.title("Static Plot")
plt.show()


# Dynamic plotting

import folium

# Create a map centered at the first coordinate
m = folium.Map(location=[coordinates[0][0], coordinates[0][1]], zoom_start=30)

folium.PolyLine(locations=coordinates, color="blue", weight=0.5, dash_array="2").add_to(
    m
)

# Iterate over coordinates and add markers and lines
for i in range(len(coordinates)):
    # Add marker for each coordinate
    folium.Marker(location=[coordinates[i][0], coordinates[i][1]]).add_to(m)

    # Add line connecting consecutive coordinates
    if i > 0:
        folium.PolyLine(
            locations=[coordinates[i - 1], coordinates[i]], color="blue"
        ).add_to(m)

    # Save the map as HTML file for visualization
m.save("coordinates.html")
