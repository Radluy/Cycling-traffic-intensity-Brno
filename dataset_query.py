import requests
from configparser import ConfigParser
from arcgis.features import FeatureLayer


# ARCGIS api has request limit of 1000-2000 records per query, use python gis lib
def download_dataset(base_url: str, savepath: str):
    params = {'where': '1=1', 'outFields': '*', 'outSR': 4326, 'f': 'geojson'}
    response = requests.get(base_url, params=params)
    with open(savepath, 'w') as f:
        f.write(response.text)


def query_arcgis_layer(base_url: str, savepath: str | None = None, out_fields: str = '*',
                       custom_where: str = "1=1", result_type: str = 'geojson'):
    """Query all data from ArcGIS FeatureLayer and save to geoJSON file
    Args:
        base_url (str): url of arcGIS FeatureLayer to query
        savepath (str, optional): path where data will be saved, don't save if left empty
        out_fields (str, optional): string of comma separated fields to query, defaults to '*'.
        custom_where (str, optional): custom WHERE sql-like clause, defaults to '1=1'
        result_type (str, optional): type or format of result, defaults to 'geojson'"""
    layer = FeatureLayer(base_url)
    response = layer.query(where=custom_where, 
                           out_fields=out_fields, 
                           outSR=4326, 
                           f=result_type)
    if savepath:
        with open(savepath, 'w') as f:
            f.write(response.to_geojson)
    else:
        print(response)


if __name__ == '__main__':
    cparser = ConfigParser()
    cparser.read('data_urls.conf')
    # download_dataset(cparser['urls']['counters'], 'datasets/testik.geojson')
    query_arcgis_layer(cparser['urls']['census'], 
                       'datasets/arcgis_bkom.geojson', 
                       out_fields='id')
    
    query_arcgis_layer(cparser['urls']['counters'], 
                       'datasets/arcgis_counters.geojson', 
                       out_fields='LocationId')
    
    query_arcgis_layer(cparser['urls']['biketowork'], 
                       'datasets/arcgis_biketowork.geojson', 
                       out_fields='GID_ROAD')

    #query_arcgis_layer(cparser['urls']['biketowork'], 
    # result_type='df',custom_where='GID_ROAD=3515.0')