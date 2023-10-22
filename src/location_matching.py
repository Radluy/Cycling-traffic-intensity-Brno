"""
Module loads basemap from OpenStreetMap network and matches other
networks and locations to it. The final model is a map of IDs to all
corresponding dataset from the Brno Cycling traffic intensity study
"""
import os
from typing import Tuple, List
os.environ['USE_PYGEOS'] = '0'

# pylint: disable=wrong-import-position
import geopandas as gpd
import pandas as pd
import pyrosm
from numpy import NaN

from geometry_utils import match_lines_by_bbox_overlap
from segmentation_utils import generate_segments, assign_segments_to_dataset


DEFAULT_BBOX = [16.4855, 49.1538, 16.7550, 49.2507]
DEFAULT_NUM_SEGMENTS = 32


def load_osm_basemap(filepath: str,
                     bounding_box: list[float, float, float, float] | None = None) \
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


def match_points_to_osm(basemap: gpd.GeoDataFrame,
                          filepath: str,
                          id_column: str,
                          new_id_column: str) -> gpd.GeoDataFrame:
    """Matches locations of any points of interest to OSM basemap. Geometry must be Points.
    Args:
        basemap (gpd.GeoDataFrame): osm basemap of Brno
        counters_path (str): path to any points dataset with coordinates
        id_column (str): exact name of column with unique IDs of the dataset
    Returns:
        gpd.GeoDataFrame: original basemap with new column of matched counters"""
    points_df = gpd.read_file(filepath)
    unique_points = points_df.drop_duplicates(subset=id_column)
    counter_ids = unique_points[id_column].to_list()
    counters_geometries = unique_points['geometry'].to_list()

    # load distances between streets and points
    distances_df = pd.DataFrame()
    for i, item in enumerate(counters_geometries):
        # pylint: disable=cell-var-from-loop
        distances_df[f'distance{i}'] = basemap['geometry'].apply(lambda x: x.distance(item))

    # create map of [osm street id : point id] by minimal distance between them
    point_way_map = {}
    for i in range(len(unique_points)):
        min_dist = basemap[distances_df[f"distance{i}"]==distances_df[f"distance{i}"].min()]
        point_way_map[min_dist['id'].unique()[0]] = counter_ids[i]

    # append point ids to basemap
    basemap[new_id_column] = basemap['id'].map(point_way_map)
    return basemap


# pylint: disable=too-many-arguments
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
    if new_id_column:
        foreign_network = foreign_network.rename(columns={id_column: new_id_column})
    else:
        new_id_column = id_column
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
            if new_match:  # query street id by geometry found by the algorithm
                new_match = foreign_segm[foreign_segm['geometry']
                                         == new_match][new_id_column].array[0]
            else:  # no matches found, NaN to match column length
                new_match = NaN
            matched_lines.append(new_match)

        basemap_segm[new_id_column] = matched_lines
        final_model = pd.concat([final_model, basemap_segm])

    return final_model


def update_street_network(model: gpd.GeoDataFrame,
                          filepath: str,
                          original_id_column: str,
                          segment_matrix: List[Tuple[float, float, float, float]],
                          model_id_column: str) -> gpd.GeoDataFrame:
    """Updates ids from matched foreign network with new version of the dataset
    Args:
        model (gpd.GeoDataFrame): basemap from OSM with already assigned segments
        and column with ids matched from foregin network
        filepath (str): path to dataset with different street network basemap, must have geometry
        original_id_column (str): exact name of column with unique IDs of the dataset
        segment_matrix (List[Tuple[float, float, float, float]]): list of segments, must be same
        as segments assigned to model
        model_id_column (str): name of column with datasets ids in model
        (could be different after rename)
    Returns:
        gpd.GeoDataFrame: model with updated column with foreign network streets ids"""
    foreign_network = gpd.read_file(filepath)
    foreign_network = foreign_network.rename(columns={original_id_column: model_id_column})
    foreign_network = foreign_network.drop_duplicates(subset=model_id_column)
    foreign_network = foreign_network[[model_id_column, 'geometry']]

    # load not already assigned streets from foreign network
    new_streets = foreign_network[
        ~foreign_network[model_id_column].isin(model[model_id_column])]
    new_streets = assign_segments_to_dataset(new_streets, segment_matrix, model_id_column)

    final_model = model.copy()
    segment_ids = range(len(segment_matrix))
    for segment_id in segment_ids:
        model_segm = model[model['segment_id'] == segment_id].copy()
        new_streets_segm = new_streets[new_streets['segment_id'] == segment_id].copy()

        # match new line from foreign to segment of basemodel (other way around)
        for new_line in new_streets_segm['geometry']:
            new_match = match_lines_by_bbox_overlap(new_line, model_segm['geometry'])
            if new_match:  # query street ID by geometry found by the algorithm
                new_line = new_streets_segm[new_streets_segm['geometry']
                                            == new_line][model_id_column].array[0]
                # update found match in model
                final_model.loc[final_model['geometry'] == new_match, model_id_column] = new_line

    return final_model


