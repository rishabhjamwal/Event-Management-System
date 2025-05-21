# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from ems.api.v1 import auth_router, events_router, permissions_router, versions_router
from ems.core.config import settings
from ems.db.session import engine
from ems.db.base import Base 
from sqlalchemy import text


Base.metadata.create_all(bind=engine)
app = FastAPI(
    title=settings.SERVER_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
app.include_router(auth_router.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(events_router.router, prefix=f"{settings.API_V1_STR}/events", tags=["events"])
app.include_router(
    permissions_router.router, 
    prefix=f"{settings.API_V1_STR}/events", 
    tags=["permissions"]
)
app.include_router(
    versions_router.router, 
    prefix=f"{settings.API_V1_STR}/events", 
    tags=["versions"]
)
@app.get("/")
def read_root():
    return {"message": "Welcome to Event Management System API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}