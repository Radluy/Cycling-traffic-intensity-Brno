import pandas as pd

from location_matching import *
from segmentation_utils import generate_segments, assign_segments_to_dataset


def update_census_example():
    model = pd.read_pickle("basemap.pkl")
    segment_matrix = generate_segments((16.4855, 49.1538, 16.7550, 49.2507), 32)
    model = assign_segments_to_dataset(model, segment_matrix, 'id')

    part_model = match_street_network_to_osm(model, '../datasets/bkom_scitanie.geojson', 'id',
                                             segment_matrix, 'census_id', [400, 399])
    print(len(part_model[~part_model['census_id'].isna()]))
    model = model.set_index('id').join(part_model.set_index('id')['census_id'])

    model = update_street_network(model, '../datasets/bkom_scitanie.geojson', 'id',
                                  segment_matrix, 'census_id')

    print(len(model[~model['census_id'].isna()]))
    return
    

def update_counters_example():
    model = pd.read_pickle("basemap.pkl")
    model = match_points_to_osm(model,
                                '../datasets/shortened_counters.geojson',
                                'LocationId',
                                'counters_id')
    print(model['counters_id'].unique())

    model = update_point_system(model,
                                '../datasets/cyklodetektory.geojson',
                                'LocationId',
                                'counters_id')
    print(model['counters_id'].unique())
    return


if __name__ == '__main__':
    update_counters_example()
