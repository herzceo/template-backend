from typing import Any
from uuid import UUID

from backend.app.rest.v1.services.types import ClientDeviceInfo
from backend.domain.enums import AssetContentType
from backend.internal.dto import StructDTO


class SignInBody(StructDTO):
    username: str
    password: str
    client_device: ClientDeviceInfo | None = None


class VerifyEmailBody(StructDTO):
    email: str
    code: str
    client_device: ClientDeviceInfo | None = None


class LoginCodeRequestBody(StructDTO):
    identifier: str


class LoginCodeVerifyBody(StructDTO):
    identifier: str
    code: str
    client_device: ClientDeviceInfo | None = None


class PasswordResetRequestBody(StructDTO):
    identifier: str


class PasswordResetConfirmBody(StructDTO):
    token: str
    password: str
    client_device: ClientDeviceInfo | None = None


class SetPasswordBody(StructDTO):
    password: str
    client_device: ClientDeviceInfo | None = None


class ChangePasswordBody(StructDTO):
    reauth_token: str
    new_password: str


class ChooseUsernameBody(StructDTO):
    username: str


class ChangeEmailRequestBody(StructDTO):
    reauth_token: str
    new_email: str


class ChangeEmailConfirmBody(StructDTO):
    token: str


class CompleteOAuthSignupBody(StructDTO):
    email: str
    username: str
    device_fingerprint: str | None = None


class ConfirmOAuthSignupBody(StructDTO):
    code: str
    client_device: ClientDeviceInfo | None = None
    device_fingerprint: str | None = None


class OAuthCallbackBody(StructDTO):
    code: str
    state: str
    device_fingerprint: str | None = None


class OAuthExchangeBody(StructDTO):
    code: str
    state: str


class ReauthPasswordBody(StructDTO):
    password: str


class UpdateUserBody(StructDTO):
    email: str | None = None


class UpdateProfileBody(StructDTO, kw_only=True):
    display_name: str | None = None
    avatar_url: str | None = None


class UpdateTenantBody(StructDTO):
    name: str | None = None
    slug: str | None = None
    settings: dict[str, Any] | None = None
    owner_id: UUID | None = None


class UpdateRoleBody(StructDTO):
    name: str | None = None
    description: str | None = None


class UpdatePermissionBody(StructDTO):
    codename: str | None = None
    description: str | None = None


class UpdateAssetBody(StructDTO):
    blurhash: str | None = None
    original_filename: str | None = None


class PresignAssetBody(StructDTO):
    original_filename: str


class ConfirmAssetUploadBody(StructDTO):
    temp_key: str
    content_type: AssetContentType
    original_filename: str


class UpdateNotificationBody(StructDTO):
    title: str | None = None
    body: str | None = None
    urgency: int | None = None


class ReactionBody(StructDTO):
    user_id: UUID
    reaction: str | None


class AssignRoleBody(StructDTO):
    role_id: UUID


class RevokeRoleBody(StructDTO):
    role_id: UUID


class AssignPermissionBody(StructDTO):
    role_id: UUID
    permission_id: UUID


class RevokePermissionBody(StructDTO):
    role_id: UUID
    permission_id: UUID


class MarkReadBody(StructDTO):
    user_id: UUID


class DismissBody(StructDTO):
    user_id: UUID
