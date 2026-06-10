"""
Geocoding Tool
Converts addresses to lat/long coordinates
"""
from geopy.geocoders import Nominatim, GoogleV3
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import os
from config.settings import GOOGLE_MAPS_API_KEY if hasattr(
    __import__('config.settings', fromlist=['GOOGLE_MAPS_API_KEY']),
    'GOOGLE_MAPS_API_KEY'
) else None

def geocode_address(address: str) -> dict:
    """
    Converts a street address to lat/long coordinates.

    Args:
        address: Full street address

    Returns:
        dict with success, latitude, longitude,
        formatted_address, confidence
    """
    # Try Nominatim first (free, no API key needed)
    try:
        geolocator = Nominatim(user_agent="ensite_unh_v1")
        location = geolocator.geocode(
            address,
            timeout=10,
            country_codes="us"
        )

        if location:
            return {
                "success": True,
                "latitude": location.latitude,
                "longitude": location.longitude,
                "formatted_address": location.address,
                "source": "OpenStreetMap Nominatim",
                "confidence": "high"
            }

    except (GeocoderTimedOut, GeocoderServiceError) as e:
        pass  # Fall through to backup geocoder

    # Return failure if all geocoders fail
    return {
        "success": False,
        "error": f"Could not geocode: {address}",
        "suggestion": "Try adding zip code or state to address"
    }