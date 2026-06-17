# -*- coding: utf-8 -*-
"""
Created on Wed Jun  3 13:47:56 2026

@author: jmd1
"""
import geopandas as gpd
from shapely.geometry import Point
from geocoding import geocode_address
import os

# GIS path
from config.settings import (SHAPEFILE_PATH)

# Prompt user for address
address = input("Enter your address:")
result = geocode_address(address)

if not result["success"]:
    print("Address not found.")
    exit()

# Search IWG Database BEFORE geocode address is converted to lat, lon coordinates
IWG_manufacturers_shp = os.path.join(SHAPEFILE_PATH, "IWG_manufacturers.shp")
IWG_manufacturers_gdf = gpd.read_file(IWG_manufacturers_shp)

formatted_address = result["formatted_address"]
if formatted_address:
    attribute_value = IWG_manufacturers_gdf['facility_a'].iloc[0]
    print(f"IWG Database: {attribute_value}")
else:
    print("0")

lat = result["latitude"]
lon = result["longitude"]

# Note: Shapely Points take coordinates as (longitude, latitude)
point = Point(lon, lat)

# Create a GeoDataFrame for your coordinate with WGS84 CRS (EPSG:4326)
point_gdf = gpd.GeoDataFrame(
    index=[0],
    geometry=[point],
    crs="EPSG:4326"
)

# Identify shapefile to use, in this case it is the utility shapefile
utility_shp = os.path.join(SHAPEFILE_PATH, "New_England_Electric_Utilitiesv2a.shp")
utility_shapefile_gdf = gpd.read_file(utility_shp)

# Ensure your shapefile CRS matches the lat/long CRS
if utility_shapefile_gdf.crs != "EPSG:4326":
    utility_shapefile_gdf = utility_shapefile_gdf.to_crs("EPSG:4326")

# Perform a spatial join to find the intersecting polygon
# This adds shapefile attributes to our point DataFrame
joined_gdf = gpd.sjoin(point_gdf, utility_shapefile_gdf, predicate="within")

# Extract the attribute value
if not joined_gdf.empty:
    attribute_value = joined_gdf['Utility_Na'].iloc[0]
    print(f"Utility: {attribute_value}")
else:
    print("The given coordinates are outside the shapefile boundaries.")

DAC_shp = os.path.join(SHAPEFILE_PATH, "DOE_DACs.shp")
DOE_DACs_gdf = gpd.read_file(DAC_shp)

if DOE_DACs_gdf.crs != "EPSG:4326":
    DOE_DACs_gdf = DOE_DACs_gdf.to_crs("EPSG:4326")

# Perform a spatial join to find the intersecting polygon
# (This adds shapefile attributes to our point DataFrame)
joinedDAC_gdf = gpd.sjoin(point_gdf, DOE_DACs_gdf, predicate="within")

# Extract the attribute value
if not joinedDAC_gdf.empty:
    attribute_value = joinedDAC_gdf['DACSTS'].iloc[0]
    print(f"DOE_DAC: {attribute_value}")
else:
    print("The given coordinates are outside the shapefile boundaries.")
