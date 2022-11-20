from shapely import geometry as geo

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


def lines_overlap(line1, line2) -> bool:
    """
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
        return any([any([_lines_overlap(line, other_line) for line in lines1]) for other_line in lines2])
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
