from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import os
from app.core.config import settings
from app.api.v1 import endpoints

tags_metadata = [
    {
        "name": "BaaS Core",
        "description": "API điều khiển Mạng lưới Máy tính phân tán Blockchain.",
    }
]

app = FastAPI(
    title="PTIT BaaS Orchestrator",
    description="Hệ thống Backend tự động hóa thiết lập kiến trúc Blockchain. Phát triển bởi Trịnh Đặng Huy Hoàng",
    version="1.5.0",
    openapi_tags=tags_metadata,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    contact={
        "name": "DevSecOps Team",
    }
)

from fastapi.middleware.cors import CORSMiddleware

# Đăng ký CORS để Frontend ở port 3000 có thể gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký router
app.include_router(endpoints.router, prefix=settings.API_V1_STR) # <--- Dòng mới

@app.get("/", response_class=HTMLResponse, tags=["Dashboard"])
def root():
    """Giao diện Quản trị Dashboard của hệ thống Orchestrator"""
    html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return "<h1>Welcome to PTIT BaaS Orchestrator</h1> <p>Go to <a href='/docs'>/docs</a> to view APIs.</p>"