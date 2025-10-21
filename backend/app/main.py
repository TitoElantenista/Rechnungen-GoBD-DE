"""FastAPI Main Application - GoBD-konformer Rechnungsgenerator"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.api import invoices, auth, health, contacts

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Rechnungsgenerator GoBD",
    description="GoBD-konformer Rechnungsgenerator mit PDF/A-3 + ZUGFeRD",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host Middleware (Security)
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.yourdomain.com", "yourdomain.com"]
    )

# Include routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(contacts.router, prefix="/api/contacts", tags=["Contacts"])
app.include_router(invoices.router, prefix="/api/invoices", tags=["Invoices"])


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print(f"🚀 Starting Rechnungsgenerator GoBD v{app.version}")
    print(f"📁 Environment: {settings.ENVIRONMENT}")
    print(f"🗄️  Database: {settings.DATABASE_URL.split('@')[-1]}")
    print(f"☁️  S3 Storage: {settings.S3_ENDPOINT}")
    print(f"🔐 TSA: {settings.TSA_URL}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Shutting down Rechnungsgenerator GoBD")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Rechnungsgenerator GoBD",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }
