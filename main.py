import io
import os
import math
import boto3
import folium
import traceback
import pandas as pd
import pyarrow.parquet as pq
from datetime import datetime
from dotenv import load_dotenv
from shapely.geometry import Point, Polygon, shape, mapping
from flask import Flask, render_template, jsonify, request, url_for, json

load_dotenv()

ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")
CSV = os.getenv("CSV")
PARQUET = os.getenv("PARQUET")
USERS = {}

# initialize Flask app
app = Flask(__name__)
app.secret_key = "secret_key"

# initialize s3 client
s3 = boto3.client("s3", aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

# get files from s3
response = s3.get_object(Bucket=BUCKET_NAME, Key=CSV)
content = response["Body"]
cdata = pd.read_csv(content)

response = s3.get_object(Bucket=BUCKET_NAME, Key=PARQUET)
content = response["Body"]
pdata = pd.read_parquet(io.BytesIO(content.read()))



def coordinate_in_area(coordinate, geojson):
    point = Point(coordinate[0], coordinate[1])

    for feature in geojson["features"]:
        if feature["geometry"]["type"] == "Polygon":
            polygon = Polygon(feature["geometry"]["coordinates"][0])
            if polygon.contains(point):
                return True

    return False


def deeper_blue(num_shades, starting_hex="#0066FF"):
    hexcodes = []
    r, g, b = (
        int(starting_hex[1:3], 16),
        int(starting_hex[3:5], 16),
        int(starting_hex[5:], 16),
    )

    for _ in range(num_shades):
        r -= 20
        g -= 20
        b -= 20
        r = max(r, 0)
        g = max(g, 0)
        b = max(b, 0)
        hexcode = f"#{r:02X}{g:02X}{b:02X}"
        hexcodes.append(hexcode)

    return hexcodes



# get all user ids
user_ids = list(set(pdata["user_id"]))
user_ids = [id_ for id_ in user_ids if id_]
# get all plants
plant_names = list(cdata["name"])
# get sorted list of all plants and their users
print("Getting users")
for id_ in user_ids:
    # get user coordinates
    filtered_data = pdata[(pdata["user_id"] == id_)]
    # Extract latitude and longitude columns
    latitude = filtered_data["latitude"]
    longitude = filtered_data["longitude"]
    # Create list of tuples
    coordinates = list(zip(latitude, longitude))
    # check if any coordinate falls within plant
    for coordinate in coordinates:
        coordinate = coordinate[1], coordinate[0]
        for name in plant_names:
            plant_row = cdata[(cdata["name"] == name)]
            data = plant_row["geojson"]
            geojson = json.loads(data[data.keys()[0]]) 
            if coordinate_in_area(coordinate, geojson):
                if name not in USERS:
                    print(f"Found new user in: {name}")
                    USERS[name] = [id_]
                elif name in USERS:
                    USERS[name].append(id_)
            

@app.get("/")
def index():
    # get plant names
    plant_names = list(set(cdata["name"]))
    plant_names = [name for name in plant_names]

    return render_template("index.html", plant_names=plant_names)


@app.get("/get-devices")
def get_devices():
    user_id = request.args.get("user_id")
    filtered_data = pdata[pdata["user_id"] == user_id]
    device_ids = filtered_data["device_id"]

    return jsonify(devices=list(set(device_ids)))


@app.post("/get-users")
def get_users():
    data = request.get_json()
    plant_name = data["plantName"]
    print(plant_name)
    # get geojson
    user_ids = list(USERS[plant_name])

    return jsonify(users=user_ids)


@app.post("/static-plot")
def static_plot():
    try:
        get_data = request.get_json()
        # values from request
        plant_name = get_data["plantName"]
        user_id = get_data["userID"]
        speed_ratio = get_data["speed"]
        from_time = datetime.strptime(get_data["fromTime"], "%Y-%m-%d")
        to_time = datetime.strptime(get_data["toTime"], "%Y-%m-%d")
        # calculate filter values
        speed_limit = 1
        filtered_cdata = cdata[(cdata["name"] == plant_name)]
        if len(filtered_cdata):
            speed_limit = filtered_cdata["speed_limit_inside"]
            speed_limit = (
                float(list(speed_limit)[0])
                if not math.isnan(list(speed_limit)[0])
                else 1
            )

        # Apply filters
        if user_id == "All":
            filtered_data = pdata[
                (pdata["created"] >= from_time)
                & (pdata["created"] <= to_time)
                & (pdata["speed"] >= int(float(speed_ratio) * speed_limit))
            ]
        else:
            filtered_data = pdata[
                (pdata["user_id"] == user_id)
                & (pdata["created"] >= from_time)
                & (pdata["created"] <= to_time)
                & (pdata["speed"] >= int(float(speed_ratio) * speed_limit))
            ]

        # Extract latitude and longitude columns
        latitude = filtered_data["latitude"]
        longitude = filtered_data["longitude"]

        # Create list of tuples
        coordinates = list(zip(latitude, longitude))

        # calculate dot
        shade_count = round((float(speed_ratio) - 1) * 10)
        shade = deeper_blue(shade_count)[-1] if shade_count != 0 else deeper_blue(1)[0]

        if coordinates:
            # Create a map centered at the first coordinate
            m = folium.Map(location=[coordinates[0][0], coordinates[0][1]])

            # Circle markers
            for coordinate in coordinates:
                folium.CircleMarker(
                    location=[coordinate[0], coordinate[1]],
                    radius=0.1,
                    weight=10,
                    color=shade,
                    fill=True,
                    fill_color=shade,
                    fill_opacity=1,
                ).add_to(m)

            # get geojson
            if len(filtered_cdata):
                row = filtered_cdata["geojson"]
                geojson = json.loads(row[row.keys()[0]])
                folium.GeoJson(geojson, name=plant_name).add_to(m)

            # auto adjust zoom
            m.fit_bounds(m.get_bounds())

            # Save map
            m.save("./static/static-coordinates.html")

            return jsonify(
                {
                    "success": True,
                    "uri": url_for(
                        "static",
                        filename="static-coordinates.html",
                        _external=True,
                        _scheme="http",
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
    try:
        get_data = request.get_json()
        # values from request
        plant_name = get_data["plantName"]
        user_id = get_data["userID"]
        speed_ratio = get_data["speed"]
        from_time = datetime.strptime(get_data["fromTime"], "%Y-%m-%d")
        to_time = datetime.strptime(get_data["toTime"], "%Y-%m-%d")
        # calculate filter values
        speed_limit = 1
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
            & (pdata["created"] >= from_time)
            & (pdata["created"] <= to_time)
            & (pdata["speed"] >= int(float(speed_ratio) * speed_limit))
        ]

        # Extract latitude and longitude columns
        latitude = filtered_data["latitude"]
        longitude = filtered_data["longitude"]

        # Create list of tuples
        coordinates = list(zip(latitude, longitude))

        # calculate dot
        shade_count = round((float(speed_ratio) - 1) * 10)
        shade = deeper_blue(shade_count)[-1] if shade_count != 0 else deeper_blue(1)[0]

        if coordinates:
            geojson = []
            if len(filtered_cdata):
                # get geojson
                row = filtered_cdata["geojson"]
                geojson.append(json.loads(row[row.keys()[0]]))
            return jsonify(
                {
                    "success": True,
                    "coordinates": coordinates,
                    "geojson": geojson,
                    "shade": shade,
                }
            )
        else:
            return jsonify({"success": False})

    except:
        print(traceback.format_exc())
        return jsonify({"success": False}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
