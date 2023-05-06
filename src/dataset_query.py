import requests
import pandas as pd
import matplotlib.dates as mdates
from configparser import ConfigParser
from arcgis.features import FeatureLayer
from matplotlib import pyplot as plt
from seaborn import lineplot


cparser = ConfigParser()
cparser.read('../data_urls.conf')

# ARCGIS api has request limit of 1000-2000 records per query, use python gis lib
def download_dataset(base_url: str, savepath: str):
    """Downloads full dataset from the arcgis featureLayer"""
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
        return response
    

def get_biketowork_data(gid: int):
    """Query biketowork dataset as dataframe based on road ID"""
    gdf = query_arcgis_layer(cparser['urls']['biketowork'],
                             result_type='df',
                             custom_where=f"GID_ROAD={gid}").sdf
    gdf = gdf[['data_2019', 'data_2020', 'data_2021', 'dpnk_22']]
    return gdf


def get_census_data(id: int):
    """Query census dataset as dataframe based on road ID"""
    gdf = query_arcgis_layer(cparser['urls']['census'],
                             result_type='df',
                             custom_where=f"id={id}").sdf
    gdf = gdf[["prac_2018", "vik_2018", "prac_2020",
               "vik_2020", "prac_2022", "vik_2022"]]
    return gdf


def get_counters_data(location_id: int, date_start: str, date_end: str):
    """Query counters dataset as dataframe based on locationId and time interval
       datetime parameters in format 'YYYY-MM-DD'"""
    gdf = query_arcgis_layer(cparser['urls']['counters'],
                             result_type='df',
                             custom_where=f"""LocationId={location_id}
                                              AND datum > DATE '{date_start}'
                                              AND datum < DATE '{date_end}'""").sdf
    gdf = gdf[['SecondDirection_Cyclists', 'FirstDirection_Cyclists']]
    return gdf


def get_strava_data(osm_id: int, date_start: str, date_end: str, csv_path: str) -> pd.DataFrame:
    """Query strava dataset from file as a dataframe based on OSM ID and time interval
       datetime parameters in format 'YYYY-MM-DD',
       dataset must be on daily granularity and contain the specified time frame"""
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    df = df[df['osm_reference_id'] == osm_id] # 48578321
    df = df[df['date'].dt.strftime('%Y-%m-%d') >= date_start]
    df = df[df['date'].dt.strftime('%Y-%m-%d') < date_end]
    df = df.groupby(['date']).mean().reset_index()
    df = df[['osm_reference_id', 'date', 'ride_count', 'forward_trip_count', 'reverse_trip_count']]
    return df


def generate_strava_report(osm_id: int, date_start: str, date_end: str, csv_path: str):
    """Generated simple html digesting strava data parsed by parameters
       datetime parameters in format 'YYYY-MM-DD'
       dataset must be on daily granularity and contain the specified time frame"""
    df = get_strava_data(osm_id, date_start, date_end, csv_path)
    fig = plt.figure(figsize=(10,8))
    ax = fig.gca()
    lineplot(x=df['date'], y=df['ride_count'], ax=ax)
    x = ax.lines[0].get_xydata()[:,0]
    y = ax.lines[0].get_xydata()[:,1]
    ax.fill_between(x,y, color="blue", alpha=0.6)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d'))
    plt.savefig('../strava_plot.png')
    sums = df.groupby(['osm_reference_id']).sum().reset_index()
    with open('../report.html', 'w') as f:
        f.write(df.to_html() +
                '<img src="strava_plot.png" alt="text">' +
                sums.to_html())



if __name__ == '__main__':
    # download_dataset(cparser['urls']['counters'], 'datasets/testik.geojson')
    """query_arcgis_layer(cparser['urls']['census'],
                       '../datasets/arcgis_bkom.geojson',
                       out_fields='id')

    query_arcgis_layer(cparser['urls']['counters'],
                       '../datasets/arcgis_counters.geojson',
                       out_fields='LocationId')

    query_arcgis_layer(cparser['urls']['biketowork'], 
                       '../datasets/arcgis_biketowork.geojson',
                       out_fields='GID_ROAD')"""

    # examples
    y = query_arcgis_layer(cparser['urls']['biketowork'],
                       result_type='df',
                       custom_where='GID_ROAD=3515.0').sdf

    x = query_arcgis_layer(cparser['urls']['counters'],
                           custom_where="datum > DATE '2023-03-22'",
                           result_type='df').sdf

    #generate_strava_report(450098706, '2022-05-01', '2022-05-31', '../datasets/strava_daily_2022_may_aug.csv')
