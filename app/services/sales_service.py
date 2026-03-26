from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Set

from app.models.sale import Sale, SaleStatus
# from app.models.user import UserRole
from app.services.audit_service import write_audit_log


def sale_to_dict(s: Sale) -> dict:
    return {
        "id": s.id,
        "sale_datetime": s.sale_datetime.isoformat() if s.sale_datetime else None,
        "total_amount": float(s.total_amount),
        "payment_method": s.payment_method.value,
        "discount_amount": float(s.discount_amount) if s.discount_amount else None,
        "note": s.note,
        "created_by_user_id": s.created_by_user_id,
        "status": s.status.value,
    }


async def get_sale_or_404(
    db: AsyncSession,
    sale_id: int,
    for_update: bool = False,
) -> Sale:
    # res = await db.execute(select(Sale).where(Sale.id == sale_id))
    q = select(Sale).where(Sale.id == sale_id)
    if for_update:
        q = q.with_for_update()
    res = await db.execute(q)
    sale = res.scalar_one_or_none()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale


def can_staff_edit(status: SaleStatus) -> bool:
    return status == SaleStatus.DRAFT


# Only allow whitelisted fields to be updated by staff
ALLOWED_UPDATE_FIELDS: Set[str] = {
    "sale_datetime",
    "total_amount",
    "payment_method",
    "discount_amount",
    "note",
}


def update_sale_fields(sale: Sale, data: dict):
    for k, v in data.items():
        if v is None:
            continue
        if k in ALLOWED_UPDATE_FIELDS:
            continue
        setattr(sale, k, v)


async def create_sale(db: AsyncSession, actor_id: int, created_by_user_id: int, payload: dict) -> Sale:
    sale = Sale(created_by_user_id=created_by_user_id, **payload)
    db.add(sale)
    await db.flush()

    await write_audit_log(
        db=db,
        actor_user_id=actor_id,
        action="create_sale",
        entity_type="sale",
        entity_id=sale.id,
        before=None,
        after=sale_to_dict(sale),
    )

    return sale


async def staff_update_sale(db: AsyncSession, actor_id: int, sale_id: int, payload: dict) -> Sale:
    sale = await get_sale_or_404(db, sale_id)

    if sale.created_by_user_id != actor_id:
        raise HTTPException(
            status_code=403, detail="Staff can only edit their own sales")
    if not can_staff_edit(sale.status):
        raise HTTPException(
            status_code=400, detail=f"Cannot edit sale wit status {sale.status.value}")

    before = sale_to_dict(sale)
    update_sale_fields(sale, payload)
    after = sale_to_dict(sale)

    # await write_audit_log(db, actor_id, "update", "sale", sale.id, before, after)
    await write_audit_log(
        db=db,
        actor_user_id=actor_id,
        action="update",
        entity_type="sale",
        entity_id=sale.id,
        before=before,
        after=after,
    )
    return sale


async def submit_sale(db: AsyncSession, actor_id: int, sale_id: int) -> Sale:
    sale = await get_sale_or_404(db, sale_id)
    if sale.created_by_user_id != actor_id:
        raise HTTPException(
            status_code=403, detail="Staff can only submit their own sales")

    if sale.status != SaleStatus.DRAFT:
        raise HTTPException(
            status_code=400, detail="Only draft sales can be submitted")

    before = sale_to_dict(sale)
    sale.status = SaleStatus.SUBMITTED
    after = sale_to_dict(sale)

    # await write_audit_log(db, actor_id, "submit", "sale", sale.id, before, after)
    await write_audit_log(
        db=db,
        actor_user_id=actor_id,
        action="submit",
        entity_type="sale",
        entity_id=sale.id,
        before=before,
        after=after,
    )
    return sale


async def admin_set_status(db: AsyncSession, admin_id: int, sale_id: int, new_status: SaleStatus) -> Sale:
    sale = await get_sale_or_404(db, sale_id)

    # enforce a sane status transition
    allowed = {
        SaleStatus.SUBMITTED: {SaleStatus.APPROVED},
        SaleStatus.APPROVED: {SaleStatus.LOCKED},
    }

    if sale.status not in allowed or new_status not in allowed[sale.status]:
        raise HTTPException(
            status_code=400, detail=f"Invalid Transition {sale.status.value} -> {new_status.value}")

    before = sale_to_dict(sale)
    sale.status = new_status
    after = sale_to_dict(sale)

    action = "approve" if new_status == SaleStatus.APPROVED else "lock"
    # await write_audit_log(db, admin_id, action, "sale", sale.id, before, after)
    await write_audit_log(
        db=db,
        actor_user_id=admin_id,
        action=action,
        entity_type="sale",
        entity_id=sale.id,
        before=before,
        after=after,
    )
    return sale
