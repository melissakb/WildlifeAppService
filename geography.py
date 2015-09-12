"""Module to handle geographic functions"""

import shapely
from shapely import geometry


def _convert_km_to_degrees(km):
    """Convert kilometers to degrees

    :param km:          Kilometers to convert

    :returns:           The number of kilometers in degrees

    """
    return km/110.574


def get_circle_coordinates(latitude, longitude, radius=10, resolution=4):
    """Get a collection of latitude/longitude points representing an
    approximate circle of the given radius around the given latitude and
    longitude

    :param latitude:        Latitude
    :param longitude:       Longitude
    :param radius           Radius in kilometers
    :param resolution:      Number of latitude/longitude pairs to calculate

    :returns:               A list of tuples (latitude, longitude)

    """
    center = shapely.geometry.Point(latitude, longitude)
    radius = _convert_km_to_degrees(radius)
    circle = center.buffer(radius, resolution=resolution)
    coordinates = [(circle.exterior.xy[0][i], circle.exterior.xy[1][i])
                   for i in xrange(len(circle.exterior.xy[0]))]
    return coordinates


def format_map_str(coordinates):
    """Format a list of latitude/longitude pairs to plot on a map at
    http://www.darrinward.com/lat-long/?id=693579

    :param coordinates:     A list of tuples (latitude, longitude)

    :return:                A string

    """
    polygon = ['{0}, {1}'.format(coor[0], coor[1])
               for coor in coordinates]
    return '\n'.join(polygon)