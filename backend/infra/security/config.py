from backend.internal.dto import StructDTO


class OAuthStateConfig(StructDTO):
    OAUTH_STATE_SECRET: str
