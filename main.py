import folium
import traceback
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, jsonify, request, url_for

app = Flask(__name__)
app.secret_key = "secret_key"

# Load the Parquet data
data = pd.read_parquet("sum2021B_MAP.parquet")


@app.get("/")
def index():
    device_ids = list(set(data["device_id"]))
    return render_template("index.html", device_ids=device_ids)


@app.post("/static-plot")
def static_plot():
    print("Started processing")
    try:
        get_data = request.get_json()
        device_id = get_data["deviceID"]
        from_time = datetime.strptime(get_data["fromTime"], "%Y-%m-%d").strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        to_time = datetime.strptime(get_data["toTime"], "%Y-%m-%d").strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )

        # Apply filters
        filtered_data = data[
            (data["device_id"] == int(device_id))
            & (data["created"] >= from_time)
            & (data["created"] <= to_time)
        ]

        # Extract latitude and longitude columns
        latitude = filtered_data["latitude"]
        longitude = filtered_data["longitude"]

        # Create list of tuples
        coordinates = list(zip(latitude, longitude))

        if coordinates:
            print("Coordinates gotten")
            # Create a map centered at the first coordinate
            m = folium.Map(location=[coordinates[0][0], coordinates[0][1]])

            # Circle markers
            for coordinate in coordinates:
                folium.CircleMarker(
                    location=[coordinate[0], coordinate[1]],
                    radius=0.1,
                    weight=1,
                    color="red",
                    fill=True,
                    fill_color="red",
                    fill_opacity=1,
                ).add_to(m)

            # auto adjust zoom
            m.fit_bounds(m.get_bounds())

            # Save map
            m.save("./static/static-coordinates.html")
            print("Map plotted and saved")

            return jsonify(
                {
                    "success": True,
                    "uri": url_for(
                        "static", filename="static-coordinates.html", _external=True
                    ),
                }
            )
        else:
            return jsonify(
                {
                    "success": False,
                }
            )
    except:
        print(traceback.format_exc())
        return jsonify({"success": False}), 500


@app.post("/dynamic-plot")
def dynamic_plot():
    print("Started processing")
    try:
        get_data = request.get_json()
        device_id = get_data["deviceID"]
        from_time = datetime.strptime(get_data["fromTime"], "%Y-%m-%d").strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )

        # Apply filters
        filtered_data = data[
            (data["device_id"] == int(device_id)) & (data["created"] >= from_time)
        ]

        # Extract latitude and longitude columns
        latitude = filtered_data["latitude"]
        longitude = filtered_data["longitude"]

        # Create list of tuples
        coordinates = list(zip(latitude, longitude))

        if coordinates:
            return jsonify({"success": True, "coordinates": coordinates})
        else:
            return jsonify({"success": False})

    except:
        print(traceback.format_exc())
        return jsonify({"success": False}), 500


if __name__ == "__main__":
    app.run(debug=True, port=4000, host="0.0.0.0")
