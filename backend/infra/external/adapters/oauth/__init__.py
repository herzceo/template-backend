from backend.infra.external.adapters.oauth.discord import ImplDiscordOAuthAdapter
from backend.infra.external.adapters.oauth.gateway import ImplOAuthGateway
from backend.infra.external.adapters.oauth.github import ImplGitHubOAuthAdapter
from backend.infra.external.adapters.oauth.google import ImplGoogleOAuthAdapter

__all__ = (
    "ImplDiscordOAuthAdapter",
    "ImplGitHubOAuthAdapter",
    "ImplGoogleOAuthAdapter",
    "ImplOAuthGateway",
)
