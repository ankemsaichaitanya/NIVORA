import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import Base, engine, SessionLocal
from app import models
from app.routers import patients, tests, dashboard, alerts, ai, ckd
from app.scheduler import start_scheduler, shutdown_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    # Auto-seed if empty
    db = SessionLocal()
    count = db.query(models.Patient).count()
    if count == 0:
        print("Empty database detected. Running automated seed...")
        from app.seed_data import seed
        seed()
    db.close()

    # Start SLA background engine
    start_scheduler()
    yield
    # Shutdown
    shutdown_scheduler()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="CareLoop: Clinical Closed-Loop Tracking System for Diagnostic Tests and Follow-Ups",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware to permit frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(dashboard.router)
app.include_router(patients.router)
app.include_router(tests.router)
app.include_router(alerts.router)
app.include_router(ai.router)
app.include_router(ckd.router)

@app.get("/")
def root():
    return {
        "status": "online",
        "system": "CareLoop Clinical Closed-Loop Tracking Engine",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
