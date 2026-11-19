# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import KolixException
import structlog

logger = structlog.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Démarrage de l'API Kolix Backend...", version=settings.VERSION, env=settings.ENVIRONMENT)
    yield
    # Shutdown
    logger.info("Arrêt propre des services Kolix Backend...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Moteur Backend Asynchrone Haute Performance pour la plateforme SaaS Kolix COD",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
@app.exception_handler(KolixException)
async def kolix_exception_handler(request: Request, exc: KolixException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "data": None
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("Erreur serveur non gérée", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": f"Une erreur interne s'est produite : {str(exc)}" if settings.DEBUG else "Une erreur interne s'est produite.",
            "data": None
        }
    )

# Routes Globales
@app.get("/", tags=["Racine"])
async def root():
    return {
        "status": "online",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", tags=["Santé"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

# Inclusion de l'API v1
app.include_router(api_router, prefix=settings.API_V1_STR)

# WebSocket direct root route
from app.api.v1.endpoints.websocket import websocket_shop_endpoint
app.websocket("/ws/{shop_id}")(websocket_shop_endpoint)

