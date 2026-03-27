from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload
from datetime import datetime, date, timedelta
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.sale import Sale, SaleStatus
from app.models.sale_item import SaleItem
from app.schemas.sale import SaleCreate, SaleUpdate, SaleOut
from app.services.sales_service import create_sale, staff_update_sale, submit_sale
from app.utils.csv_export import rows_to_csv

router = APIRouter(prefix="/sales", tags=["sales"])

@router.post("", response_model=SaleOut)
async def create_my_sale(
    payload: SaleCreate,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
):
    data = payload.model_dump()
    if data.get("sale_datetime") is None:
        data.pop("sale_datetime")

    sale = await create_sale(db, actor_id=user.id, created_by_user_id=user.id, payload=data)
    await db.commit()
    
    # Eagerly load items before returning
    res = await db.execute(select(Sale).options(selectinload(Sale.items)).where(Sale.id == sale.id))
    sale_with_items = res.scalar_one()
    
    return sale_with_items

@router.get("", response_model=list[SaleOut])
async def list_my_sales(
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
    status: SaleStatus | None = Query(default=None),
    limit: int = Query(default=50, le=200),
):
    stmt = select(Sale).options(selectinload(Sale.items)).where(Sale.created_by_user_id == user.id)
    if status:
        stmt = stmt.where(Sale.status == status)
    stmt = stmt.order_by(desc(Sale.sale_datetime)).limit(limit)

    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/dashboard")
async def my_dashboard(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    # today boundaries
    today = date.today()
    start_today = datetime.combine(today, datetime.min.time())
    end_today = start_today + timedelta(days=1)

    # Calculate today's total sales
    total_today_usd = await db.scalar(
        select(func.coalesce(func.sum(Sale.total_amount_usd), 0))
        .where(Sale.created_by_user_id == user.id)
        .where(Sale.sale_datetime >= start_today, Sale.sale_datetime < end_today)
        .where(Sale.status.in_([SaleStatus.SUBMITTED, SaleStatus.APPROVED, SaleStatus.LOCKED]))
    )

    total_today_khr = await db.scalar(
        select(func.coalesce(func.sum(Sale.total_amount_khr), 0))
        .where(Sale.created_by_user_id == user.id)
        .where(Sale.sale_datetime >= start_today, Sale.sale_datetime < end_today)
        .where(Sale.status.in_([SaleStatus.SUBMITTED, SaleStatus.APPROVED, SaleStatus.LOCKED]))
    )

    return {
        "total_today_usd": float(total_today_usd or 0),
        "total_today_khr": float(total_today_khr or 0)
    }

@router.get("/export.csv")
async def export_my_sales_csv(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
):
    stmt = select(Sale).where(Sale.created_by_user_id == user.id)
    if start:
        stmt = stmt.where(Sale.sale_datetime >= start)
    if end:
        stmt = stmt.where(Sale.sale_datetime <= end)

    res = await db.execute(stmt.order_by(desc(Sale.sale_datetime)).limit(5000))
    sales = res.scalars().all()

    rows = []
    for s in sales:
        rows.append({
            "id": s.id,
            "sale_datetime": s.sale_datetime.isoformat() if s.sale_datetime else "",
            "total_amount_usd": float(s.total_amount_usd),
            "total_amount_khr": float(s.total_amount_khr),
            "payment_method": s.payment_method.value,
            "status": s.status.value,
        })

    csv_text = rows_to_csv(rows)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=my_sales.csv"},
    )

@router.patch("/{sale_id}", response_model=SaleOut)
async def update_my_sale(
    sale_id: int,
    payload: SaleUpdate,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
):
    await staff_update_sale(db, actor_id=user.id, sale_id=sale_id, payload=payload.model_dump())
    await db.commit()
    
    # Reload to get updated items
    res = await db.execute(select(Sale).options(selectinload(Sale.items)).where(Sale.id == sale_id))
    sale_updated = res.scalar_one()
    return sale_updated

@router.post("/{sale_id}/submit", response_model=SaleOut)
async def submit_my_sale(
    sale_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
):
    await submit_sale(db, actor_id=user.id, sale_id=sale_id)
    await db.commit()
    
    res = await db.execute(select(Sale).options(selectinload(Sale.items)).where(Sale.id == sale_id))
    sale = res.scalar_one()
    return sale
