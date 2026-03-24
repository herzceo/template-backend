from __future__ import annotations

from backend.internal.dto import StructDTO


class ResendSettings(StructDTO):
    RESEND_API_KEY: str
    RESEND_BASE_URL: str = "https://api.resend.com"
