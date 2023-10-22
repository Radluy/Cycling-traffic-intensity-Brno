"""
Utils for geometry handling using shapely. Capable of calculating line angles, overlaps,
and finding best match for line in a different set.
"""
import os
import warnings
os.environ['USE_PYGEOS'] = '0'

# pylint: disable=wrong-import-position
import geopandas as gpd
import numpy as np
from shapely import geometry as shp

from segmentation_utils import generate_segments, assign_segments_to_dataset


# older GEOS warns for simple intersections, ignore
warnings.filterwarnings("ignore", message="invalid value encountered in intersection")
# http://www.csgnetwork.com/gpsdistcalc.html
# 4 digits ~ 23m roundup / 5 digits 2m roundup
NDIGITS = 5
ANGLE_OFFSET_LIMIT = 15
ANGLE_STEP = 5


def lines_overlap(line1: shp.MultiLineString | shp.LineString,
                  line2: shp.MultiLineString | shp.LineString,
                  round_digits: int) -> bool:
    """Determine whether two lines fully overlap with acceptable deviation.
    Shapely doesn't compute overlap for MultiLineStrings, so helper method is needed to
    determine overlap between all pairs of partial lineStrings
    Args:
        line1 (shp.MultiLineString | shp.linestring): line checked for covering second line
        line2 (shp.MultiLineString | shp.linestring): line checked for being covered by first line
        round_digits (int): number of digits to round the coordinates - helps with divergency
    Returns:
        bool: True or False whether lines overlap"""
    # lines may be linestring and multilinestrings
    lines1, lines2 = None, None
    if isinstance(line1, shp.MultiLineString):
        lines1 = list(line1.geoms)
    if isinstance(line2, shp.MultiLineString):
        lines2 = list(line2.geoms)

    # case multiline : multiline
    if lines1 and lines2:
        return any(
            any(_lines_overlap(line, other_line, round_digits) for line in lines1)
            for other_line in lines2)
    # case multiline : line
    if lines1 and not lines2:
        return any(_lines_overlap(line, line2, round_digits) for line in lines1)
    # case line : multiline
    if lines2 and not lines1:
        return any(_lines_overlap(line1, other_line, round_digits) for other_line in lines2)
    # case line : line
    return _lines_overlap(line1, line2, round_digits)


def _lines_overlap(line1: shp.LineString, line2: shp.LineString, round_digits: int) -> bool:
    """Private helper method for rounding and comparing partial LineString because
    Shapely doesn't compute overlap for MultiLineStrings.
    Args:
        line1 (shp.linestring): line checked for covering second line
        line2 (shp.linestring): line checked for being covered by first line
        round_digits (int): number of digits to round the coordinates - helps with divergency
    Returns:
        bool: whether either line covers the other"""
    line1_coords = []
    line2_coords = []
    # round according to round_digits param
    # bigger roundup means the lines are more likely to meet, eliminates offset
    for point_i in range(2):
        line1_coords.append((round(line1.coords[point_i][0], round_digits),
                             round(line1.coords[point_i][1], round_digits)))
        line2_coords.append((round(line2.coords[point_i][0], round_digits),
                             round(line2.coords[point_i][1], round_digits)))
    line1 = shp.LineString(line1_coords)
    line2 = shp.LineString(line2_coords)
    return line1.overlaps(line2) or line2.overlaps(line1)


def ellipsoid_buffer(line: shp.MultiLineString, round_digits: int) -> shp.Polygon:
    """Create ellipsoid-shaped bounding buffer over a MultiLineString.
    Args:
        line (shp.MultiLineString): original line to calculate its buffer
        round_digits (int): number of digits to round the coordinates - helps with divergency
    Returns:
        shp.Polygon: calculated ellipsoid-like buffer for the input line
    """
    polygon = shp.box(*[round(coord, round_digits) for coord in line.bounds])
    center = polygon.centroid
    unit_circle = center.buffer(1)
    x_length = polygon.bounds[2] - polygon.bounds[0]  # max_x - min_x
    y_length = polygon.bounds[3] - polygon.bounds[1]  # max_y - min_y
    scaled_ellipse = shp.affinity.scale(unit_circle, x_length, y_length)

    x_axis = shp.LineString([[0, 0], [1, 0]])
    angle = angle_between(line, x_axis)
    rotated_ellipse = shp.affinity.rotate(scaled_ellipse, angle)

    return rotated_ellipse


def box_buffer(line: shp.MultiLineString, round_digits: int) -> shp.Polygon:
    """Create box-shaped bounding buffer over a MultiLineString.
    Args:
        line (shp.MultiLineString): original line to calculate its buffer
        round_digits (int): number of digits to round the coordinates - helps with divergency
    Returns:
        shp.Polygon: calculated box buffer for the input line
    """
    return shp.box(*[round(coord, round_digits) for coord in line.bounds])


