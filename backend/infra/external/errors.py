from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(eq=False)
class ExternalError(Exception):
    message: str = ""
    code: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message


class NetworkError(ExternalError):
    message = "Network error"
    code = "network_error"


@dataclass(eq=False)
class DecodeError(ExternalError):
    message: str = "Decode error"
    code: str = "decode_error"
    raw: bytes = b""


class ClientError(ExternalError):
    message = "Client error"
    code = "client_error"
