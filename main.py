import math
import folium
import traceback
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, jsonify, request, url_for, json

app = Flask(__name__)
app.secret_key = "secret_key"

# Load the Parquet data
pdata = pd.read_parquet("sum2021B_MAP.parquet")
cdata = pd.read_csv("tbl__geofence.csv")


@app.get("/")
def index():
    # get user ids
    user_ids = list(set(pdata["user_id"]))
    user_ids = [id_ for id_ in user_ids if id_]
    # get plant names
    plant_names = list(set(cdata["name"]))
    plant_names = [name for name in plant_names]

    return render_template("index.html", user_ids=user_ids, plant_names=plant_names)


@app.get("/get-devices")
def get_devices():
    user_id = request.args.get("user_id")
    filtered_data = pdata[pdata["user_id"] == user_id]
    device_ids = filtered_data["device_id"]

    return jsonify(devices=list(set(device_ids)))


@app.post("/static-plot")
def static_plot():
    print("Started processing")
    try:
        get_data = request.get_json()
        plant_name = get_data["plantName"]
        user_id = get_data["userID"]
        device_id = get_data["deviceID"]
        speed_ratio = get_data["speed"]
        from_time = datetime.strptime(get_data["fromTime"], "%Y-%m-%d").strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        to_time = datetime.strptime(get_data["toTime"], "%Y-%m-%d").strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        speed_limit = 1
        plants = cdata["geojson"]
        filtered_cdata = cdata[(cdata["name"] == plant_name)]
        if len(filtered_cdata):
            speed_limit = filtered_cdata["speed_limit_inside"]
            speed_limit = (
                float(list(speed_limit)[0])
                if not math.isnan(list(speed_limit)[0])
                else 1
            )

        # Apply filters
        filtered_data = pdata[
            (pdata["user_id"] == user_id)
            & (pdata["device_id"] == int(device_id))
            & (pdata["created"] >= from_time)
            & (pdata["created"] <= to_time)
            & (pdata["speed"] >= float(speed_ratio) * speed_limit)
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

            # get geojson
            if plant_name == "All":
                [folium.GeoJson(json.loads(row)).add_to(m) for row in list(plants)]
            else:
                if len(filtered_cdata):
                    row = filtered_cdata["geojson"]
                    geojson = json.loads(row[row.keys()[0]])
                    folium.GeoJson(geojson, name=plant_name).add_to(m)

            # auto adjust zoom
            m.fit_bounds(m.get_bounds())

            # Save map
            m.save("./static/static-coordinates.html")
            print("Map plotted and saved")

            return jsonify(
                {
                    "success": True,
                    "uri": url_for(
                        "static",
                        filename="static-coordinates.html",
                        _external=True,
                        _scheme="https",
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
        plant_name = get_data["plantName"]
        user_id = get_data["userID"]
        device_id = get_data["deviceID"]
        speed_ratio = get_data["speed"]
        from_time = datetime.strptime(get_data["fromTime"], "%Y-%m-%d").strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        to_time = datetime.strptime(get_data["toTime"], "%Y-%m-%d").strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        speed_limit = 1
        plants = cdata["geojson"]
        filtered_cdata = cdata[(cdata["name"] == plant_name)]
        if len(filtered_cdata):
            speed_limit = filtered_cdata["speed_limit_inside"]
            speed_limit = (
                float(list(speed_limit)[0])
                if not math.isnan(list(speed_limit)[0])
                else 1
            )

        # Apply filters
        filtered_data = pdata[
            (pdata["user_id"] == user_id)
            & (pdata["device_id"] == int(device_id))
            & (pdata["created"] >= from_time)
            & (pdata["created"] <= to_time)
            & (pdata["speed"] >= float(speed_ratio) * speed_limit)
        ]

        # Extract latitude and longitude columns
        latitude = filtered_data["latitude"]
        longitude = filtered_data["longitude"]

        # Create list of tuples
        coordinates = list(zip(latitude, longitude))

        if coordinates:
            geojson = []
            if plant_name == "All":
                geojson = [json.loads(row) for row in list(plants)]
            else:
                if len(filtered_cdata):
                    # get geojson
                    row = filtered_cdata["geojson"]
                    geojson.append(json.loads(row[row.keys()[0]]))
            return jsonify(
                {"success": True, "coordinates": coordinates, "geojson": geojson}
            )
        else:
            return jsonify({"success": False})

    except:
        print(traceback.format_exc())
        return jsonify({"success": False}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
