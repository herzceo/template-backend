from __future__ import annotations

from backend.internal.dto import StructDTO


class Email(StructDTO):
    id: str
    from_: str
    to: list[str]
    subject: str
    html: str | None = None
    text: str | None = None
    bcc: list[str] | None = None
    cc: list[str] | None = None
    reply_to: list[str] | None = None
    created_at: str = ""
    last_event: str = ""
