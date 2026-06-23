"""
Geocoding Tool
Converts addresses to lat/long coordinates
"""
from geopy.geocoders import GoogleV3
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

from dotenv import load_dotenv
from pathlib import Path
import os

# Using a relative path so it works on any machine, only if the '.env' file is 
# stored in the 'config' folder within the 'ensite' repository
env_path = Path(__file__).parent.parent / 'config' / '.env'
load_dotenv(dotenv_path=env_path)

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

if __name__ == "__main__":
    main()
