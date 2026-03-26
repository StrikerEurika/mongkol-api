from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, date, timedelta
from app.db.session import get_db
from app.core.deps import require_admin, get_current_user
from app.models.sale import Sale, SaleStatus, PaymentMethod
from app.models.user import User, UserRole
from app.schemas.sale import SaleOut
from app.services.sales_service import admin_set_status
from app.utils.csv_export import rows_to_csv

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/sales", response_model=list[SaleOut])
async def admin_list_sales(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    staff_id: int | None = Query(default=None),
    status: SaleStatus | None = Query(default=None),
    payment_method: PaymentMethod | None = Query(default=None),
    limit: int = Query(default=200, le=1000),
):
    stmt = select(Sale)

    if start:
        stmt = stmt.where(Sale.sale_datetime >= start)
    if end:
        stmt = stmt.where(Sale.sale_datetime <= end)
    if staff_id:
        stmt = stmt.where(Sale.created_by_user_id == staff_id)
    if status:
        stmt = stmt.where(Sale.status == status)
    if payment_method:
        stmt = stmt.where(Sale.payment_method == payment_method)

    stmt = stmt.order_by(desc(Sale.sale_datetime)).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/sales/{sale_id}/approve", response_model=SaleOut)
async def approve_sale(
    sale_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    sale = await admin_set_status(db, admin_id=admin.id, sale_id=sale_id, new_status=SaleStatus.APPROVED)
    await db.commit()
    await db.refresh(sale)
    return sale


@router.post("/sales/{sale_id}/lock", response_model=SaleOut)
async def lock_sale(
    sale_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    sale = await admin_set_status(db, admin_id=admin.id, sale_id=sale_id, new_status=SaleStatus.LOCKED)
    await db.commit()
    await db.refresh(sale)
    return sale


@router.get("/dashboard")
async def admin_dashboard(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    # today boundaries (server timezone; later you can use Asia/Phnom_Penh explicitly)
    today = date.today()
    start_today = datetime.combine(today, datetime.min.time())
    end_today = start_today + timedelta(days=1)

    # month boundaries
    start_month = date(today.year, today.month, 1)
    start_month_dt = datetime.combine(start_month, datetime.min.time())
    next_month = (start_month.replace(day=28) +
                  timedelta(days=4)).replace(day=1)
    next_month_dt = datetime.combine(next_month, datetime.min.time())

    # totals
    total_today = await db.scalar(
        select(func.coalesce(func.sum(Sale.total_amount), 0))
        .where(Sale.sale_datetime >= start_today, Sale.sale_datetime < end_today)
        .where(Sale.status.in_([SaleStatus.SUBMITTED, SaleStatus.APPROVED, SaleStatus.LOCKED]))
    )

    total_month = await db.scalar(
        select(func.coalesce(func.sum(Sale.total_amount), 0))
        .where(Sale.sale_datetime >= start_month_dt, Sale.sale_datetime < next_month_dt)
        .where(Sale.status.in_([SaleStatus.SUBMITTED, SaleStatus.APPROVED, SaleStatus.LOCKED]))
    )

    # leaderboard by staff (month)
    leaderboard = (await db.execute(
        select(Sale.created_by_user_id, func.coalesce(
            func.sum(Sale.total_amount), 0).label("total"))
        .where(Sale.sale_datetime >= start_month_dt, Sale.sale_datetime < next_month_dt)
        .where(Sale.status.in_([SaleStatus.SUBMITTED, SaleStatus.APPROVED, SaleStatus.LOCKED]))
        .group_by(Sale.created_by_user_id)
        .order_by(desc("total"))
        .limit(10)
    )).all()

    # missing entries alert: staff with zero submitted/approved/locked sales today
    staff_ids_with_sales_today = (await db.execute(
        select(Sale.created_by_user_id)
        .where(Sale.sale_datetime >= start_today, Sale.sale_datetime < end_today)
        .where(Sale.status.in_([SaleStatus.SUBMITTED, SaleStatus.APPROVED, SaleStatus.LOCKED]))
        .group_by(Sale.created_by_user_id)
    )).scalars().all()

    missing_staff = (await db.execute(
        select(User.id, User.name)
        .where(User.role == UserRole.STAFF, User.is_active == True)
        .where(User.id.not_in(staff_ids_with_sales_today) if staff_ids_with_sales_today else True)
    )).all()

    return {
        "total_today": float(total_today or 0),
        "total_month": float(total_month or 0),
        "leaderboard": [{"user_id": uid, "total": float(total)} for (uid, total) in leaderboard],
        "missing_entries_today": [{"user_id": uid, "name": name} for (uid, name) in missing_staff],
    }


@router.get("/sales/export.csv")
async def export_sales_csv(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
):
    stmt = select(Sale)
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
            "sale_datetime": s.sale_datetime.isoformat(),
            "total_amount": float(s.total_amount),
            "payment_method": s.payment_method.value,
            "discount_amount": float(s.discount_amount) if s.discount_amount is not None else "",
            "status": s.status.value,
            "created_by_user_id": s.created_by_user_id,
        })

    csv_text = rows_to_csv(rows)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sales_export.csv"},
    )
