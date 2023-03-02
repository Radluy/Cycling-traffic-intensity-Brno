import pyrosm
import geopandas as gpd
import pandas as pd
import gc
import typing


def load_osm_basemap(filepath: str, bounding_box: typing.List = None) -> gpd.GeoDataFrame:
    """Read OpenStreetMap .osm.pbf file and create a street network dataset for Brno
    Args:
        filepath (str): Path to the '.osm.pbf' file from OpenstreetMap
        bounding_box (typing.List, optional): List of coordinates [minx, miny, maxx, maxy]
        to trim the full dataset to  required location. Defaults to None.
    """
    bbox = [16.4855, 49.1538, 16.7550, 49.2507]  # default values for Brno borders
    pbf_reader = pyrosm.OSM(filepath, bounding_box=bbox)
    basemap_network = pbf_reader.get_network('cycling').append(pbf_reader.get_network('driving'))
    # clean up memory afterwards
    del pbf_reader
    gc.collect()
    return basemap_network


if __name__ == '__main__':
    basemap = load_osm_basemap('datasets/czech_republic-latest.osm.pbf')
    print(basemap.head())