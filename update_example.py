import pandas as pd

from location_matching import match_street_network_to_osm, update_street_network
from segmentation_utils import generate_segments, assign_segments_to_dataset


if __name__ == '__main__':
    model = pd.read_pickle("basemap.pkl")
    segment_matrix = generate_segments((16.4855, 49.1538, 16.7550, 49.2507), 32)
    model = assign_segments_to_dataset(model, segment_matrix, 'id')

    part_model = match_street_network_to_osm(model, 'datasets/bkom_scitanie.geojson', 'id',
                                             segment_matrix, 'census_id', [400, 399])
    print(len(part_model[~part_model['census_id'].isna()]))
    model = model.set_index('id').join(part_model.set_index('id')['census_id'])

    model = update_street_network(model, 'datasets/bkom_scitanie.geojson', 'id',
                                  segment_matrix, 'census_id')

    print(len(model[~model['census_id'].isna()]))
