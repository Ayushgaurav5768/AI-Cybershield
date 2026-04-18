from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import assistant, dashboard, reports, scan
from app.database.db import engine
from app.models.report_model import AllowlistEntry, ExtensionEvent, ScanFeedback, UserReport
from app.models.scan_detail_model import ScanDetail
from app.models.scan_model import Base, Scan
from app.rag.retriever import warm_assistant_assets
from core.config import settings
from core.security import rate_limiter

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

# Enable CORS
allowed_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def preload_assistant_stack():
    warm_assistant_assets()


@app.middleware("http")
async def apply_rate_limit(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    endpoint_limit = settings.max_scan_requests_per_minute if request.url.path == "/scan" else settings.max_general_requests_per_minute
    bucket_key = f"{client_ip}:{request.url.path}"

    if not rate_limiter.allow(bucket_key, endpoint_limit):
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Please try again shortly."})

    return await call_next(request)

# Include routers
app.include_router(scan.router)
app.include_router(dashboard.router)
app.include_router(assistant.router)
app.include_router(reports.router)

@app.get("/")
def root():
    return {"message": f"{settings.app_name} backend running", "environment": settings.environment}
