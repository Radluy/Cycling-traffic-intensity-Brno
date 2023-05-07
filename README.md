# Cycling-traffic-intensity-Brno

This project was created as a Master's thesis at the Faculty of Information Technology, Brno University of Technology. It introduces an innovative approach to integrating basemap datasets defining street networks. The algorithm is then used to unify multiple datasets regarding cycling numbers in Brno and the resulting model is visualized in a publicly available dashboard.

Datasets can be found at: <https://data.brno.cz> \
Dashboard can be found at: [dashboard](https://fitvut-xelias18.maps.arcgis.com/apps/dashboards/30441a5a3b6f497880474e5e70ccd3e7) \
(Note that there's currently an ArcGIS bug, where it might prompt you to log in. Closing this popup a few times will resolve this issue, if not, it's possible to register an account for free.)

This thesis was also submitted to the [EXCEL@FIT 2023](https://excel.fit.vutbr.cz/) conference, where it was awarded by an expert panel, as well as by industry partners. 
Submission: [poster](https://excel.fit.vutbr.cz/submissions/2023/030/30_poster.pdf), [abstract](https://excel.fit.vutbr.cz/submissions/2023/030/30.pdf)

---

## Installation

The installation process follows the standard Python procedure. All the necessary packages are defined in the `requirements.txt` file.
To build a closed, working environment, you need to:

- `python -m venv venv` (Create empty Python env in the root folder)
- `source venv/bin/activate` (Enable it)
- `python -m pip install -r requirements.txt` (Install required packages)

---

## Usage

All the methods for dataset matching are implemented in the `src/location_matching.py` source file, it can be imported to any Python application and used as a library. \
Specifically for the Brno list of datasets, the whole process is implemented as the main method of this script. However, it requires an exact filesystem structure and naming of the files. \

```tree
|- src/
|- datasets/
    |- czech_republic-latest.osm.pbf
    |- cyklodetektory.geojson
    |- do_prace_na_kole.geojson
    |- bkom_scitanie.geojson
```

Brno datasets can be downloaded from the ArcGIS hosted storage using the `query_arcgis_layer()` method from the `src/dateset_query.py` source file (examples are in the main function, but the documentation explains all the required parameters).

### Update workflow

How to update an existing model with a new version of end-dataset is demonstrated in the `src/update_example.py` file.

---

In case of any problems or questions, don't hesitate to contact me at [radoslave0@gmail.com](mailto:radoslave0@gmail.com).
