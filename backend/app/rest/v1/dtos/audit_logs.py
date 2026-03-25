from typing import Any

from backend.internal.dto import StructDTO


class AuditLog(StructDTO):
    id: str
    actor_id: str | None
    action: str
    resource_type: str
    resource_id: str
    changes: dict[str, Any] | None
    ip: str | None
    tenant_id: str
    created_at: str
