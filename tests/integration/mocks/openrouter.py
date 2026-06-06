from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import final

from backend.app.shared.ports.llm.openrouter import (
    ChatCompletion,
    ChatCompletionDelta,
    ChatMessage,
    Embedding,
)


@dataclass
class OpenRouterCall:
    method: str
    messages: list[ChatMessage] | None = None
    inputs: list[str] | None = None
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None


@final
@dataclass
class MockOpenRouterGateway:
    completion_content: str = "mock completion"
    stream_deltas: tuple[str, ...] = ("mock ", "completion")
    embedding: tuple[float, ...] = (0.1, 0.2, 0.3)
    _calls: list[OpenRouterCall] = field(default_factory=list)

    async def complete(
        self,
        *,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ChatCompletion:
        self._calls.append(
            OpenRouterCall(
                method="complete",
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        )
        return ChatCompletion(
            content=self.completion_content,
            model=model or "mock-model",
            prompt_tokens=len(messages),
            completion_tokens=1,
        )

    async def stream(
        self,
        *,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[ChatCompletionDelta]:
        self._calls.append(
            OpenRouterCall(
                method="stream",
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        )
        for delta in self.stream_deltas:
            yield ChatCompletionDelta(content=delta)

    async def embed(
        self,
        *,
        inputs: list[str],
        model: str | None = None,
    ) -> list[Embedding]:
        self._calls.append(OpenRouterCall(method="embed", inputs=inputs, model=model))
        return [Embedding(vector=list(self.embedding), index=i) for i in range(len(inputs))]

    def get_calls(self) -> list[OpenRouterCall]:
        return list(self._calls)
