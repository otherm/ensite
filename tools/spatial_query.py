"""
tools/spatial_query.py
=============================================
Performs spatial point-in-polygon queries
against New England utility territory shapefiles.

Identifies which electric utility serves
a given latitude/longitude coordinate.

Fixed:
  - Explicit global declaration in _load_shapefile()
  - Defensive initialization of _utility_gdf
  - Clear error messages for missing shapefile

Author: ENSITE Project, UNH
Date: June 2026
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

import logging
import os
import geopandas as gpd
from shapely.geometry import Point
from config.settings import (
    SHAPEFILE_DIR,
    NEW_ENGLAND_STATES,
    NEW_ENGLAND_STATE_FIPS,
    GIS_CRS
)

logger = logging.getLogger(__name__)

# ============================================
# MODULE LEVEL CACHE
# ============================================
# Defined here at module level so it persists
# between function calls.
#
# None  = not loaded yet
# GeoDataFrame = already loaded, reuse it
#
# This means we only read the shapefile from
# disk ONCE no matter how many queries we run.
# ============================================
_utility_gdf = None

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


# Build the shapefile path using SHAPEFILE_DIR
# from settings.py (folder) + filename
# This is set once at module load time
UTILITY_SHAPEFILE = os.path.join(SHAPEFILE_DIR, 'New_England_Electric_Utilitiesv2a.shp')


def _load_shapefile():
    """
    Loads the utility territory shapefile into
    memory and caches it in _utility_gdf.

    Called automatically by find_utility() on
    first use. Subsequent calls return the
    cached GeoDataFrame without re-reading disk.

    Returns:
        GeoDataFrame or None if load failed
    """
    # ==========================================
    # THIS IS THE CRITICAL FIX:
    # global declaration MUST be here so Python
    # knows we mean the MODULE LEVEL _utility_gdf
    # not a new local variable inside this function
    # ==========================================
    global _utility_gdf

    # Already loaded — return cached version
    if _utility_gdf is not None:
        logger.debug("Returning cached shapefile")
        return _utility_gdf

    # Check shapefile exists before trying to load
    if not UTILITY_SHAPEFILE:
        logger.error(
            f"Shapefile not found: {UTILITY_SHAPEFILE}\n"
            f"  Expected location: {UTILITY_SHAPEFILE}\n"
            f"  SHAPEFILE_DIR is:  {SHAPEFILE_DIR}\n"
            f"  Fix: Download shapefile and place in "
            f"  {SHAPEFILE_DIR}"
        )
        return None

    # Load the shapefile
    try:
        logger.info(f"Loading shapefile: {UTILITY_SHAPEFILE}")
        gdf = gpd.read_file(str(UTILITY_SHAPEFILE))

        # Convert to standard GPS coordinate system
        # EPSG:4326 = WGS84 = standard lat/lon
        logger.info(
            f"Converting CRS from {gdf.crs} to {GIS_CRS}"
        )
        #gdf = gdf.to_crs(GIS_CRS)
        """
        # Filter to New England states only
        # Makes spatial queries faster
        //
        if "STATE" in gdf.columns:
            ne_fips = list(NEW_ENGLAND_STATE_FIPS.values())
            gdf = gdf[gdf["STATE"].isin(ne_fips)]
            logger.info(
                f"Filtered to New England: "
                f"{len(gdf)} utility territories"
            )
        elif "STATEFP" in gdf.columns:
            ne_fips = list(NEW_ENGLAND_STATE_FIPS.values())
            gdf = gdf[gdf["STATEFP"].isin(ne_fips)]
            logger.info(
                f"Filtered to New England: "
                f"{len(gdf)} utility territories"
            )
        else:
            logger.warning(
                "No STATE or STATEFP column found. "
                "Cannot filter to New England. "
                f"Available columns: {gdf.columns.tolist()}"
            )
        """
        # Cache in module level variable
        # global declaration above makes this work!
        _utility_gdf = gdf
        logger.info("Shapefile loaded and cached successfully")
        return _utility_gdf

    except Exception as e:
        logger.error(f"Failed to load shapefile: {e}")
        return None


def find_utility(
    latitude: float,
    longitude: float
) -> dict:
    """
    Identifies the electric utility serving
    a location using a spatial point-in-polygon
    query against utility territory shapefiles.

    Args:
        latitude:  Facility latitude coordinate
        longitude: Facility longitude coordinate

    Returns:
        dict with:
        - success: True/False
        - utility_name: Name of serving utility
        - utility_id: EIA utility ID
        - state: Two-letter state code
        - iso_region: ISO New England
        - confidence: high/medium/low
        - error: Error message if failed
    """

    # Validate inputs
    if latitude is None or longitude is None:
        return {
            "success": False,
            "error": "Latitude and longitude cannot be None",
            "suggestion": (
                "Run geocoding first to get coordinates"
            )
        }

    # Validate coordinate ranges
    # New England is roughly:
    # Lat: 41.0 to 47.5
    # Lon: -73.7 to -66.9
    if not (41.0 <= latitude <= 47.5):
        return {
            "success": False,
            "error": (
                f"Latitude {latitude} is outside "
                f"New England range (41.0 to 47.5)"
            ),
            "suggestion": (
                "ENSITE currently covers New England only. "
                "Verify the address is in CT, MA, ME, NH, RI, or VT."
            )
        }

    if not (-73.7 <= longitude <= -66.9):
        return {
            "success": False,
            "error": (
                f"Longitude {longitude} is outside "
                f"New England range (-73.7 to -66.9)"
            ),
            "suggestion": (
                "ENSITE currently covers New England only. "
                "Verify the address is in CT, MA, ME, NH, RI, or VT."
            )
        }

    # Load shapefile (uses cache after first call)
    gdf = _load_shapefile()

    if gdf is None:
        return {
            "success": False,
            "error": "Utility shapefile could not be loaded",
            "suggestion": (
                f"Check that shapefile exists at: "
                f"{UTILITY_SHAPEFILE}"
            )
        }

    # Create point geometry
    # NOTE: Shapely Point takes (longitude, latitude)
    # NOT (latitude, longitude)!
    # This is a very common source of bugs!
    point = Point(longitude, latitude)

    point_gdf = gpd.GeoDataFrame(
        index=[0],
        geometry=[point],
        crs="EPSG:4326"
    )
    bounds = gdf.total_bounds
    if not (bounds[0] <= longitude <= bounds[2] and bounds[1] <= latitude <= bounds[3]):
        return {
            "success": False,
            "error": (
                f"Coordinates {latitude}, {longitude} are outside the shapefile bounds"
            ),
            "suggestion": (
                "Ensure the coordinates are within the New England region."
            )
        }

    # Perform spatial query
    # Find which utility territory polygon
    # contains our point
    # Perform a spatial join to find the intersecting polygon
    # This adds shapefile attributes to our point DataFrame

    else:
        print("The given coordinates are inside the shapefile boundaries.")

    # Extract the attribute value
    joined_gdf = gpd.sjoin(point_gdf, gdf, predicate="within")

    if not joined_gdf.empty:
        utility_name = joined_gdf['Utility_Na'].iloc[0]
        utility_type = joined_gdf['Utility_Ty'].iloc[0]
        state_name = joined_gdf['STATE'].iloc[0]
        state_code = next((k for k, v in NEW_ENGLAND_STATES.items() if v == state_name), None)

        logger.info(
            f"Utility found: {utility_name} "
            f"({state_code})"
        )

        return {
            "success": True,
            "utility_name": str(utility_name),
            "utility_type": str(utility_type),
            "state": str(state_code),
            "iso_region": "ISO New England (ISO-NE)",
            "confidence": "high",
            "source": "HIFLD Utility Territory Shapefile",
            "coordinates_queried": {
                "latitude": latitude,
                "longitude": longitude
            }
        }

    else:
        # Point not found in any polygon
        # May be on a boundary or outside coverage
        logger.warning(
            f"No utility found at "
            f"{latitude}, {longitude}"
        )
        return {
            "success": False,
             "error": (
                f"No utility territory found for "
                f"coordinates {latitude}, {longitude}"
            ),
            "suggestion": (
                "Location may be on a utility boundary. "
                "Try a nearby address or contact the "
                "state PUC directly to identify the utility."
            ),
            "coordinates_queried": {
                "latitude": latitude,
                "longitude": longitude
            }
        }


def get_shapefile_info() -> dict:
    """
    Returns diagnostic information about the
    loaded shapefile. Useful for debugging.

    Returns:
    dict with shapefile metadata
    """
    gdf = _load_shapefile()

    if gdf is None:
        return {
            "loaded": False,
            "path": str(UTILITY_SHAPEFILE),
            "exists": UTILITY_SHAPEFILE.exists()
        }

    return {
        "loaded": True,
        "path": str(UTILITY_SHAPEFILE),
        "exists": True,
        "row_count": len(gdf),
        "columns": gdf.columns.tolist(),
        "crs": str(gdf.crs),
        "bounds": gdf.total_bounds.tolist()
    }


def reset_cache():
    """
    Clears the cached shapefile.
    Useful for testing or if shapefile changes.
    """
    global _utility_gdf
    _utility_gdf = None
    logger.info("Shapefile cache cleared")

