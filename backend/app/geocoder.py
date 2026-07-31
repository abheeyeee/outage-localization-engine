import math
from typing import Optional, Dict

# Bounded offline Bangalore PIN Code centroid database (Zero external API key dependency)
BANGALORE_PINCODE_CENTROIDS = [
    {"pincode": "560001", "name": "MG Road / Cubbon Park", "lat": 12.9750, "lon": 77.6010},
    {"pincode": "560002", "name": "City Market / Chickpet", "lat": 12.9650, "lon": 77.5750},
    {"pincode": "560004", "name": "Basavanagudi", "lat": 12.9410, "lon": 77.5740},
    {"pincode": "560025", "name": "Richmond Town", "lat": 12.9580, "lon": 77.6040},
    {"pincode": "560027", "name": "Wilson Garden", "lat": 12.9480, "lon": 77.5960},
    {"pincode": "560034", "name": "Koramangala", "lat": 12.9350, "lon": 77.6240},
    {"pincode": "560070", "name": "Banashankari", "lat": 12.9250, "lon": 77.5710},
    {"pincode": "560095", "name": "HSR Layout", "lat": 12.9120, "lon": 77.6440},
]

def resolve_pincode(lat: Optional[float], lon: Optional[float], existing_pincode: Optional[str] = None) -> Dict[str, str]:
    """
    Offline Spatial Geocoding Engine:
    Resolves PIN code for any GPS coordinate in Bangalore using zero-dependency 
    Nearest-Neighbor spatial bounding lookup. Gracefully imputes missing 3% pole PIN codes offline.
    """
    # 1. Return existing valid PIN code if available in GIS registry
    if existing_pincode and str(existing_pincode).strip() and str(existing_pincode).isdigit() and len(str(existing_pincode)) == 6:
        return {
            "pincode": str(existing_pincode),
            "area": "Registered Utility Substation Zone",
            "is_imputed": False
        }

    # 2. If lat/lon invalid, degrade gracefully to Bangalore Central
    if lat is None or lon is None:
        return {
            "pincode": "560001",
            "area": "Bangalore Central (Imputed)",
            "is_imputed": True
        }

    # 3. Offline Nearest Neighbor Centroid Distance Computation
    closest = None
    min_dist = float('inf')

    for entry in BANGALORE_PINCODE_CENTROIDS:
        # Euclidean distance approximation for spatial proximity
        dist = math.sqrt((lat - entry["lat"])**2 + (lon - entry["lon"])**2)
        if dist < min_dist:
            min_dist = dist
            closest = entry

    if closest:
        return {
            "pincode": closest["pincode"],
            "area": closest["name"],
            "is_imputed": True if not existing_pincode else False
        }

    return {
        "pincode": "560001",
        "area": "Bangalore Urban",
        "is_imputed": True
    }
