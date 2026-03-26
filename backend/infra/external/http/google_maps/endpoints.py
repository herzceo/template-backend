from __future__ import annotations

from enum import StrEnum


class Endpoint(StrEnum):
    AUTOCOMPLETE = "/place/autocomplete/json"
    PLACE_DETAILS = "/place/details/json"
    GEOCODE = "/geocode/json"
