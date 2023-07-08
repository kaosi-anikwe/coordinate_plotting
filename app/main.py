import io
import os
import math
import boto3
import folium
import traceback
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from shapely.geometry import Point, Polygon, shape, mapping
from shapely.affinity import scale
from flask import Blueprint, render_template, jsonify, request, url_for, json, current_app

# local imports
from .functions import coordinate_in_area, deeper_blue
from . import cdata, pdata
from .models import Users

load_dotenv()


# initialize Flask app
main = Blueprint("main", __name__)


@main.get("/")
def index():
    # get plant names
    plant_names = list(set(cdata["name"]))
    plant_names = [name for name in plant_names]

    return render_template("index.html", plant_names=plant_names)


@main.get("/get-devices")
def get_devices():
    user_id = request.args.get("user_id")
    filtered_data = pdata[pdata["user_id"] == user_id]
    device_ids = filtered_data["device_id"]

    return jsonify(devices=list(set(device_ids)))


@main.post("/get-users")
def get_users():
    data = request.get_json()
    plant_name = data["plantName"]
    print(plant_name)
    # get geojson
    users = Users.query.filter(Users.plant_name == plant_name).all()
    user_ids = [user.user_id for user in users]

    return jsonify(users=user_ids)


@main.post("/static-plot")
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
                    weight=5,
                    color=shade,
                    fill=True,
                    fill_color=shade,
                    fill_opacity=1,
                ).add_to(m)

            # get geojson
            if len(filtered_cdata):
                row = filtered_cdata["geojson"]
                geojson = json.loads(row[row.keys()[0]])
                # scale plant
                geojson_coordinates = geojson['features'][0]['geometry']
                original_polygon = shape(geojson_coordinates)
                original_polygon = scale(original_polygon, 10, 10)
                scaled_coordinates = mapping(original_polygon.buffer(0.05).exterior)
                folium.GeoJson({"type": "Polygon", "coordinates": [scaled_coordinates['coordinates']]}).add_to(m)

            # auto adjust zoom
            m.fit_bounds(m.get_bounds())

            # Save map
            m.save(f"{current_app.static_folder}/static-coordinates.html")

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


@main.post("/dynamic-plot")
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
                data = json.loads(row[row.keys()[0]])
                # scale plant
                geojson_coordinates = data['features'][0]['geometry']
                original_polygon = shape(geojson_coordinates)
                original_polygon = scale(original_polygon, 10, 10)
                scaled_coordinates = mapping(original_polygon.buffer(0.05).exterior)
                scaled_geojson = {"type": "Polygon", "coordinates": [scaled_coordinates['coordinates']]}
                geojson.append(scaled_geojson)
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
