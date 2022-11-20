from shapely import geometry as geo
import numpy as np


# http://www.csgnetwork.com/gpsdistcalc.html
# 4 digits ~ 23m roundup / 5 digits 2m roundup
NDIGITS = 4


def is_point_on_line(point, line):
    return line.distance(point) < 1e-3


def lines_connect(line1, line2):
    # TODO
    pass


def lines_match(line1, line2):
    # TODO
    pass


# TODO: optimize to stop traversing dataset once a single match was found
def assign_overlap(row, model_geom, current_gid, new_gid):
    # find new overlap
    if lines_overlap(row['geometry'], model_geom):
        list_current = current_gid  # .to_list()
        list_current.append(new_gid)
        return list_current
    else:
        return current_gid


def lines_overlap(line1, line2) -> bool:
    """
    Determine whether two lines fully overlap with acceptable deviation
    :param line1: geo.MultiLineString: line that is checked for fully covering the second param line
    :param line2: geo.MultiLineString: line that is checked for being fully covered by the first param line
    :return Boolean whether the lines overlap
    """
    lines1, lines2 = None, None
    if isinstance(line1, geo.MultiLineString):
        lines1 = [line for line in line1.geoms]
    if isinstance(line2, geo.MultiLineString):
        lines2 = [line for line in line2.geoms]

    if lines1 and lines2:
        return any(
            [any([_lines_overlap(line, other_line) for line in lines1]) for other_line in lines2]
        )
    elif lines1 and not lines2:
        return any([_lines_overlap(line, line2) for line in lines1])
    elif lines2 and not lines1:
        return any([_lines_overlap(line1, other_line) for other_line in lines2])
    else:
        return _lines_overlap(line1, line2)


def _lines_overlap(line1, line2):
    line1_coords = []
    line2_coords = []
    for point_i in range(2):
        line1_coords.append((round(line1.coords[point_i][0], NDIGITS),
                             round(line1.coords[point_i][1], NDIGITS)))
        line2_coords.append((round(line2.coords[point_i][0], NDIGITS),
                             round(line2.coords[point_i][1], NDIGITS)))
    line1 = geo.LineString(line1_coords)
    line2 = geo.LineString(line2_coords)
    return line1.covers(line2)


"""# TAKEN FROM https://stackoverflow.com/questions/28260962/calculating-angles-between-line-segments-python-with-math-atan2
def _dot_product(vector_a, vector_b):
    return vector_a[0]*vector_b[0]+vector_a[1]*vector_b[1]


def angle(line_1, line_2):
    vector_a = [(line_1[0] - line_1[2]), (line_1[1] - line_1[3])]
    vector_b = [(line_2[0] - line_2[2]), (line_2[1] - line_2[3])]
    # Get dot prod
    dot_product = _dot_product(vector_a, vector_b)
    # Get magnitudes
    magnitude_a = _dot_product(vector_a, vector_a) ** 0.5
    magnitude_b = _dot_product(vector_b, vector_b) ** 0.5
    # Get cosine value
    cos = dot_product / magnitude_a / magnitude_b
    # Get angle in radians and then convert to degrees
    angle_radians = math.acos(dot_product / magnitude_b / magnitude_a)
    # Basically doing angle <- angle mod 360
    angle_degree = math.degrees(angle_radians) % 360

    if angle_degree - 180 >= 0:
        return 360 - angle_degree
    else:
        return angle_degree"""


def angle_between(line_1, line_2):
    """
    Calculates the angle in degrees between two 2D lines
    taken from:
    https://stackoverflow.com/questions/2827393/angles-between-two-n-dimensional-vectors-in-python/13849249#13849249
    """
    vector1 = [(line_1[0] - line_1[2]), (line_1[1] - line_1[3])]
    vector2 = [(line_2[0] - line_2[2]), (line_2[1] - line_2[3])]
    v1_unit = vector1 / np.linalg.norm(vector1)
    v2_unit = vector2 / np.linalg.norm(vector2)
    angle_radians = np.arccos(np.clip(np.dot(v1_unit, v2_unit), -1.0, 1.0))
    # modulo 90 to ignore direction of vector
    return np.degrees(angle_radians) % 90


# TODO: WIP
def match_lines(line, other_lines):
    # The snap() function in shapely.ops snaps the vertices in one geometry
    # to the vertices in a second geometry with a given tolerance.
    # from shapely.ops import snap
    other_geoms = [multiline.geoms for multiline in other_lines]
    for other_geom in other_geoms:
        for linestring in other_geom:
            print([a for a in linestring.coords])


if __name__ == '__main__':
    line = geo.MultiLineString((((16.4199381, 49.1733522), (16.4203671, 49.1733876)),
                                ((16.4203671, 49.1733876), (16.4209684, 49.1735831)),
                                ((16.4209684, 49.1735831), (16.4211327, 49.1736097)),
                                ((16.4211327, 49.1736097), (16.4212775, 49.1736027)),
                                ((16.4212775, 49.1736027), (16.4214545, 49.173536))))
    import pandas as pd
    model = pd.read_pickle('model_shrink_segmented.pkl')
    match_lines(line, model[model['segment_id'] == 188]['geometry'])