def update_point_system(model: gpd.GeoDataFrame,
                        filepath: str,
                        original_id_column: str,
                        model_id_column: str) -> gpd.GeoDataFrame:
    """Update ids in model from newer version of point system dataset
    Args:
        model (gpd.GeoDataFrame): basemap from OSM with existing column with point ids
        filepath (str): path to any points dataset with coordinates
        original_id_column (str): exact name of column with unique IDs of the dataset
        model_id_column (str): name of column with datasets ids in model
    Returns:
        gpd.GeoDataFrame: model with updated column with point system ids
    """
    points_df = gpd.read_file(filepath)
    points_df = points_df.rename(columns={original_id_column: model_id_column})
    unique_points = points_df.drop_duplicates(subset=model_id_column)
    # load not already assigned points from dataset
    new_points = unique_points[
        ~unique_points[model_id_column].isin(model[model_id_column])]
    counter_ids = new_points[model_id_column].to_list()
    counters_geometries = new_points['geometry'].to_list()

    # load distances between streets and points
    distances_df = pd.DataFrame()
    for i, item in enumerate(counters_geometries):
        # pylint: disable=cell-var-from-loop
        distances_df[f'distance{i}'] = model['geometry'].apply(lambda x: x.distance(item))

    # create map of {osm street id : point id} by minimal distance between them
    point_way_map = {}
    for i in range(len(new_points)):
        min_dist = model[distances_df[f"distance{i}"]==distances_df[f"distance{i}"].min()]
        point_way_map[min_dist['id'].unique()[0]] = counter_ids[i]

    # assign newly found point matches
    for model_id, point_id in point_way_map.items():
        model.loc[model['id'] == model_id, model_id_column] = point_id
    return model


if __name__ == '__main__':
    # read osm street network
    if not os.path.exists('../datasets/basemap.pkl'):
        model = load_osm_basemap("../datasets/czech_republic-latest.osm.pbf")
        print(model.head())
        model.to_pickle("../datasets/basemap.pkl")
    else:
        model = pd.read_pickle("../datasets/basemap.pkl")
    # match counter unit locations to basemap
    #model = match_points_to_osm(model,
    #                            '../datasets/cyklodetektory.geojson',
    #                            'LocationId',
    #                            'counters_id')
    #print(model.head())

    # match biketowork street network to basemap
    segments = generate_segments(DEFAULT_BBOX, DEFAULT_NUM_SEGMENTS)
    model = assign_segments_to_dataset(model, segments, 'id')
    model = match_street_network_to_osm(model,
                                        "../datasets/do_prace_na_kole.geojson",
                                        "GID_ROAD",
                                        segments,
                                        'biketowork_id')
    print(model.head())

    # match bkom street network to basemap
    #model = match_street_network_to_osm(model,
    #                                    "../datasets/bkom_scitanie.geojson",
    #                                    "id",
    #                                    segments,
    #                                    'city_census_id')
    #print(model.head())

    gpd.GeoDataFrame(model).to_file('../datasets/full_model.geojson', driver="GeoJSON")
