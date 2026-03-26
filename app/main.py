from fastapi import FastAPI
from app.core.config import settings
from app.routers import auth, sales, admin

app = FastAPI(title=settings.APP_NAME)

app.include_router(auth.router)
app.include_router(sales.router)
app.include_router(admin.router)

@app.get("/health")
async def health():
    return {"status": "ok"}
