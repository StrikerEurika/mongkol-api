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
from app.models.product import Product
from app.models.sale_item import SaleItem


def _month_start(dt: date) -> date:
    return date(dt.year, dt.month, 1)


async def reset_data(session: AsyncSession) -> None:
    # Order matters due to FKs
    await session.execute(delete(SaleItem))
    await session.execute(delete(Sale))
    await session.execute(delete(Target))
    await session.execute(delete(Product))
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


async def seed_products(session: AsyncSession) -> Sequence[Product]:
    existing = (await session.execute(select(Product))).scalars().all()
    if existing:
        return existing

    products = [
        Product(name_km="ទៀនធំ", name_en="Large Candle", price_usd=5.00, price_khr=20000, stock_quantity=100),
        Product(name_km="ទៀនតូច", name_en="Small Candle", price_usd=2.00, price_khr=8000, stock_quantity=200),
        Product(name_km="ធូប", name_en="Incense Sticks", price_usd=1.50, price_khr=6000, stock_quantity=500),
        Product(name_km="ឈុតសែន", name_en="Offering Set", price_usd=15.00, price_khr=60000, stock_quantity=50),
    ]
    session.add_all(products)
    await session.commit()
    for p in products:
        await session.refresh(p)
    return products


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


async def seed_sales(session: AsyncSession, users: Sequence[User], products: Sequence[Product], n_sales: int = 50) -> None:
    staff_users = [u for u in users if u.role == UserRole.STAFF]
    if not staff_users or not products:
        return

    statuses = [SaleStatus.DRAFT, SaleStatus.SUBMITTED, SaleStatus.APPROVED]
    payments = [PaymentMethod.CASH, PaymentMethod.CARD,
                PaymentMethod.TRANSFER, PaymentMethod.EWALLET]

    # Spread sales across the last ~30 days
    now = datetime.utcnow()
    for i in range(n_sales):
        creator = random.choice(staff_users)
        
        sale_items = []
        total_usd = 0.0
        total_khr = 0.0
        
        # Pick 1 to 3 random products
        for _ in range(random.randint(1, 3)):
            prod = random.choice(products)
            qty = random.randint(1, 5)
            sub_usd = float(prod.price_usd) * qty
            sub_khr = float(prod.price_khr) * qty
            total_usd += sub_usd
            total_khr += sub_khr
            
            sale_items.append(
                SaleItem(
                    product_id=prod.id,
                    quantity=qty,
                    unit_price_usd=prod.price_usd,
                    unit_price_khr=prod.price_khr,
                    subtotal_usd=sub_usd,
                    subtotal_khr=sub_khr
                )
            )

        discount_usd = round(random.uniform(0, total_usd * 0.15), 2) if random.random() < 0.5 else 0.0
        discount_khr = discount_usd * 4000
        
        dt = now - timedelta(days=random.randint(0, 30),
                             hours=random.randint(0, 23), minutes=random.randint(0, 59))
        sale = Sale(
            sale_datetime=dt,
            total_amount_usd=total_usd,
            total_amount_khr=total_khr,
            payment_method=random.choice(payments),
            discount_amount_usd=discount_usd if discount_usd > 0 else None,
            discount_amount_khr=discount_khr if discount_khr > 0 else None,
            note=("Test order" if random.random() < 0.2 else None),
            created_by_user_id=creator.id,
            status=random.choice(statuses),
            items=sale_items
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
        products = await seed_products(session)
        await seed_targets(session, users, months=months)
        await seed_sales(session, users, products, n_sales=sales_count)


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
