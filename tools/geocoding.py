"""
Geocoding Tool
Converts addresses to lat/long coordinates
Searches for existing onsite energy installations in zipcode
"""
from geopy.geocoders import GoogleV3
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

import pandas as pd
from config.settings import INSTALLATIONS_XLSX

from dotenv import load_dotenv
from pathlib import Path
import os

# Using a relative path so it works on any machine, only if the '.env' file is 
# stored in the 'config' folder within the 'ensite' repository
env_path = Path(__file__).parent.parent / 'config' / '.env'
load_dotenv(dotenv_path=env_path)

INSTALLATIONS_XLSX = os.path.join(INSTALLATIONS_XLSX)
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

#If the API key is not able to be located an appropriate message will be displayed
if not GOOGLE_MAPS_API_KEY:
    raise EnvironmentError(
        "GOOGLE_MAPS_API_KEY not found. "
        "Check that config/production.env exists and contains the key.")
           
def geocode_address(address: str) -> dict:
    """
    Converts a street address to lat/long coordinates.

    Args:
        address: Full street address

    Returns:
        dict with success, latitude, longitude,
        formatted_address, confidence
     """    
    try: 
        geolocator = GoogleV3(api_key=GOOGLE_MAPS_API_KEY)
        location = geolocator.geocode(
            address,
            timeout = 10,
            components={"country":"US"})
        
        if location:
           return {
               "success": True,
               "latitude": location.latitude,
               "longitude": location.longitude,
               "formatted_address": location.address,
               "source": "GoogleV3",
               "confidence": "high"
                  }
       
        if GOOGLE_MAPS_API_KEY is None:
            print("Warning: GOOGLE_MAPS_API_KEY not found.")
    
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"Error: {e}")                   
    # Return failure if all geocoders fail
    return {
         "success": False,
         "error": f"Could not geocode: {address}",
         "suggestion": "Try adding zip code or state to address"  
             }
def reverse_geocode(
    latitude: float,
    longitude: float
) -> dict:
    """
    Converts lat/lon coordinates to a formatted
    street address using the Google Maps API.

    Args:
        latitude:  Facility latitude coordinate
        longitude: Facility longitude coordinate

    Returns:
        dict with:
        - success:           True/False
        - formatted_address: Formatted street address
        - source:            "GoogleV3"
        - confidence:        high/medium/low
        - error:             Error message if failed
    """
    try:
        geolocator = GoogleV3(api_key=GOOGLE_MAPS_API_KEY)
        location = geolocator.reverse(
            f"{latitude}, {longitude}",
            timeout=10,
            exactly_one=True   # Return only the best match
        )

        if location:
            return {
                "success":           True,
                "formatted_address": location.address,
                "source":            "GoogleV3",
                "confidence":        "high"
            }

        return {
            "success": False,
            "error": (
                f"No address found for coordinates "
                f"{latitude}, {longitude}"
            ),
            "suggestion": (
                "Verify the coordinates are correct."
            )
        }

    except (GeocoderTimedOut, GeocoderServiceError) as e:
        return {
            "success": False,
            "error":   f"Reverse geocoding failed: {e}",
            "suggestion": (
                "Check that the Google Maps API key is valid "
                "and has the Geocoding API enabled."
            )
        }
def main():
    #Prompt the user for their address
    try:
        address = str(input("Enter your address:"))
    except (ValueError, TypeError):
        print("Must enter a valid address.")
        return   
    #Run geocode_address function
    if address:
        result = geocode_address(address)
        print("lat =", result["latitude"])
        print("lon =",result["longitude"])

#     """----Uncomment to Validate Tool---"""
    result = geocode_address(address)
    print("Source:",result["source"])
    print("Latitude:",result["latitude"])
    print("Longitude:",result["longitude"])
    print(result["formatted_address"])

#if __name__ == "__main__":
#   main()

def load_installations(filepath: str) -> pd.DataFrame:
    """
    Loads onsite energy installation records from
    an Excel spreadsheet into a pandas DataFrame.

    Transformations applied:
        1. Strip leading/trailing whitespace from
           all string columns
        2. Standardize column names to lowercase
           with underscores (e.g. "Site Name" → "site_name")
        3. Pad zip codes with leading zeros to ensure
           all values are 5 digits
           (e.g. 3824 → "03824")

    Args:
        filepath: Path to the Excel file

    Returns:
        Cleaned DataFrame of installation records,
        or empty DataFrame if load failed
    """
    try:
        df = pd.read_excel(
            filepath,
            dtype={"Zip Code": str}  # Preserve any existing leading zeros
                                     # before column renaming occurs
        )

        # Step 1: Strip leading/trailing whitespace from all string columns
        str_cols = df.select_dtypes(include="object").columns
        df[str_cols] = df[str_cols].apply(lambda col: col.str.strip())

        # Step 2: Standardize column names to lowercase with underscores
        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
        )

        # Step 3: Pad zip codes with leading zeros
        if "zip_code" in df.columns:
            df["zip_code"] = (
                df["zip_code"]
                .astype(str)
                .str.strip()
                .str.zfill(5)
            )
        else:
            print(
                "Warning: 'Zip Code' column not found. "
                "Zip code padding was not applied.\n"
                f"Available columns: {df.columns.tolist()}"
            )

        print(f"Loaded {len(df)} records, {len(df.columns)} columns")
        print(f"Columns: {df.columns.tolist()}")

        return df

    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return pd.DataFrame()

    except Exception as e:
        print(f"Error loading file: {e}")
        return pd.DataFrame()

