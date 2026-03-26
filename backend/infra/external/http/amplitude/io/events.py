from __future__ import annotations

from typing import Any, TypedDict

from backend.internal.dto import StructDTO


class Event(TypedDict, total=False):
    user_id: str
    device_id: str
    event_type: str
    time: int
    event_properties: dict[str, Any]
    user_properties: dict[str, Any]
    groups: dict[str, Any]
    app_version: str
    platform: str
    os_name: str
    os_version: str
    device_brand: str
    device_manufacturer: str
    device_model: str
    carrier: str
    country: str
    region: str
    city: str
    dma: str
    language: str
    price: float
    quantity: int
    revenue: float
    product_id: str
    revenue_type: str
    location_lat: float
    location_lng: float
    ip: str
    idfa: str
    idfv: str
    adid: str
    android_id: str
    event_id: int
    session_id: int
    insert_id: str


class Identification(TypedDict, total=False):
    user_id: str
    device_id: str
    user_properties: dict[str, Any]
    groups: dict[str, Any]
    app_version: str
    platform: str
    os_name: str
    os_version: str
    country: str
    region: str
    city: str
    language: str


class TrackResponse(StructDTO):
    code: int
    events_ingested: int = 0
    payload_size_bytes: int = 0
    server_upload_time: int = 0


class IdentifyResponse(StructDTO):
    code: int
