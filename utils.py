from shapely import geometry as geo
import numpy as np


# http://www.csgnetwork.com/gpsdistcalc.html
# 4 digits ~ 23m roundup / 5 digits 2m roundup
NDIGITS = 4
ANGLE_OFFSET_LIMIT = 15


def is_point_on_line(point, line):
    return line.distance(point) < 1e-3


# TODO: optimize to stop traversing dataset once a single match was found
def assign_overlap(row, model_geom, current_gid, new_gid):
    # find new overlap
    if lines_overlap(row['geometry'], model_geom, round_digits=NDIGITS):
        list_current = current_gid  # .to_list()
        list_current.append(new_gid)
        return list_current
    else:
        return current_gid


def lines_overlap(line1, line2, round_digits) -> bool:
    """
    Determine whether two lines fully overlap with acceptable deviation
    :param line1: shapely.MultiLineString: line that is checked for fully covering the second param line
    :param line2: shapely.MultiLineString: line that is checked for being fully covered by the first param line
    :return Boolean whether the lines overlap
    """
    lines1, lines2 = None, None
    if isinstance(line1, geo.MultiLineString):
        lines1 = [line for line in line1.geoms]
    if isinstance(line2, geo.MultiLineString):
        lines2 = [line for line in line2.geoms]

    if lines1 and lines2:
        return any(
            [any([_lines_overlap(line, other_line, round_digits) for line in lines1]) for other_line in lines2]
        )
    elif lines1 and not lines2:
        return any([_lines_overlap(line, line2, round_digits) for line in lines1])
    elif lines2 and not lines1:
        return any([_lines_overlap(line1, other_line, round_digits) for other_line in lines2])
    else:
        return _lines_overlap(line1, line2, round_digits)


def _lines_overlap(line1, line2, round_digits) -> bool:
    """
    Private helper method for rounding and comparing small LineString segments
    :param line1: shapely.LineString
    :param line2: shapely.LineString
    :param round_digits: number of digits the coordinates should be rounded to
    :return: bool: whether either line covers the other
    """
    line1_coords = []
    line2_coords = []
    for point_i in range(2):
        line1_coords.append((round(line1.coords[point_i][0], round_digits),
                             round(line1.coords[point_i][1], round_digits)))
        line2_coords.append((round(line2.coords[point_i][0], round_digits),
                             round(line2.coords[point_i][1], round_digits)))
    line1 = geo.LineString(line1_coords)
    line2 = geo.LineString(line2_coords)
    return line1.intersects(line2) or line2.intersects(line1)


def angle_between(line_1, line_2) -> float:
    """
    Calculates the angle in degrees between two 2D lines
    taken from:
    https://stackoverflow.com/questions/2827393/angles-between-two-n-dimensional-vectors-in-python/13849249#13849249
    :param line_1: shapely.MultiLineString
    :param line_2: shapely.MultiLineString
    :return: Float: angle between two lines
    """
    vector1 = [(line_1[0] - line_1[2]), (line_1[1] - line_1[3])]
    vector2 = [(line_2[0] - line_2[2]), (line_2[1] - line_2[3])]
    v1_unit = vector1 / np.linalg.norm(vector1)
    v2_unit = vector2 / np.linalg.norm(vector2)
    angle_radians = np.arccos(np.clip(np.dot(v1_unit, v2_unit), -1.0, 1.0))
    # modulo 90 to ignore direction of vector
    return np.degrees(angle_radians) % 90


def match_lines(line, other_lines) -> geo.MultiLineString | None:
    """
    Find best match in list of other lines for line
    Takes angles into an account
    :param line: shapely.MultiLineString: base line for which the matches should be found
    :param other_lines: list(shapely.MultiLineString): list of other lines with possible matches
    :return: shapely.MultiLineString with best match from other_lines
    """
    candidate_lines = {}
    for round_digits in range(7, 2, -1):
        for index, other_line in enumerate(other_lines):
            angle = angle_between(line.bounds, other_line.bounds)
            if lines_overlap(line, other_line, round_digits) and angle < ANGLE_OFFSET_LIMIT:
                candidate_lines[f"{index}"] = angle
    if candidate_lines:
        best_match = min(candidate_lines, key=candidate_lines.get)
        return other_lines.iloc[int(best_match)]
    else:
        return None


if __name__ == '__main__':
    line = geo.MultiLineString((((16.4199381, 49.1733522), (16.4203671, 49.1733876)),
                                ((16.4203671, 49.1733876), (16.4209684, 49.1735831)),
                                ((16.4209684, 49.1735831), (16.4211327, 49.1736097)),
                                ((16.4211327, 49.1736097), (16.4212775, 49.1736027)),
                                ((16.4212775, 49.1736027), (16.4214545, 49.173536))))
    import pandas as pd
    import geopandas as gpd
    model = pd.read_pickle('model_shrink_segmented.pkl')
    biketowork = pd.read_pickle('biketowork_shrink_segmented.pkl')
    model_160 = model[model['segment_id'] == 160].copy()

    matched_lines = []
    for line_real in biketowork[biketowork['segment_id'] == 160]['geometry']:
        new_match = match_lines(line_real, model_160['geometry'])
        new_gid = biketowork[biketowork['geometry'] == new_match]['GID_ROAD']
        matched_lines.append(new_gid)

    model_160['GID_ROAD'] = pd.Series(matched_lines)
    model_160.to_csv('model_160_matched_biketowork.csv')
    gpd.GeoDataFrame(model_160).to_file('model_160_matched_biketowork.geojson', driver="GeoJSON")
