"""
FastAPI application entry point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import time
import uuid

from .config import settings
from .db.session import get_db
from .api.routes import projects, tasks, files, variants, generators, workflow, auth, analytics
from .core.logging_config import setup_logging, get_logger
from .core.redis import init_redis, close_redis, get_redis
from .middleware.security import setup_security, XSSProtectionMiddleware
from .middleware.rate_limit import setup_rate_limiting

# Setup logging on startup
setup_logging(settings.LOG_LEVEL, settings.LOG_FORMAT)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("Starting up Ops-Video API...")

    # Initialize Redis
    redis_connected = await init_redis()
    if redis_connected:
        logger.info("Redis connection established")
    else:
        logger.warning("Redis not available, caching and rate limiting disabled")

    yield

    # Shutdown
    logger.info("Shutting down Ops-Video API...")
    await close_redis()
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Ops-Video: Automatic manga video generation workflow",
    lifespan=lifespan,
)

# Security middleware (CORS + Security Headers)
setup_security(app, allowed_origins=settings.cors_origins)

# XSS Protection
app.add_middleware(XSSProtectionMiddleware)

# Rate Limiting (requires Redis)
setup_rate_limiting(app, requests_per_minute=60, burst=100)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Middleware for logging requests and responses"""
    # Generate request ID
    request_id = str(uuid.uuid4())[:8]

    # Get start time for performance tracking
    start_time = time.time()

    # Log request
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            'request_id': request_id,
            'method': request.method,
            'path': request.url.path,
            'client': request.client.host if request.client else 'unknown',
        }
    )

    # Process request
    try:
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}"

        # Log response
        log_level = "warning" if response.status_code >= 400 else "info"
        getattr(logger, log_level)(
            f"Request completed: {response.status_code} in {process_time:.4f}s",
            extra={
                'request_id': request_id,
                'status_code': response.status_code,
                'process_time': process_time,
            }
        )

        return response

    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url.path} - {str(e)}",
            extra={
                'request_id': request_id,
                'error': str(e),
                'process_time': process_time,
            },
            exc_info=True,
        )
        raise


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health(db: Session = Depends(get_db)):
    """
    Comprehensive health check endpoint

    Returns status of:
    - API itself
    - Database connection
    - Redis connection (if configured)
    """
    from sqlalchemy import text

    health_status = {
        "status": "healthy",
        "version": settings.VERSION,
        "checks": {},
    }

    # Check database
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection OK"
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": str(e)
        }
        health_status["status"] = "degraded"

    # Check Redis
    redis_client = get_redis()
    if redis_client.is_connected:
        try:
            await redis_client.get("health_check")
            health_status["checks"]["redis"] = {
                "status": "healthy",
                "message": "Redis connection OK"
            }
        except Exception as e:
            health_status["checks"]["redis"] = {
                "status": "unhealthy",
                "message": str(e)
            }
            health_status["status"] = "degraded"
    else:
        health_status["checks"]["redis"] = {
            "status": "disabled",
            "message": "Redis not configured"
        }

    return health_status


@app.get("/ready")
async def ready():
    """
    Readiness probe endpoint

    Returns 200 only if all critical services are healthy
    """
    from .db.session import engine
    from sqlalchemy import text

    # Check database
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "Database connection failed"}
        )

    return {"status": "ready"}


# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(files.router, prefix="/api/v1/files", tags=["files"])
app.include_router(variants.router, prefix="/api/v1/variants", tags=["variants"])
app.include_router(generators.router, prefix="/api/v1/generators", tags=["generators"])
app.include_router(workflow.router, prefix="/api/v1/workflow", tags=["workflow"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
