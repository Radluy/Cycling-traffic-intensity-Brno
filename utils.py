from shapely import geometry as geo


def is_point_on_line(point, line):
    return line.distance(point) < 1e-3


def lines_connect(line1, line2):
    # TODO
    pass


def lines_match(line1, line2):
    # TODO
    pass
