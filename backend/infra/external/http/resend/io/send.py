from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from backend.internal.dto import StructDTO

if TYPE_CHECKING:
    from backend.infra.external.http.resend.io.common import Attachment, Tag


class SendEmailRequest(TypedDict, total=False):
    from_: str
    to: list[str]
    subject: str
    html: str
    text: str
    cc: list[str]
    bcc: list[str]
    reply_to: list[str]
    tags: list[Tag]
    attachments: list[Attachment]
    headers: dict[str, str]
    scheduled_at: str


class SendEmailResponse(StructDTO):
    id: str


class BatchEmailResponse(StructDTO):
    data: list[SendEmailResponse]
