"""Experiments evaluating the final application"""
import geopandas as gpd
import pandas as pd


def eval_street_algorithm():
    """Calculate algorithm accuracy on the annotated samples"""
    model = gpd.read_file('../datasets/full_model_ellipsoid.geojson')
    results = pd.read_csv('../datasets/algo_eval.csv', delimiter=';')

    correct_matches_btw = 0
    correct_matches_cens = 0
    for _, line in results.iterrows():
        line['OSM'] = int(line['OSM'].replace(',', ''))
        line['BikeToWork'] = [int(val) for val in line['BikeToWork'].split(',')]

        model_street = model[model['id'] == line['OSM']]
        if model_street['biketowork_id'].array[0] in line['BikeToWork']:
            correct_matches_btw += 1
        if model_street['city_census_id'].array[0] == line['Census']:
            correct_matches_cens += 1

    percentage = round(correct_matches_btw/results.shape[0] * 100, 2)
    print(f"BikeToWork matches: {correct_matches_btw}, [{percentage}%]")
    # pylint: disable=no-member
    percentage = round(correct_matches_cens/results.shape[0] * 100, 2)
    print(f"Census matches: {correct_matches_cens}, [{percentage}%]")


if __name__ == '__main__':
    eval_street_algorithm()
