from enum import StrEnum


class OpenRouterEndpoints(StrEnum):
    CHAT_COMPLETIONS = "/chat/completions"
    EMBEDDINGS = "/embeddings"
