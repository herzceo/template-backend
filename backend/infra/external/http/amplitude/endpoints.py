from __future__ import annotations

from enum import StrEnum


class Endpoint(StrEnum):
    TRACK = "/2/httpapi"
    IDENTIFY = "/identify"
