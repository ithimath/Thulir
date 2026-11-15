from fastapi import FastAPI, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import SessionLocal, get_db
from backend.app.services.seed_service import seed_warning_rules
from backend.app.middleware.size_limit import RequestSizeLimitMiddleware
from backend.app.middleware.auth_middleware import get_current_user, AuthenticatedUser
from backend.app.models.models import AcademicYear, ReportingPeriod
from backend.app.routers import auth, students, indicators, cases, import_data, reports, support_requests, assistant, corrections, data_quality, rules

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

# 3. Exception Handlers (Preserve HTTP status codes and details)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    import logging
    logging.exception(f"Unhandled error on {request.method} {request.url.path}: {exc}")
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
app.include_router(corrections.router)
app.include_router(data_quality.router)
app.include_router(rules.router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": "THULIR",
        "environment": settings.APP_ENV,
    }

@app.get("/api/academic-year/current")
def get_current_academic_year(
    auth: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the current academic year and active reporting period for this school."""
    ay = db.query(AcademicYear).filter(
        AcademicYear.school_id == auth.school_id,
        AcademicYear.is_current == True
    ).first()
    if not ay:
        return {"year_name": "2025-26", "term_name": None, "term_sequence": None}

    # Find current reporting period
    current_period = db.query(ReportingPeriod).filter(
        ReportingPeriod.academic_year_id == ay.id,
        ReportingPeriod.is_current == True
    ).first()

    return {
        "year_name": ay.year_name,
        "term_name": current_period.name if current_period else None,
        "term_sequence": current_period.sequence_order if current_period else None,
    }
