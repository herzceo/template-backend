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


class IpType(StrEnum):
    RESIDENTIAL = "residential"
    DATACENTER = "datacenter"
    VPN = "vpn"
    TOR = "tor"
    MOBILE = "mobile"


class DeviceType(StrEnum):
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"
    API = "api"


class AssetContentType(StrEnum):
    JPEG = "image/jpeg"
    PNG = "image/png"
    GIF = "image/gif"
    WEBP = "image/webp"
    SVG = "image/svg+xml"
    PDF = "application/pdf"
    MP4 = "video/mp4"
    WEBM = "video/webm"
