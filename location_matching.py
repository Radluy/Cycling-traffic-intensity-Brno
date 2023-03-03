"""
Module loads basemap from OpenStreetMap network and matches other 
networks and locations to it. The final model is a map of IDs to all 
corresponding dataset from the Brno Cycling traffic intensity study
"""
import logging
import os
import typing

import geopandas as gpd
import pandas as pd
import pyrosm


def load_osm_basemap(filepath: str, bounding_box: typing.List | None = None) -> gpd.GeoDataFrame:
    """Read OpenStreetMap .osm.pbf file and create a street network dataset for Brno
    Args:
        filepath (str): Path to the '.osm.pbf' file from OpenstreetMap
        bounding_box (typing.List, optional): List of coordinates [minx, miny, maxx, maxy]
        to trim the full dataset to  required location. Defaults to None.
    Returns:
        gpd.GeoDataFrame: Brno basemap dataframe
    """
    if not bounding_box:
        bounding_box = [16.4855, 49.1538, 16.7550, 49.2507]  # default values for Brno borders
    pbf_reader = pyrosm.OSM(filepath, bounding_box=bounding_box)
    basemap_df = pd.concat([pbf_reader.get_network('cycling'), pbf_reader.get_network('driving')])
    basemap_df = basemap_df.drop_duplicates(subset='id')
    return basemap_df


def match_counters_to_osm(basemap: gpd.GeoDataFrame, counters_filepath: str) -> gpd.GeoDataFrame:
    """Match locations of counter units to OSM basemap. Uses 'LocationId' column of counters set
    Args:
        basemap (gpd.GeoDataFrame): osm basemap of Brno
        counters_path (str): path to counters GEOJSON dataset with unit locations
    Returns:
        gpd.GeoDataFrame: original basemap with new column of matched counters
    """
    counters_df = gpd.read_file(counters_filepath)
    unique_counters = counters_df.drop_duplicates(subset='LocationId')
    counter_ids = unique_counters['LocationId'].to_list()
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


def match_biketowork_to_osm(basemap: gpd.GeoDataFrame, 
                            biketowork_filepath: str) -> gpd.GeoDataFrame:
    """_summary_
    Args:
        basemap (gpd.GeoDataFrame): _description_
        biketowork_filepath (str): _description_
    Returns:
        gpd.GeoDataFrame: _description_
    """
    biketowork_df = gpd.read_file(biketowork_filepath)



if __name__ == '__main__':
    # read osm street network
    if not os.path.exists('basemap.pkl'):
        logging.log(level=1, msg="Generating basemap from OSM dataset")
        basemap = load_osm_basemap('datasets/czech_republic-latest.osm.pbf')
        print(basemap.head())
        basemap.to_pickle('basemap.pkl')
    else:
        basemap = pd.read_pickle('basemap.pkl')
    # match counter unit locations to basemap
    logging.log(level=1, msg="Matching counter unit locations to basemap")
    basemap = match_counters_to_osm(basemap, 'datasets/cyklodetektory.geojson')
    print(basemap.head())

    logging.log(level=1, msg="Matching BikeToWork street network to basemap")
