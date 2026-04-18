from enum import StrEnum


class Endpoint(StrEnum):
    ACCOUNTS_AUTHORIZE = "/o/oauth2/v2/auth"
    OAUTH_TOKEN = "/token"
    API_USERINFO = "/oauth2/v3/userinfo"
