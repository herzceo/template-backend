from backend.internal.dto import StructDTO


class VerificationConfig(StructDTO):
    VERIFICATION_TTL_SECONDS: int = 15 * 60
    VERIFICATION_MAX_ATTEMPTS: int = 3
