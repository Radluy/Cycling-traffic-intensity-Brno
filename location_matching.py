"""
Module loads basemap from OpenStreetMap network and matches other 
networks and locations to it. The final model is a map of IDs to all 
corresponding dataset from the Brno Cycling traffic intensity study
"""
import os
from typing import Tuple, List
os.environ['USE_PYGEOS'] = '0'

import geopandas as gpd
import pandas as pd
import pyrosm
from numpy import NaN

from geometry_utils import match_lines_by_bbox_overlap
from segmentation_utils import generate_segments, assign_segments_to_dataset


DEFAULT_BBOX = (16.4855, 49.1538, 16.7550, 49.2507)


def load_osm_basemap(filepath: str,
                     bounding_box: Tuple[float, float, float, float] | None = None) \
                     -> gpd.GeoDataFrame:
    """Read OpenStreetMap .osm.pbf file and create a street network dataset for Brno
    Args:
        filepath (str): Path to the '.osm.pbf' file from OpenstreetMap
        bounding_box (typing.List, optional): List of coordinates [minx, miny, maxx, maxy]
        to trim the full dataset to  required location. Defaults to None.
    Returns:
        gpd.GeoDataFrame: Brno basemap dataframe"""
    if not bounding_box:
        bounding_box = DEFAULT_BBOX  # default values for Brno borders
    pbf_reader = pyrosm.OSM(filepath, bounding_box=bounding_box)
    basemap_df = pd.concat([pbf_reader.get_network('cycling'), pbf_reader.get_network('driving')])
    basemap_df = basemap_df.drop_duplicates(subset='id')
    return basemap_df


def match_counters_to_osm(basemap: gpd.GeoDataFrame,
                          counters_filepath: str,
                          id_column: str) -> gpd.GeoDataFrame:
    """Matches locations of counter units to OSM basemap.
    Args:
        basemap (gpd.GeoDataFrame): osm basemap of Brno
        counters_path (str): path to counters GEOJSON dataset with unit locations
        id_column (str): exact name of column with unique IDs of the dataset
    Returns:
        gpd.GeoDataFrame: original basemap with new column of matched counters"""
    counters_df = gpd.read_file(counters_filepath)
    unique_counters = counters_df.drop_duplicates(subset=id_column)
    counter_ids = unique_counters[id_column].to_list()
    counters_geometries = unique_counters['geometry'].to_list()

    # load distances between streets and counter units
    distances_df = pd.DataFrame()
    for i, item in enumerate(counters_geometries):
        distances_df[f'distance{i}'] = basemap['geometry'].apply(lambda x: x.distance(item))

    # create map of [osm street id : unit id] by minimal distance between them
    unit_way_map = {}
    for i in range(len(unique_counters)):
        min_dist = basemap[distances_df[f"distance{i}"]==distances_df[f"distance{i}"].min()]
        unit_way_map[min_dist['id'].unique()[0]] = counter_ids[i]

    # append unit ids to counters_df
    basemap['counter_id'] = basemap['id'].map(unit_way_map)
    return basemap


def match_street_network_to_osm(basemap: gpd.GeoDataFrame,
                                filepath: str,
                                id_column: str,
                                segment_matrix: List[Tuple[float, float, float, float]],
                                new_id_column: str | None = None,
                                segment_ids: List[int] | None = None) -> gpd.GeoDataFrame:
    """Matches streets from any network to osm basemap, 
    using algorithm based on street bounding box overlap and angle.
    Args:
        basemap (gpd.GeoDataFrame): basemap dataframe from OSM, needs to have geometry 
        filepath (str): path to dataset with different street network basemap, must have geometry
        id_column (str): exact name of column with unique IDs of the dataset
        new_id_column (str | None): optional rename of the ID column
        segment_matrix (List[Tuple[float, float, float, float]]): list of segments used in basemap
        of the osm basemap used, must be same as one used in load_osm_basemap() function
        segment_ids (List[int] | None, optional): list of segment ids to process, all if empty
    Returns:
        gpd.GeoDataFrame: basemap with appended column with matched foreign network streets"""
    final_model = gpd.GeoDataFrame()
    # prepare dataset to be processed
    foreign_network = gpd.read_file(filepath)
    foreign_network = foreign_network.rename(columns={id_column: new_id_column})
    foreign_network = foreign_network.drop_duplicates(subset=new_id_column)
    foreign_network = foreign_network[[new_id_column, 'geometry']]
    foreign_network = assign_segments_to_dataset(foreign_network, segment_matrix, new_id_column)
    # compare corresponding segments
    segment_ids = range(len(segment_matrix)) if not segment_ids else segment_ids
    for segment_id in segment_ids:
        basemap_segm = basemap[basemap['segment_id'] == segment_id].copy()
        foreign_segm = foreign_network[foreign_network['segment_id'] == segment_id].copy()

        matched_lines = []
        for basemap_line in basemap_segm['geometry']:
            new_match = match_lines_by_bbox_overlap(basemap_line, foreign_segm['geometry'])
            if new_match:  # query row by id found by the algorithm
                new_match = foreign_segm[foreign_segm['geometry']
                                         == new_match][new_id_column].array[0]
            else:  # no matches found, NaN to match column length
                new_match = NaN
            matched_lines.append(new_match)

        basemap_segm[new_id_column] = matched_lines
        final_model = pd.concat([final_model, basemap_segm])

    return final_model


if __name__ == '__main__':
    # read osm street network
    if not os.path.exists('basemap.pkl'):
        model = load_osm_basemap("datasets/czech_republic-latest.osm.pbf")
        print(model.head())
        model.to_pickle("basemap.pkl")
    else:
        model = pd.read_pickle("basemap.pkl")  
    # match counter unit locations to basemap
    model = match_counters_to_osm(model, 'datasets/cyklodetektory.geojson', 'LocationId')
    print(model.head())

    # match biketowork street network to basemap
    segment_matrix = generate_segments((16.4855, 49.1538, 16.7550, 49.2507), 32)
    model = assign_segments_to_dataset(model, segment_matrix, 'id')
    model = match_street_network_to_osm(model,
                                        "datasets/do_prace_na_kole.geojson",
                                        "GID_ROAD",
                                        segment_matrix,
                                        'biketowork_id')
    print(model.head())

    # match bkom street network to basemap
    model = match_street_network_to_osm(model,
                                        "datasets/bkom_scitanie.geojson",
                                        "id",
                                        segment_matrix,
                                        'city_census_id')
    print(model.head())

    gpd.GeoDataFrame(model).to_file('full_model.geojson', driver="GeoJSON")
    