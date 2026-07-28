from typing import final

from backend.app.shared.ports.auth.email_normalizer import EmailNormalizer


@final
class ImplEmailNormalize(EmailNormalizer):
    """Dependency-free, provider-aware email canonicalizer.

    Lowercases and trims every address, and for Gmail/Googlemail additionally
    strips ``+tag`` suffixes and dots from the local part and normalizes the
    domain to ``gmail.com`` — the aliasing rules that map many spellings to one
    real mailbox. This mirrors the ``_canonical`` SQL in the ``user_email``
    migration exactly, so backfilled rows and runtime lookups always agree.

    Swap point: a project wanting deeper provider coverage (Outlook, Yahoo,
    Google Apps, MX-resolved providers) can replace this adapter with one backed
    by a library such as ``email-normalize`` — keep the migration's backfill SQL
    in sync with whatever canonical form it produces.
    """

    _GMAIL_DOMAINS = frozenset({"gmail.com", "googlemail.com"})

    async def canonical(self, email: str) -> str:
        lowered = email.strip().lower()
        local, sep, domain = lowered.partition("@")
        if not sep:
            return lowered
        if domain in self._GMAIL_DOMAINS:
            local = local.split("+", 1)[0].replace(".", "")
            return f"{local}@gmail.com"
        return lowered
