from __future__ import annotations

from enum import StrEnum


class Endpoint(StrEnum):
    SEND_EMAIL = "/emails"
    SEND_BATCH = "/emails/batch"
    GET_EMAIL = "/emails/{email_id}"
    CANCEL_EMAIL = "/emails/{email_id}/cancel"
