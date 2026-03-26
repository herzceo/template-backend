from __future__ import annotations

from typing import TypedDict

from backend.internal.dto import StructDTO


class AutocompleteRequest(TypedDict, total=False):
    input: str
    language: str
    types: str
    components: str
    location: str
    radius: int
    sessiontoken: str


class PlaceDetailsRequest(TypedDict, total=False):
    place_id: str
    fields: str
    language: str
    sessiontoken: str


class GeocodeRequest(TypedDict, total=False):
    address: str
    latlng: str
    place_id: str
    language: str
    components: str


class StructuredFormatting(StructDTO):
    main_text: str = ""
    secondary_text: str = ""


class MatchedSubstring(StructDTO):
    offset: int = 0
    length: int = 0


class Term(StructDTO):
    offset: int = 0
    value: str = ""


class AutocompletePrediction(StructDTO):
    place_id: str = ""
    description: str = ""
    structured_formatting: StructuredFormatting = StructuredFormatting()
    terms: list[Term] = []  # noqa: RUF012
    types: list[str] = []  # noqa: RUF012
    matched_substrings: list[MatchedSubstring] = []  # noqa: RUF012


class AutocompleteResponse(StructDTO):
    status: str = ""
    predictions: list[AutocompletePrediction] = []  # noqa: RUF012


class Location(StructDTO):
    lat: float = 0.0
    lng: float = 0.0


class Geometry(StructDTO):
    location: Location = Location()


class AddressComponent(StructDTO):
    long_name: str = ""
    short_name: str = ""
    types: list[str] = []  # noqa: RUF012


class PlaceDetails(StructDTO):
    place_id: str = ""
    name: str = ""
    formatted_address: str = ""
    geometry: Geometry = Geometry()
    address_components: list[AddressComponent] = []  # noqa: RUF012
    types: list[str] = []  # noqa: RUF012
    url: str = ""
    utc_offset: int | None = None


class PlaceDetailsResponse(StructDTO):
    status: str = ""
    result: PlaceDetails | None = None


class GeocodeResult(StructDTO):
    place_id: str = ""
    formatted_address: str = ""
    geometry: Geometry = Geometry()
    address_components: list[AddressComponent] = []  # noqa: RUF012
    types: list[str] = []  # noqa: RUF012


class GeocodeResponse(StructDTO):
    status: str = ""
    results: list[GeocodeResult] = []  # noqa: RUF012
