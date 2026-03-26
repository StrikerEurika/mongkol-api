from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog


async def write_audit_log(
    db: AsyncSession,
    actor_user_id: int,
    action: str,
    entity_type: str,
    entity_id: int,
    before: dict | None = None,
    after: dict | None = None,
) -> None:
    log = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_json=before,
        after_json=after,
    )

    db.add(log)
