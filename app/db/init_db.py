from app.db.session import engine
from app.db.base import Base

# import models so Base knows them
from app.models.user import User
from app.models.sale import Sale
from app.models.target import Target
from app.models.audit_log import AuditLog

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)