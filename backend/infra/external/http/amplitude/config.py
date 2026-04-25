from __future__ import annotations

from backend.internal.dto import StructDTO


class AmplitudeConfig(StructDTO):
    AMPLITUDE_API_KEY: str
    AMPLITUDE_BASE_URL: str = "https://api2.amplitude.com"
