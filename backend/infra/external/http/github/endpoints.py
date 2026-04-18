from enum import StrEnum


class Endpoint(StrEnum):
    OAUTH_AUTHORIZE = "/login/oauth/authorize"
    OAUTH_TOKEN = "/login/oauth/access_token"
    API_USER = "/user"
    API_EMAILS = "/user/emails"
