"""Utils responsible for segmenting window of a basemap to speed up processing and comparing"""
import os
from typing import Tuple, List
from itertools import pairwise
os.environ['USE_PYGEOS'] = '0'

import geopandas as gpd


MIN_X = 0
MIN_Y = 1
MAX_X = 2
MAX_Y = 3


def generate_segments(bounding_box: Tuple[float, float, float, float],
                      num_of_segments: int) -> List[Tuple[float, float, float, float]]:
    """Split window defined by limits into equally sized segments.
    Args:
        bounding_box (Tuple[float, float, float, float]): [minx, miny, maxx, maxy] of basemap
        num_of_segments (int): number of segments in 1 row and 1 column, final num is 2^x
    Returns:
        List[Tuple[float, float, float, float]]: List of segments, 1 segment defined by 4 limits"""
    # calculate X coordinates
    window_width = bounding_box[MAX_X] - bounding_box[MIN_X]
    segment_width = window_width / num_of_segments
    start_minx = bounding_box[MIN_X]
    segment_mins_x = [start_minx + (segment_width*n) for n in range(num_of_segments+1)]
    # calculate Y coordinates
    window_height = bounding_box[MAX_Y] - bounding_box[MIN_Y]
    segment_heigth = window_height / num_of_segments
    start_miny = bounding_box[MIN_Y]
    segment_mins_y = [start_miny + (segment_heigth*n) for n in range(num_of_segments+1)]

    # create segment matrix
    segment_matrix = []
    y_pairs = pairwise(segment_mins_y)
    for y_limits in y_pairs:
        x_pairs = pairwise(segment_mins_x)
        for x_limits in x_pairs:
            segment_matrix.append((x_limits[0], y_limits[0], x_limits[1], y_limits[1]))

    return segment_matrix


def is_in_segment(street_bounds: Tuple[float, float, float, float],
                  segment_bounds: Tuple[float, float, float, float]) -> bool:
    """Checks if start of street lays in segment
    Args:
        street_bounds (Tuple[float, float, float, float]): bounds of street
        segment_bounds (Tuple[float, float, float, float]): bounds of a segment
    Returns:
        bool: whether street lays in segment bounds"""
    return (street_bounds[MIN_X] > segment_bounds[MIN_X]) and \
           (street_bounds[MIN_X] < segment_bounds[MAX_X]) and \
           (street_bounds[MIN_Y] > segment_bounds[MIN_Y]) and \
           (street_bounds[MIN_Y] < segment_bounds[MAX_Y])


def assign_segments_to_dataset(dataset: gpd.GeoDataFrame,
                               segment_matrix: List[Tuple[float, float, float, float]],
                               id_column: str) -> gpd.GeoDataFrame:
    """Append column with assigned segment IDs. Dataset must have 'geometry' column.
    Args:
        dataset (gpd.GeoDataFrame): any geodataframe with 'geometry' column
        segment_matrix (List[Tuple[float, float, float, float]]): list generated by generate fnc
        id_column (str): name of column with unique IDs of the dataset
    Returns:
        gpd.GeoDataFrame: copy of dataset with segments column"""
    segment_ids = []
    street_ids = []
    for _, row in dataset.iterrows():
        street_bounds = row['geometry'].bounds
        # check every segment
        for index, segment in enumerate(segment_matrix):
            # save found segment and street ID
            if is_in_segment(street_bounds, segment):
                segment_ids.append(index)
                street_ids.append(row[id_column])
                break

    # append dataset with matched segment IDs
    street_to_segment_df = gpd.GeoDataFrame({id_column: street_ids, 'segment_id': segment_ids})
    return gpd.GeoDataFrame(dataset.merge(street_to_segment_df, on=id_column))