def angle_between(line_1: shp.MultiLineString, line_2: shp.MultiLineString) -> float:
    """Calculates angle in degrees between two 2D lines
    taken from:
    https://stackoverflow.com/a/13849249/71522
    Args:
        line_1 (shp.MultiLineString): first line of the angle
        line_2 (shp.MultiLineString): second line of the angle
    Returns:
        float: angle between two lines"""
    line_1, line_2 = line_1.bounds, line_2.bounds
    vector1 = [(line_1[0] - line_1[2]), (line_1[1] - line_1[3])]
    vector2 = [(line_2[0] - line_2[2]), (line_2[1] - line_2[3])]
    v1_unit = vector1 / np.linalg.norm(vector1)
    v2_unit = vector2 / np.linalg.norm(vector2)
    angle_radians = np.arccos(np.clip(np.dot(v1_unit, v2_unit), -1.0, 1.0))
    # modulo 90 to ignore direction of vector
    return np.degrees(angle_radians) % 90


def match_line_to_set(line: shp.MultiLineString,
                      other_lines: gpd.GeoSeries) -> shp.MultiLineString | None:
    """Finds best match in list of other lines for line
    Args:
        line (shp.MultiLineString): base line for which the matches should be found
        other_lines (gpd.GeoSeries): series of other lines with possible matches
    Returns:
        shp.MultiLineString | None: best match from other_lines or None if nothing was found"""
    candidate_lines = {}
    for round_digits in range(7, 2, -1):  # every digit down means more benevolent matching
        for index, other_line in enumerate(other_lines):
            angle = angle_between(line, other_line)
            if lines_overlap(line, other_line, round_digits) and angle < ANGLE_OFFSET_LIMIT:
                candidate_lines[f"{index}"] = angle
    if candidate_lines:
        best_match = min(candidate_lines, key=candidate_lines.get)
        return other_lines.iloc[int(best_match)]
    return None


def match_lines_by_bbox_overlap(line: shp.MultiLineString,
                                other_lines: gpd.GeoSeries) -> shp.MultiLineString | None:
    """Finds best match in list of other lines for line based on overlap of bounding boxes
    Args:
        line (shp.MultiLineString): baseline for which the matches should be found
        other_lines (gpd.GeoSeries): series of other lines with possible matches
    Returns:
        shp.MultiLineString | None: best match from other_lines or None if nothing was found"""
    max_accepted_angle = ANGLE_OFFSET_LIMIT
    round_digits = NDIGITS
    best_match = (0, 0, 0)  # overlap[0-1], angle[degrees], index of the line
    while best_match == (0, 0, 0):
        max_accepted_angle = max_accepted_angle + ANGLE_STEP
        # allow bigger offset if nothing was found up to 45 degrees and try one last iteration
        if max_accepted_angle >= 45:
            round_digits = round_digits - 1
        # iterate all lines from other set and save best match
        for index, other_line in enumerate(other_lines):
            angle = angle_between(line, other_line)
            polygon = ellipsoid_buffer(line, round_digits)
            other_polygon = ellipsoid_buffer(other_line, round_digits)
            try:  # calculate overlap of bounding boxes of streets in <0-1> interval
                overlap = polygon.intersection(other_polygon).area /         \
                    polygon.union(other_polygon).area
            except ZeroDivisionError:  # union can be empty, skip the street
                continue
            # progressively bigger allowed angle and highest overlap
            if angle < max_accepted_angle and overlap > best_match[0]:
                best_match = (overlap, angle, index)
        # if last iteration didn't succeed, return no match
        if max_accepted_angle >= 45 and best_match == (0, 0, 0):
            return None

    return other_lines.iloc[int(best_match[2])]


if __name__ == '__main__':
    # example usage of algorithm on one segment of OSM basemap and BikeToWork dataset
    import pandas as pd  # pylint: disable=wrong-import-position
    basemap = pd.read_pickle('basemap.pkl')
    segment_matrix = generate_segments((16.4855, 49.1538, 16.7550, 49.2507), 32)
    basemap = assign_segments_to_dataset(basemap, segment_matrix, 'id')
    biketowork = gpd.read_file('../datasets/do_prace_na_kole.geojson')
    biketowork = assign_segments_to_dataset(biketowork, segment_matrix, 'GID_ROAD')

    SEGMENT_ID = 400
    basemap_segm = basemap[basemap['segment_id'] == SEGMENT_ID]
    biketowork_segm = biketowork[biketowork['segment_id'] == SEGMENT_ID]
    matched_lines = []
    for basemap_line in basemap_segm['geometry']:
        # new_match = match_line_to_set(basemap_line, biketowork_segm['geometry'])
        new_match = match_lines_by_bbox_overlap(basemap_line, biketowork_segm['geometry'])
        if new_match:
            new_gid = biketowork_segm[biketowork_segm['geometry'] == new_match]['GID_ROAD'].array[0]
        else:
            new_gid = np.NaN
        matched_lines.append(new_gid)

    basemap_segm['GID_ROAD'] = matched_lines
