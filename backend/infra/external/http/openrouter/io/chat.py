from typing import Any, NotRequired, Required, TypedDict

from msgspec import field

from backend.internal.dto import StructDTO


class ChatCompletionRequest(TypedDict, total=False):
    model: Required[str]
    messages: Required[list[dict[str, Any]]]
    temperature: NotRequired[float]
    max_tokens: NotRequired[int]
    stream: NotRequired[bool]


class Usage(StructDTO):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class Message(StructDTO):
    role: str
    content: str


class Choice(StructDTO):
    message: Message
    finish_reason: str | None = None


class ChatCompletionResponse(StructDTO):
    model: str
    choices: list[Choice]
    usage: Usage = field(default_factory=Usage)


class Delta(StructDTO):
    content: str | None = None


class ChunkChoice(StructDTO):
    delta: Delta


class ChatCompletionChunk(StructDTO):
    choices: list[ChunkChoice]
