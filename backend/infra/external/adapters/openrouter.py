from __future__ import annotations

from typing import TYPE_CHECKING, final

from backend.app.shared.ports.llm.openrouter import (
    ChatCompletion,
    ChatCompletionDelta,
    Embedding,
    OpenRouterGateway,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from backend.app.shared.ports.llm.openrouter import ChatMessage
    from backend.infra.external.http.openrouter import io
    from backend.infra.external.http.openrouter.client import OpenRouterClient


@final
class ImplOpenRouterGateway(OpenRouterGateway):
    __slots__ = ("_client", "_default_model")

    def __init__(self, client: OpenRouterClient, default_model: str) -> None:
        self._client = client
        self._default_model = default_model

    def _chat_body(
        self,
        messages: list[ChatMessage],
        model: str | None,
        temperature: float | None,
        max_tokens: int | None,
    ) -> io.ChatCompletionRequest:
        body: io.ChatCompletionRequest = {
            "model": model or self._default_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        if temperature is not None:
            body["temperature"] = temperature
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        return body

    async def complete(
        self,
        *,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ChatCompletion:
        body = self._chat_body(messages, model, temperature, max_tokens)
        response = (await self._client.complete(**body)).raise_()
        choice = response.choices[0]
        return ChatCompletion(
            content=choice.message.content,
            model=response.model,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
        )

    async def stream(
        self,
        *,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[ChatCompletionDelta]:
        body = self._chat_body(messages, model, temperature, max_tokens)
        async for chunk in self._client.stream_complete(**body):
            if not chunk.choices:
                continue
            content = chunk.choices[0].delta.content
            if content:
                yield ChatCompletionDelta(content=content)

    async def embed(
        self,
        *,
        inputs: list[str],
        model: str | None = None,
    ) -> list[Embedding]:
        response = (
            await self._client.embed(model=model or self._default_model, input=inputs)
        ).raise_()
        return [Embedding(vector=item.embedding, index=item.index) for item in response.data]
