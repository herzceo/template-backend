from backend.internal.dto import StructDTO


class OpenRouterConfig(StructDTO):
    OPENROUTER_API_KEY: str
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"
    OPENROUTER_HTTP_REFERER: str = ""
    OPENROUTER_TITLE: str = ""
