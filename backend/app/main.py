from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from backend.app.config import settings
from backend.app.database import SessionLocal
from backend.app.services.seed_service import seed_warning_rules
from backend.app.middleware.size_limit import RequestSizeLimitMiddleware
from backend.app.routers import auth, students, indicators, cases, import_data, reports, support_requests, assistant

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure baseline warning rules exist in DB
    db = SessionLocal()
    try:
        seed_warning_rules(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title="THULIR API",
    description="Student Early-Warning & Support System API for Government Schools",
    version="1.0.0",
    lifespan=lifespan,
)

# 1. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Request Size Limit Middleware (5 MB default)
app.add_middleware(RequestSizeLimitMiddleware, max_upload_size_mb=settings.MAX_UPLOAD_SIZE_MB)

# 3. Global Exception Handler (No sensitive stack traces leaked to user)
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    import logging
    logging.exception(f"Unhandled error on {request.method} {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact the administrator."},
    )

# 4. Include Routers
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(indicators.router)
app.include_router(cases.router)
app.include_router(import_data.router)
app.include_router(reports.router)
app.include_router(support_requests.router)
app.include_router(assistant.router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": "THULIR",
        "environment": settings.APP_ENV,
    }
