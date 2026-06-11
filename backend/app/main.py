from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import engine, Base
from .routers import (
    auth, study_rooms, shifts, signups, attendance,
    leave, volunteers, stats, audit, duplicate_checks
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    description="城市书房志愿排班系统 API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(study_rooms.router)
app.include_router(shifts.router)
app.include_router(signups.router)
app.include_router(attendance.router)
app.include_router(leave.router)
app.include_router(volunteers.router)
app.include_router(stats.router)
app.include_router(audit.router)
app.include_router(duplicate_checks.router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": "1.0.0"
    }


@app.get("/")
def root():
    return {
        "message": "城市书房志愿排班系统",
        "docs": "/docs",
        "health": "/health"
    }
