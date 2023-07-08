import json
from shapely import Point, Polygon
from shapely.geometry import shape
from shapely.affinity import scale

# local imports
from . import cdata, pdata
from .models import Users


def coordinate_in_area(coordinate, geojson):
    point = Point(coordinate[0], coordinate[1])
    
    geojson_coordinates = geojson['features'][0]['geometry']
    original_polygon = shape(geojson_coordinates)
    scaled_polygon = scale(original_polygon, 10, 10)
    if scaled_polygon.contains(point):
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


def load_users():
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
            for plant_name in plant_names:
                plant_row = cdata[(cdata["name"] == plant_name)]
                data = plant_row["geojson"]
                geojson = json.loads(data[data.keys()[0]])
                if coordinate_in_area(coordinate, geojson):
                    check_users = Users.query.filter(
                        Users.plant_name == plant_name, Users.user_id == str(id_)
                    ).all()
                    if not check_users:
                        print(f"Found new user in: {plant_name}")
                        new_user = Users(plant_name=plant_name, user_id=str(id_))
                        new_user.insert()
