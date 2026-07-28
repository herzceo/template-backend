from abc import abstractmethod
from typing import Protocol


class EmailNormalizer(Protocol):
    """Canonicalizes an email to a provider-aware, aggressively-normalized form.

    The returned value is the global-uniqueness key stored in
    ``UserEmail.normalized_email`` — it collapses provider-specific aliasing
    (Gmail dots and ``+tags``, Google Apps, etc.) so that alias variants of one
    real mailbox resolve to a single identity. Input is assumed already
    format-validated (see ``normalize_email``); this only canonicalizes.
    """

    @abstractmethod
    async def canonical(self, email: str) -> str: ...
