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

import logging
import os
import re
import geopandas as gpd
from shapely.geometry import Point
from tools.geocoding import geocode_address, reverse_geocode
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
_doe_dac_gdf = None
_iwg_gdf = None

UTILITY_SHAPEFILE = os.path.join(SHAPEFILE_DIR, 'New_England_Electric_Utilitiesv2a.shp')
DOE_DAC_SHAPEFILE = os.path.join(SHAPEFILE_DIR, 'DOE_DACs.shp')
IWG_DATABASE = os.path.join(SHAPEFILE_DIR, 'IWG_manufacturers.dbf')

ROAD_TYPE_EXPANSIONS = {
    "ALY":  "ALLEY",
    "AVE":  "AVENUE",
    "BLVD": "BOULEVARD",
    "CIR":  "CIRCLE",
    "CT":   "COURT",
    "CV":   "COVE",
    "DR":   "DRIVE",
    "EXPY": "EXPRESSWAY",
    "HWY":  "HIGHWAY",
    "LN":   "LANE",
    "PKWY": "PARKWAY",
    "PL":   "PLACE",
    "PT":   "POINT",
    "RD":   "ROAD",
    "SQ":   "SQUARE",
    "ST":   "STREET",
    "TER":  "TERRACE",
    "TRL":  "TRAIL",
    "WAY":  "WAY",
}
def _load_utility_shp():
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
def _load_dac_shp():
    """
    Loads the DAC (DisAdvantaged Communities) shapefile into
    memory and caches it in _dac_gdf.

    Called automatically by find_DACSTS() on
    first use. Subsequent calls return the
    cached GeoDataFrame without re-reading disk.

    Returns:
        GeoDataFrame or None if load failed
    """
    global _doe_dac_gdf

    # Already loaded — return cached version
    if _doe_dac_gdf is not None:
        logger.debug("Returning cached shapefile")
        return _doe_dac_gdf

    # Check shapefile exists before trying to load
    if not DOE_DAC_SHAPEFILE:
        logger.error(
            f"Shapefile not found: {DOE_DAC_SHAPEFILE}\n"
            f"  Expected location: {DOE_DAC_SHAPEFILE}\n"
            f"  SHAPEFILE_DIR is:  {SHAPEFILE_DIR}\n"
            f"  Fix: Download shapefile and place in "
            f"  {SHAPEFILE_DIR}"
        )
        return None

    # Load the shapefile
    try:
        logger.info(f"Loading shapefile: {DOE_DAC_SHAPEFILE}")
        gdf = gpd.read_file(str(DOE_DAC_SHAPEFILE))

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
        _doe_dac_gdf = gdf
        logger.info("Shapefile loaded and cached successfully")
        return _doe_dac_gdf

    except Exception as e:
        logger.error(f"Failed to load shapefile: {e}")
        return None

