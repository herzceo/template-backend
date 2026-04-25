from __future__ import annotations

from backend.internal.dto import StructDTO


class GoogleMapsConfig(StructDTO):
    GOOGLE_MAPS_API_KEY: str
    GOOGLE_MAPS_BASE_URL: str = "https://maps.googleapis.com/maps/api"
