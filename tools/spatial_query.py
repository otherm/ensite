# -*- coding: utf-8 -*-
"""
Created on Wed Jun  3 13:47:56 2026

@author: jmd1
"""

import geopandas as gpd
from shapely.geometry import Point

import os

#GIS path
from config.settings import (
    SHAPEFILE_PATH
)

# 1. Define your target coordinate (Lat/Lon)
lat, lon = 43.134, -70.926  # Example: Durham, NH area

# Note: Shapely Points take coordinates as (longitude, latitude)
point = Point(lon, lat)

# 2. Create a GeoDataFrame for your coordinate with WGS84 CRS (EPSG:4326)
point_gdf = gpd.GeoDataFrame(
    index=[0],
    geometry=[point],
    crs="EPSG:4326"
)

# 3.  Identify shapefile to use, in this case it is the utility shapefile
utility_shp = os.path.join(SHAPEFILE_PATH, "New_England_Electric_Utilitiesv2a.shp")
utility_shapefile_gdf = gpd.read_file(utility_shp)

# 4. Ensure your shapefile CRS matches the lat/long CRS
if utility_shapefile_gdf.crs != "EPSG:4326":
    utility_shapefile_gdf = utility_shapefile_gdf.to_crs("EPSG:4326")

# 5. Perform a spatial join to find the intersecting polygon
# (This adds shapefile attributes to our point DataFrame)
joined_gdf = gpd.sjoin(point_gdf, utility_shapefile_gdf, predicate="within")

# 6. Extract the attribute value
if not joined_gdf.empty:
    # Replace 'YOUR_COLUMN_NAME' with the field you want to extract
    attribute_value = joined_gdf['Utility_Na'].iloc[0]
    print(f"Attribute found: {attribute_value}")
else:
    print("The given coordinates are outside the shapefile boundaries.")
