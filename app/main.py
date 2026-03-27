import asyncio
import sys

from fastapi import FastAPI
from app.core.config import settings
from app.routers import auth, sales, admin, products

# Set the event loop policy to use SelectorEventLoop on Windows to avoid issues with psycopg
if sys.platform.startswith("win"):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except AttributeError:
        # Ignore if not available (for newer Python versions)
        pass

app = FastAPI(title=settings.APP_NAME)

app.include_router(auth.router)
app.include_router(sales.router)
app.include_router(admin.router)
app.include_router(products.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
