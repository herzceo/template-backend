from enum import StrEnum


class Endpoint(StrEnum):
    OAUTH_AUTHORIZE = "/oauth2/authorize"
    OAUTH_TOKEN = "/api/v10/oauth2/token"
    API_USERINFO = "/api/v10/users/@me"
