from fastapi import FastAPI
from app.core.config import settings
from app.api.v1 import endpoints  # <--- Import mới

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Đăng ký router
app.include_router(endpoints.router, prefix=settings.API_V1_STR) # <--- Dòng mới

@app.get("/")
def root():
    return {
        "message": "Welcome to PTIT BaaS Orchestrator",
        "docs": "/docs",
        "version": "1.0"
    }