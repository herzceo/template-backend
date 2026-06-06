from abc import abstractmethod
from collections.abc import AsyncIterator
from typing import Protocol

from backend.internal.dto import StructDTO


class ChatMessage(StructDTO):
    role: str
    content: str


class ChatCompletion(StructDTO):
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int


class ChatCompletionDelta(StructDTO):
    content: str


class Embedding(StructDTO):
    vector: list[float]
    index: int


class OpenRouterGateway(Protocol):
    @abstractmethod
    async def complete(
        self,
        *,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ChatCompletion: ...

    @abstractmethod
    def stream(
        self,
        *,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[ChatCompletionDelta]: ...

    @abstractmethod
    async def embed(
        self,
        *,
        inputs: list[str],
        model: str | None = None,
    ) -> list[Embedding]: ...
