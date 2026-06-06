from typing import Required, TypedDict

from msgspec import field

from backend.infra.external.http.openrouter.io.chat import Usage
from backend.internal.dto import StructDTO


class EmbeddingRequest(TypedDict, total=False):
    model: Required[str]
    input: Required[list[str]]


class EmbeddingData(StructDTO):
    embedding: list[float]
    index: int


class EmbeddingResponse(StructDTO):
    model: str
    data: list[EmbeddingData]
    usage: Usage = field(default_factory=Usage)
