from __future__ import annotations

from backend.internal.dto import StructDTO


class Tag(StructDTO):
    name: str
    value: str


class Attachment(StructDTO):
    filename: str
    content: str
    path: str | None = None
    content_type: str | None = None
