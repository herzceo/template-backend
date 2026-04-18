from enum import StrEnum


class NotificationAudience(StrEnum):
    ALL = "all"
    ROLE = "role"
    USER = "user"


class NotificationUrgency(int):
    LOW = 10
    NORMAL = 20
    HIGH = 30
    CRITICAL = 40


class AuditAction(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    PERMISSION_CHANGE = "permission_change"


class IdentityProvider(StrEnum):
    EMAIL_PASSWORD = "email_password"
    USERNAME_PASSWORD = "username_password"
    GOOGLE = "google"
    GITHUB = "github"
    DISCORD = "discord"
