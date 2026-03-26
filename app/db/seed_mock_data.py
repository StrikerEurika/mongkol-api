import asyncio
import sys
import random
from datetime import datetime, date, timedelta
from typing import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.db.init_db import init_models
from app.models.user import User, UserRole
from app.models.sale import Sale, SaleStatus, PaymentMethod
from app.models.target import Target


def _month_start(dt: date) -> date:
    return date(dt.year, dt.month, 1)


async def reset_data(session: AsyncSession) -> None:
    # Order matters due to FKs
    await session.execute(delete(Sale))
    await session.execute(delete(Target))
    await session.execute(delete(User))
    await session.commit()


async def seed_users(session: AsyncSession, n_staff: int = 5) -> Sequence[User]:
    existing = (await session.execute(select(User))).scalars().all()
    if existing:
        return existing

    users: list[User] = []

    admin = User(
        name="Admin User",
        email="admin@example.com",
        role=UserRole.ADMIN,
        is_active=True,
    )
    users.append(admin)

    for i in range(1, n_staff + 1):
        users.append(
            User(
                name=f"Staff {i}",
                email=f"staff{i}@example.com",
                role=UserRole.STAFF,
                is_active=True,
            )
        )

    session.add_all(users)
    await session.commit()
    # refresh to get IDs
    for u in users:
        await session.refresh(u)
    return users


async def seed_targets(session: AsyncSession, users: Sequence[User], months: int = 3) -> None:
    # Create monthly targets for each user for the past N months
    today = date.today()
    month_starts = []
    d = _month_start(today)
    for _ in range(months):
        month_starts.append(d)
        # go to previous month
        prev = (d.replace(day=1) - timedelta(days=1))
        d = _month_start(prev)

    for u in users:
        if u.role == UserRole.ADMIN:
            # Optional: skip admin targets
            continue
        for m in month_starts:
            # Check existing unique (user_id, period_month)
            exists = (
                await session.execute(
                    select(Target).where(Target.user_id ==
                                         u.id, Target.period_month == m)
                )
            ).scalars().first()
            if exists:
                continue
            target_amount = round(random.uniform(1000, 5000), 2)
            session.add(Target(user_id=u.id, period_month=m,
                        target_amount=target_amount))

    await session.commit()


async def seed_sales(session: AsyncSession, users: Sequence[User], n_sales: int = 50) -> None:
    staff_users = [u for u in users if u.role == UserRole.STAFF]
    if not staff_users:
        return

    statuses = [SaleStatus.DRAFT, SaleStatus.SUBMITTED, SaleStatus.APPROVED]
    payments = [PaymentMethod.CASH, PaymentMethod.CARD,
                PaymentMethod.TRANSFER, PaymentMethod.EWALLET]

    # Spread sales across the last ~30 days
    now = datetime.utcnow()
    for i in range(n_sales):
        creator = random.choice(staff_users)
        total = round(random.uniform(5, 500), 2)
        discount = round(random.uniform(0, total * 0.15),
                         2) if random.random() < 0.5 else None
        dt = now - timedelta(days=random.randint(0, 30),
                             hours=random.randint(0, 23), minutes=random.randint(0, 59))
        sale = Sale(
            sale_datetime=dt,
            total_amount=total,
            payment_method=random.choice(payments),
            discount_amount=discount,
            note=("Test order" if random.random() < 0.2 else None),
            created_by_user_id=creator.id,
            status=random.choice(statuses),
        )
        session.add(sale)

    await session.commit()


async def run_seed(reset: bool = False, staff_count: int = 5, sales_count: int = 50, months: int = 3) -> None:
    # Ensure tables exist
    await init_models()
    async with AsyncSessionLocal() as session:
        if reset:
            await reset_data(session)
        users = await seed_users(session, n_staff=staff_count)
        await seed_targets(session, users, months=months)
        await seed_sales(session, users, n_sales=sales_count)


def _parse_args():
    import argparse

    parser = argparse.ArgumentParser(
        description="Seed mock data for API testing")
    parser.add_argument("--reset", action="store_true",
                        help="Clear existing data before seeding")
    parser.add_argument("--staff", type=int, default=5,
                        help="Number of staff users to create")
    parser.add_argument("--sales", type=int, default=50,
                        help="Number of sales to create")
    parser.add_argument("--months", type=int, default=3,
                        help="Number of past months to create targets for")
    return parser.parse_args()


if __name__ == "__main__":
    # psycopg async needs selector loop on Windows
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    args = _parse_args()
    asyncio.run(run_seed(reset=args.reset, staff_count=args.staff,
                sales_count=args.sales, months=args.months))