def _load_iwg_dbf():
    """
    Loads the IWG Manufacturer database into
    memory and caches it in _iwg_gdf.

    Called automatically by find_IWG() on
    first use. Subsequent calls return the
    cached GeoDataFrame without re-reading disk.

    Returns:
        GeoDataFrame or None if load failed
    """
    global _iwg_gdf

    # Already loaded — return cached version
    if _iwg_gdf is not None:
        logger.debug("Returning cached IWG database")
        return _iwg_gdf

    # Check shapefile exists before trying to load
    if not IWG_DATABASE:
        logger.error(
            f"Database not found: {IWG_DATABASE}\n"
            f"  Expected location: {IWG_DATABASE}\n"
            f"  SHAPEFILE_DIR is:  {SHAPEFILE_DIR}\n"
            f"  Fix: Download IWG_manufacturers.dbf and place in "
            f"  {SHAPEFILE_DIR}"
        )
        return None

    # Load the shapefile
    try:
        logger.info(f"Loading database: {IWG_DATABASE}")
        gdf = gpd.read_file(str(IWG_DATABASE))
        """
        # Filter to New England states only
        # Makes spatial queries faster
        //
        if "STATE" in gdf.columns:
            ne_fips = list(NEW_ENGLAND_STATE_FIPS.values())
            gdf = gdf[gdf["STATE"].isin(ne_fips)]
            logger.info(
                f"Filtered to New England "                
            )
        elif "STATEFP" in gdf.columns:
            ne_fips = list(NEW_ENGLAND_STATE_FIPS.values())
            gdf = gdf[gdf["STATEFP"].isin(ne_fips)]
            logger.info(
                f"Filtered to New England: "
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
        _iwg_gdf = gdf
        logger.info("Database loaded and cached successfully")
        return _iwg_gdf

    except Exception as e:
        logger.error(f"Failed to load database: {e}")
        return None

def _normalize_address(address) -> str:
    """
    Normalizes a Google Maps formatted address to match
    the formatting used in the IWG DBF file.

    Transformations applied:
        1. Convert to uppercase
        2. Remove ", USA" suffix added by Google Maps API
        3. Expand road type abbreviations word by word,
           but only when the abbreviation appears directly
           before a comma or at the end of the street
           segment (i.e. is acting as a road type suffix)

    Args:
        formatted_address: Raw address string from Google Maps API

    Returns:
        Normalized address string matching DBF format

    Examples:
        "123 Main St, Durham, NH 03824, USA"
        → "123 MAIN STREET, DURHAM, NH 03824"

        "456 Oak Blvd, Providence, RI 02903, USA"
        → "456 OAK BOULEVARD, PROVIDENCE, RI 02903"

        "123 St Mary's Rd, Newport, RI 02840, USA"
        → "123 ST MARY'S ROAD, NEWPORT, RI 02840"
    """
    if not address:
        return address

    address = address.upper().strip()
    address = address.removesuffix(", USA")

    segments = address.split(",")
    normalized_segments = []

    for i, segment in enumerate(segments):
        segment = segment.strip()
        words = segment.split()

        # Only expand the LAST word of the FIRST segment
        # (the street address segment) since road type
        # suffixes only appear at the end of street names
        if i == 0 and words:
            last_word = words[-1]
            if last_word in ROAD_TYPE_EXPANSIONS:
                words[-1] = ROAD_TYPE_EXPANSIONS[last_word]

        normalized_segments.append(" ".join(words))

        address = ", ".join(normalized_segments)

        address = re.sub(r'([A-Z]{2}) (\d{5}(?:-\d{4})?)', r'\1, \2', address)

    return address

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
    gdf = _load_utility_shp()

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
def find_dacsts(
    latitude: float,
    longitude: float
) -> dict:
    """
        Determines the DAC (DisAdvantaged Communities)
        Status of a location using a spatial point-in-polygon
        query against DOE_DACs shapefiles.

        Args:
            latitude:  Facility latitude coordinate
            longitude: Facility longitude coordinate

        Returns:
            dict with:
            - success: True/False
            - DACSTS: True/False
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
    gdf = _load_dac_shp()

    if gdf is None:
        return {
            "success": False,
            "error": "DOE_DAC shapefile could not be loaded",
            "suggestion": (
                f"Check that shapefile exists at: "
                f"{DOE_DAC_SHAPEFILE}"
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

    # Extract the attribute value
    joined_gdf = gpd.sjoin(point_gdf, gdf, predicate="within")

    if not joined_gdf.empty:
        DACSTS = joined_gdf['DACSTS'].iloc[0]
        city = joined_gdf['city'].iloc[0]
        county = joined_gdf['county'].iloc[0]
        stateabb = joined_gdf['stateabb'].iloc[0]

        logger.info(
            f"DAC status found: {DACSTS} "
            f"({city}, {county}, {stateabb})"
        )

        return {
            "success": True,
            "DACSTS": str(DACSTS),
            "city": str(city),
            "stateabb": str(stateabb),
            "iso_region": "ISO New England (ISO-NE)",
            "confidence": "high",
            "source": "DOE DAC Shapefile",
            "coordinates_queried": {
                "latitude": latitude,
                "longitude": longitude
            }
        }

    else:
        # Point not found in any polygon
        # May be on a boundary or outside coverage
        logger.warning(
            f"No DAC status found at "
            f"{latitude}, {longitude}"
        )
        return {
            "success": False,
             "error": (
                f"No DAC status found for "
                f"coordinates {latitude}, {longitude}"
            ),
            "suggestion": (
                "Location may be on a DAC boundary. "
                "Try a nearby address instead."
            ),
            "coordinates_queried": {
                "latitude": latitude,
                "longitude": longitude
            }
        }

def find_iwg(
    latitude: float,
    longitude: float
) -> dict:
    """
    Determines if address is listed in IWG (Industrial
    Working Group) database.

    Args:
        latitude:  Facility latitude coordinate
        longitude: Facility longitude coordinate

    Returns:
        dict with:
        - success:     True/False
        - IWG_status:  True/False
        - name:        Name of facility
        - facility_a:  Address of facility
        - naics:       NAICS code of facility
        - confidence:  high/medium/low
        - error:       Error message if failed
    """
    if latitude is None or longitude is None:
        return {
            "success": False,
            "IWG_status": False,
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
            "IWG_status": False,
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
            "IWG_status": False,
            "error": (
                f"Longitude {longitude} is outside "
                f"New England range (-73.7 to -66.9)"
            ),
            "suggestion": (
                "ENSITE currently covers New England only. "
                "Verify the address is in CT, MA, ME, NH, RI, or VT."
            )
        }

    # ==========================================
    # FIX 2: Load shapefile using cache only
    # Do NOT call gpd.read_file() again below
    # ==========================================
    gdf = _load_iwg_dbf()

    if gdf is None:
        return {
            "success": False,
            "IWG_status": False,
            "error": "IWG_Manufacturers database could not be loaded",
            "suggestion": (
                f"Check that database exists at: "
                f"{IWG_DATABASE}"
            )
        }

    geocode_result = reverse_geocode(
        latitude=latitude,
        longitude=longitude
    )
# ------ UNCOMMENT to test geocode_result---------
#    print(geocode_result["formatted_address"],"boof")
    if not geocode_result["success"]:
        return {
            "success": False,
            "IWG_status": False,
            "error": (
                f"Could not reverse geocode coordinates "
                f"{latitude}, {longitude}: "
                f"{geocode_result.get('error', 'Unknown error')}"
            ),
            "suggestion": geocode_result.get(
                "suggestion",
                "Check that the Google Maps API key is valid."
            )
        }

    # Normalize formatted address to match DBF format:
    # - Uppercase
    # - Remove ", USA" suffix
    # - Expand road type abbreviations
    formatted_address = _normalize_address(
        geocode_result["formatted_address"]
    )
    # ---UNCOMMENT to test formatted_address---
    #print(formatted_address,"boof")
    attributes = gdf[gdf['facility_a'] == formatted_address]

    # FIX 5: Use .empty to properly evaluate match
    if not attributes.empty:
        # Extract attributes from the matched row only
        name = attributes['name'].iloc[0]
        facility_a = attributes['facility_a'].iloc[0]
        naics_ni_c = attributes['naics_ni_c'].iloc[0]

        logger.info(
            f"IWG match found: {name} "
            f"({facility_a}, NAICS: {naics_ni_c})"
        )

        return {
            "success":    True,
            "IWG_status": True,
            "name":       str(name),
            "facility_a": str(facility_a),
            "naics_ni_c": str(naics_ni_c),
            "confidence": "high",
            "source":     "IWG Manufacturers Database",
            "coordinates_queried": {
                "latitude":  latitude,
                "longitude": longitude
            }
        }

    else:
        logger.warning(
            f"No IWG status found at "
            f"{latitude}, {longitude}"
        )
        return {
            "success":    False,
            "IWG_status": False,      # FIX 6: Added IWG_status
            "error": (
                f"No IWG facility found for "
                f"coordinates {latitude}, {longitude}"
            ),
            "suggestion": (
                "Location may not be listed in the IWG database. "
                "Try a nearby address instead."
            ),
            "coordinates_queried": {
                "latitude":  latitude,
                "longitude": longitude
            }
        }
def get_shapefile_info(target: str) -> dict:
    """
    Returns diagnostic information about the
    loaded shapefile. Useful for debugging.

    Args:
        target: Which shapefile to inspect
            "utility" - utility territory shapefile
            "dac" - DAC territory shapefile
            "iwg" - IWG territory shapefile
    Returns:
    dict with shapefile metadata
    """
    if target == "utility":
        path = os.path.join(UTILITY_SHAPEFILE)
        gdf = gpd.read_file(path)
    elif target == "dac":
        path = os.path.join(DOE_DAC_SHAPEFILE)
        gdf = gpd.read_file(path)
    elif target == "iwg":
        path = os.path.join(IWG_DATABASE)
        gdf = gpd.read_file(path)
    else:
        return{
            "loaded":False,
            "error": (
                f"Unknown target: '{target}'\n"
                f"  Valid targets are: 'utility', 'dac', 'iwg'"
            )
        }
    if gdf is None:
        return {
            "loaded": False,
            "path": str(path),
            "exists": os.path.exists(path)
        }

    return {
        "loaded": True,
        "target": target,
        "path": str(path),
        "exists": True,
        "row_count": len(gdf),
        "columns": gdf.columns.tolist(),
        "crs": str(gdf.crs),
        "bounds": gdf.total_bounds.tolist()
    }

def reset_cache(target: str = "all"):
    """
    Clears the cached shapefile.
    Useful for testing or if shapefile changes.

    Args:
        target: Which cache to clear
            "utility" - clears utility shapefile cache
            "dac" - clears DAC shapefile cache
            "iwg" - clears IWG shapefile cache
            "all" - clears all shapefile caches
    """
    global _utility_gdf,_doe_dac_gdf, _iwg_gdf

    if target == "utility":
        _utility_gdf = None
        logger.info("Utility shapefile cache cleared")
    elif target == "dac":
        _doe_dac_gdf = None
        logger.info("DAC shapefile cache cleared")
    elif target == "iwg":
        _iwg_gdf = None
        logger.info("IWG shapefile cache cleared")
    else:
        logger.warning(
            f"Unrecognized cache target: {target}"
            f"  Valid options: {['utility', 'dac', 'iwg', 'all']}"
        )

# ==========================================================
#            UNCOMMENT TO VALIDATE TOOL
# ==========================================================
# address = input("Enter address: ")
# geocode_address(address)
# result = geocode_address(address)
# latitude = result["latitude"]
# longitude = result["longitude"]
#
# def validate(latitude, longitude):
#     _load_utility_shp()
#     _load_dac_shp()
#     _load_iwg_dbf()
#     find_utility(longitude, latitude)
#     find_dacsts(longitude, latitude)
#     find_iwg(longitude, latitude)
#
# validate(longitude,latitude)



