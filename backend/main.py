from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Import our modular routers
from auth import router as auth_router
from activities import router as activities_router
from thresholds import router as thresholds_router
from onboarding import router as onboarding_router
from dashboard import router as dashboard_router
from intervals_icu import router as intervals_router

# Import config and models for scheduler
from config import SessionLocal
from models import User
from activities import sync_strava_activities

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Training Load API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(activities_router, prefix="/activities", tags=["Activities"])
app.include_router(thresholds_router, prefix="/thresholds", tags=["Thresholds"])
app.include_router(onboarding_router, prefix="/onboarding", tags=["Onboarding"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(intervals_router, prefix="/intervals", tags=["Intervals.icu"])

# APScheduler setup for background Strava sync
scheduler = BackgroundScheduler()

@app.on_event("startup")
def start_scheduler():
    scheduler.add_job(sync_strava_activities, IntervalTrigger(minutes=30))  # Runs every 30 minutes
    scheduler.start()
    logging.info("APScheduler started for Strava sync job.")

@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()
    logging.info("APScheduler shut down.")

@app.get("/")
def root():
    return {"message": "Training Load API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
