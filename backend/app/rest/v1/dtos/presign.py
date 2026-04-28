from backend.internal.dto import StructDTO


class PresignedUploadResponse(StructDTO):
    url: str
    key: str
    expires_in: int