def get_installations_by_zipcode(
    df: pd.DataFrame,
    zipcode: str,
    zip_col: str = "zip_code"
) -> dict:
    """
    Filters the installations DataFrame to return
    all records matching a specific zip code.

    Args:
        df:       DataFrame of installation records
                  loaded by load_installations()
        zipcode:  5-digit zip code to search for
        zip_col:  Name of the zip code column in the
                  DataFrame

    Returns:
        dict with:
        - success:       True/False
        - zipcode:       Zip code queried
        - count:         Number of installations found
        - installations: List of installation records
        - error:         Error message if failed
    """

    # ==========================================
    # Validate DataFrame
    # ==========================================
    if df is None or df.empty:
        return {
            "success": False,
            "zipcode": zipcode,
            "count":   0,
            "error":   "Installations DataFrame is empty or None",
            "suggestion": (
                "Run load_installations() first to "
                "load the Excel spreadsheet."
            )
        }

    # ==========================================
    # Validate zip code column exists
    # ==========================================
    if zip_col not in df.columns:
        return {
            "success": False,
            "zipcode": zipcode,
            "count":   0,
            "error": (
                f"Column '{zip_col}' not found in DataFrame.\n"
                f"Available columns: {df.columns.tolist()}"
            ),
            "suggestion": (
                f"Pass the correct column name using the "
                f"zip_col argument. For example: "
                f"get_installations_by_zipcode(df, '{zipcode}', "
                f"zip_col='postal_code')"
            )
        }

    # ==========================================
    # Validate zip code input
    # ==========================================
    if zipcode is None:
        return {
            "success": False,
            "zipcode": zipcode,
            "count":   0,
            "error":   "Zip code cannot be None",
            "suggestion": (
                "Provide a 5-digit zip code as a string. "
                "Example: '03824'"
            )
        }

    # Strip whitespace and validate format
    # Must be exactly 5 digits
    zipcode = str(zipcode).strip()
    if not zipcode.isdigit() or len(zipcode) != 5:
        return {
            "success": False,
            "zipcode": zipcode,
            "count":   0,
            "error": (
                f"'{zipcode}' is not a valid 5-digit zip code."
            ),
            "suggestion": (
                "Provide a 5-digit zip code as a string. "
                "Example: '03824'. If your zip code has a +4 "
                "extension (e.g. '03824-1234'), pass only "
                "the first 5 digits."
            )
        }

    # ==========================================
    # Normalize zip column to string to prevent
    # type mismatch (e.g. int 3824 vs str "03824")
    # ==========================================
    zip_series = df[zip_col].astype(str).str.strip().str.zfill(5)

    # ==========================================
    # Filter DataFrame by zip code
    # ==========================================
    matched = df[zip_series == zipcode]

    if matched.empty:
        return {
            "success":       False,
            "zipcode":       zipcode,
            "count":         0,
            "installations": [],
            "error": (
                f"No installations found in zip code {zipcode}."
            ),
            "suggestion": (
                "Verify the zip code is correct, or check "
                "that the spreadsheet contains records "
                "for this area."
            )
        }

    # ==========================================
    # Convert matched rows to list of dicts
    # ==========================================
    installations = matched.to_dict(orient="records")

    return {
        "success":       True,
        "zipcode":       zipcode,
        "count":         len(installations),
        "installations": installations
    }

def validate(df):
    print("\n=== Installation Lookup ===")
    zipcode = input("Enter a 5‑digit ZIP code: ").strip()

    result = get_installations_by_zipcode(df, zipcode)

    print("\n=== Lookup Result ===")
    print(f"Success: {result['success']}")
    print(f"ZIP Code Queried: {result['zipcode']}")
    print(f"Count: {result['count']}")

    # If failed, show error + suggestion
    if not result["success"]:
        print(f"Error: {result.get('error', 'Unknown error')}")
        if "suggestion" in result:
            print(f"Suggestion: {result['suggestion']}")
        return

    # If successful, print each installation record
    print("\nInstallations:")
    for i, inst in enumerate(result["installations"], start=1):
        print(f"\n--- Installation {i} ---")
        for key, value in inst.items():
            print(f"{key}: {value}")
# -------- UNCOMMENT to Validate---------
#df = load_installations(INSTALLATIONS_XLSX)
#validate(df)