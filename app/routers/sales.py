from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.sale import Sale, SaleStatus
from app.schemas.sale import SaleCreate, SaleUpdate, SaleOut
from app.services.sales_service import create_sale, staff_update_sale, submit_sale

router = APIRouter(prefix="/sales", tags=["sales"])

@router.post("", response_model=SaleOut)
async def create_my_sale(
    payload: SaleCreate,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
):
    data = payload.model_dump()
    # if client doesn't provide datetime, keep server default
    if data.get("sale_datetime") is None:
        data.pop("sale_datetime")

    sale = await create_sale(db, actor_id=user.id, created_by_user_id=user.id, payload=data)
    await db.commit()
    await db.refresh(sale)
    return sale

@router.get("", response_model=list[SaleOut])
async def list_my_sales(
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
    status: SaleStatus | None = Query(default=None),
    limit: int = Query(default=50, le=200),
):
    stmt = select(Sale).where(Sale.created_by_user_id == user.id)
    if status:
        stmt = stmt.where(Sale.status == status)
    stmt = stmt.order_by(desc(Sale.sale_datetime)).limit(limit)

    res = await db.execute(stmt)
    return res.scalars().all()

@router.patch("/{sale_id}", response_model=SaleOut)
async def update_my_sale(
    sale_id: int,
    payload: SaleUpdate,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
):
    sale = await staff_update_sale(db, actor_id=user.id, sale_id=sale_id, payload=payload.model_dump())
    await db.commit()
    await db.refresh(sale)
    return sale

@router.post("/{sale_id}/submit", response_model=SaleOut)
async def submit_my_sale(
    sale_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
):
    sale = await submit_sale(db, actor_id=user.id, sale_id=sale_id)
    await db.commit()
    await db.refresh(sale)
    return sale
