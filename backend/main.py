from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

# Import our modular routers
from auth import router as auth_router
from activities import router as activities_router
from thresholds import router as thresholds_router
from onboarding import router as onboarding_router
from dashboard import router as dashboard_router
from intervals_icu import router as intervals_router

# Import recommendation engine
from training_recommendations import TrainingRecommendationEngine

# Import config and models for scheduler
from config import SessionLocal, get_db
from models import User, Activity, Threshold
from activities import sync_strava_activities, _fetch_and_process_activities
from utils import calculate_utl, estimate_thresholds_from_activities
from research_threshold_calculator import calculate_initial_thresholds_for_new_user

logging.basicConfig(level=logging.INFO)

# Background job functions
def quick_sync_job():
    """Quick sync job (every 3-4 hours): fetch recent activities and wellness data."""
    logging.info("🚀 Starting quick sync job (3-4 hour interval)")
    try:
        db = SessionLocal()
        users = db.query(User).filter(User.strava_oauth_token.isnot(None)).all()
        
        total_new_activities = 0
        total_users_synced = 0
        
        for user in users:
            try:
                logging.info(f"Quick sync for user {user.user_id}")
                
                # Import last 3 days (shorter timeframe for frequent sync)
                pre_count = db.query(Activity).filter_by(user_id=user.user_id).count()
                _fetch_and_process_activities(user.user_id, db, backfill_days=3)
                post_count = db.query(Activity).filter_by(user_id=user.user_id).count()
                new_activities = post_count - pre_count
                total_new_activities += new_activities
                
                if new_activities > 0:
                    logging.info(f"User {user.user_id}: imported {new_activities} new activities")
                    
                    # If new activities found, check for threshold updates
                    from datetime import datetime, timedelta
                    week_ago = datetime.now() - timedelta(days=7)
                    recent_significant = db.query(Activity).filter(
                        Activity.user_id == user.user_id,
                        Activity.start_date >= week_ago,
                        Activity.type.in_(['Ride', 'VirtualRide', 'Run', 'VirtualRun']),
                        Activity.moving_time > 1800  # >30 minutes
                    ).count()
                    
                    if recent_significant >= 3:
                        logging.info(f"User {user.user_id}: {recent_significant} significant activities, updating thresholds")
                        recalculate_thresholds_for_user(user.user_id)
                
                # Sync wellness data from intervals.icu (last 7 days)
                try:
                    if user.integrations and 'intervals_icu' in user.integrations:
                        intervals_config = user.integrations['intervals_icu']
                        if intervals_config.get('api_key') and intervals_config.get('athlete_id'):
                            from intervals_icu import _sync_wellness_data_task
                            _sync_wellness_data_task(
                                user.user_id, 
                                intervals_config['api_key'],
                                intervals_config['athlete_id'], 
                                7,  # Last 7 days for quick sync
                                db
                            )
                            logging.info(f"User {user.user_id}: synced wellness data")
                except Exception as wellness_error:
                    logging.debug(f"User {user.user_id}: wellness sync failed: {wellness_error}")
                
                total_users_synced += 1
                
            except Exception as e:
                logging.error(f"Quick sync error for user {user.user_id}: {e}")
        
        db.close()
        logging.info(f"Quick sync completed: {total_new_activities} new activities across {total_users_synced} users")
        
    except Exception as e:
        logging.error(f"Quick sync job failed: {e}")


def daily_sync_job():
    """Daily job: comprehensive sync and maintenance."""
    logging.info("🔄 Starting daily comprehensive sync job")
    try:
        # Get all users with Strava tokens
        db = SessionLocal()
        users = db.query(User).filter(User.strava_oauth_token.isnot(None)).all()
        
        for user in users:
            try:
                logging.info(f"Daily comprehensive sync for user {user.user_id}")
                
                # Import last 14 days (longer lookback for daily comprehensive sync)
                pre_count = db.query(Activity).filter_by(user_id=user.user_id).count()
                _fetch_and_process_activities(user.user_id, db, backfill_days=14)
                post_count = db.query(Activity).filter_by(user_id=user.user_id).count()
                new_activities = post_count - pre_count
                
                logging.info(f"User {user.user_id}: imported {new_activities} new activities")
                
                # Check for threshold updates and wellness data sync
                from datetime import datetime, timedelta
                week_ago = datetime.now() - timedelta(days=7)
                recent_significant = db.query(Activity).filter(
                    Activity.user_id == user.user_id,
                    Activity.start_date >= week_ago,
                    Activity.type.in_(['Ride', 'VirtualRide', 'Run', 'VirtualRun']),
                    Activity.moving_time > 1800  # >30 minutes
                ).count()
                
                if recent_significant >= 3:
                    logging.info(f"User {user.user_id}: {recent_significant} significant activities, updating thresholds")
                    recalculate_thresholds_for_user(user.user_id)
                
                # Comprehensive wellness data sync (last 30 days for daily job)
                try:
                    if user.integrations and 'intervals_icu' in user.integrations:
                        intervals_config = user.integrations['intervals_icu']
                        if intervals_config.get('api_key') and intervals_config.get('athlete_id'):
                            from intervals_icu import _sync_wellness_data_task
                            _sync_wellness_data_task(
                                user.user_id, 
                                intervals_config['api_key'],
                                intervals_config['athlete_id'], 
                                30,  # Last 30 days for comprehensive daily sync
                                db
                            )
                            logging.info(f"User {user.user_id}: comprehensive wellness data sync completed")
                except Exception as wellness_error:
                    logging.debug(f"User {user.user_id}: wellness sync failed: {wellness_error}")
                
                # Update resting HR from recent wellness data if available
                try:
                    from intervals_icu import update_resting_hr_from_wellness
                    updated_rhr = update_resting_hr_from_wellness(user.user_id, db)
                    if updated_rhr:
                        logging.info(f"User {user.user_id}: updated resting HR to {updated_rhr} bpm from wellness data")
                except Exception as rhr_error:
                    logging.debug(f"User {user.user_id}: resting HR update failed: {rhr_error}")
                
            except Exception as e:
                logging.error(f"Daily comprehensive sync error for user {user.user_id}: {e}")
        
        db.close()
        logging.info("Daily comprehensive sync completed successfully")
        
    except Exception as e:
        logging.error(f"Daily sync job failed: {e}")


def weekly_threshold_job():
    """Weekly job: full threshold recalculation for all users."""
    logging.info("🧮 Starting weekly threshold recalculation")
    try:
        db = SessionLocal()
        users = db.query(User).filter(User.strava_oauth_token.isnot(None)).all()
        
        for user in users:
            try:
                recalculate_thresholds_for_user(user.user_id)
                
                # Also update resting HR from wellness data (longer lookback for weekly job)
                try:
                    from intervals_icu import update_resting_hr_from_wellness
                    updated_rhr = update_resting_hr_from_wellness(user.user_id, db, lookback_days=30)
                    if updated_rhr:
                        logging.info(f"User {user.user_id}: weekly resting HR update to {updated_rhr} bpm")
                except Exception as rhr_error:
                    logging.debug(f"User {user.user_id}: weekly resting HR update failed: {rhr_error}")
                
                logging.info(f"Weekly threshold update completed for user {user.user_id}")
            except Exception as e:
                logging.error(f"Weekly threshold update failed for user {user.user_id}: {e}")
        
        db.close()
        
    except Exception as e:
        logging.error(f"Weekly threshold job failed: {e}")


def monthly_utl_job():
    """Monthly job: recalculate UTL scores for accuracy."""
    logging.info("📊 Starting monthly UTL recalculation")
    try:
        db = SessionLocal()
        users = db.query(User).filter(User.strava_oauth_token.isnot(None)).all()
        
        for user in users:
            try:
                recalculate_utl_for_user(user.user_id, db)
                logging.info(f"Monthly UTL recalc completed for user {user.user_id}")
            except Exception as e:
                logging.error(f"Monthly UTL recalc failed for user {user.user_id}: {e}")
        
        db.close()
        
    except Exception as e:
        logging.error(f"Monthly UTL job failed: {e}")


def resting_hr_update_job():
    """Dedicated job: update resting HR from wellness data for all users."""
    logging.info("💓 Starting resting HR update job")
    try:
        db = SessionLocal()
        users = db.query(User).filter(User.strava_oauth_token.isnot(None)).all()
        
        updated_users = 0
        for user in users:
            try:
                from intervals_icu import update_resting_hr_from_wellness
                updated_rhr = update_resting_hr_from_wellness(user.user_id, db, lookback_days=14)
                if updated_rhr:
                    updated_users += 1
                    logging.info(f"User {user.user_id}: updated resting HR to {updated_rhr} bpm")
            except Exception as e:
                logging.debug(f"User {user.user_id}: resting HR update failed: {e}")
        
        db.close()
        logging.info(f"Resting HR update job completed: {updated_users} users updated")
        
    except Exception as e:
        logging.error(f"Resting HR update job failed: {e}")


def recalculate_thresholds_for_user(user_id: int):
    """Recalculate thresholds for a specific user."""
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            return
        
        # Get activities from the last 12 months
        from datetime import datetime, timedelta
        one_year_ago = datetime.now() - timedelta(days=365)
        activities = db.query(Activity).filter(
            Activity.user_id == user_id,
            Activity.start_date >= one_year_ago
        ).all()
        
        # Prepare activity data
        activity_data = []
        for act in activities:
            activity_summary = {
                'type': act.type,
                'moving_time': act.moving_time,
                'average_speed': act.average_speed,
                'average_watts': act.data.get('average_watts') if act.data else None,
                'max_heartrate': act.data.get('max_heartrate') if act.data else None,
                'distance': act.distance,
                'start_date': act.start_date,
                'name': act.name
            }
            activity_data.append(activity_summary)
        
        # Calculate new thresholds
        try:
            estimates = calculate_initial_thresholds_for_new_user(user_id)
        except Exception:
            # Fall back to activity-based estimation
            estimates = estimate_thresholds_from_activities(activity_data, user.gender or 'M', [])
        
        if estimates:
            # Update thresholds in database
            threshold = db.query(Threshold).filter_by(user_id=user_id).first()
            if not threshold:
                threshold = Threshold(user_id=user_id)
                db.add(threshold)
            
            old_ftp = threshold.ftp_watts
            old_fthp = threshold.fthp_mps
            
            if estimates.get('ftp_watts'):
                threshold.ftp_watts = estimates['ftp_watts']
            if estimates.get('fthp_mps'):
                threshold.fthp_mps = estimates['fthp_mps']
            if estimates.get('max_hr'):
                threshold.max_hr = estimates['max_hr']
            if estimates.get('resting_hr'):
                threshold.resting_hr = estimates['resting_hr']
            
            threshold.date_updated = datetime.now()
            
            # Check for significant changes (>5%)
            ftp_change = abs((threshold.ftp_watts or 0) - (old_ftp or 0)) / max(old_ftp or 1, 1)
            fthp_change = abs((threshold.fthp_mps or 0) - (old_fthp or 0)) / max(old_fthp or 1, 1)
            
            if ftp_change > 0.05 or fthp_change > 0.05:
                logging.info(f"Significant threshold change for user {user_id}, triggering UTL recalc")
                db.commit()
                recalculate_utl_for_user(user_id, db)
            else:
                db.commit()
            
    finally:
        db.close()


def recalculate_utl_for_user(user_id: int, db_session=None):
    """Recalculate UTL scores for a specific user."""
    db = db_session or SessionLocal()
    close_db = db_session is None
    
    try:
        threshold = db.query(Threshold).filter_by(user_id=user_id).first()
        if not threshold:
            return
        
        # Get recent activities (last 90 days)
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=90)
        activities = db.query(Activity).filter(
            Activity.user_id == user_id,
            Activity.start_date >= cutoff_date
        ).all()
        
        updated_count = 0
        for activity in activities:
            try:
                activity_summary = {
                    'type': activity.type,
                    'moving_time': activity.moving_time,
                    'distance': activity.distance,
                    'average_speed': activity.average_speed,
                    'start_date': activity.start_date.isoformat() if activity.start_date else None
                }
                
                activity_streams = activity.data.get('streams') if activity.data else None
                
                # Recalculate UTL
                new_utl, new_method = calculate_utl(activity_summary, threshold, activity_streams)
                
                # Update if significantly different
                old_utl = activity.utl_score or 0
                if abs(new_utl - old_utl) > 0.05 * max(old_utl, 1) or activity.calculation_method != new_method:
                    activity.utl_score = float(new_utl)
                    activity.calculation_method = new_method
                    updated_count += 1
            
            except Exception as e:
                logging.error(f"Error recalculating UTL for activity {activity.strava_activity_id}: {e}")
        
        db.commit()
        logging.info(f"Updated UTL for {updated_count} activities for user {user_id}")
        
    finally:
        if close_db:
            db.close()

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

# Training Recommendations API
recommendation_engine = TrainingRecommendationEngine()

@app.get("/recommendations/{user_id}")
async def get_training_recommendations(user_id: int, db: Session = Depends(get_db)):
    """
    Generate science-based training recommendations for the next 5 days.
    """
    try:
        recommendations = recommendation_engine.generate_recommendations(user_id, db)
        return {"status": "success", "data": recommendations}
    except Exception as e:
        logging.error(f"Failed to generate recommendations for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# APScheduler setup for background processing
jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///scheduler_jobs.sqlite')
}
executors = {
    'default': ThreadPoolExecutor(20),
}
job_defaults = {
    'coalesce': False,
    'max_instances': 1
}

scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults
)

@app.on_event("startup")
def start_scheduler():
    # Quick sync job (every 3.5 hours) - replaces old 30-minute Strava sync
    scheduler.add_job(
        func=quick_sync_job, 
        trigger=IntervalTrigger(hours=3, minutes=30),  # Every 3.5 hours
        id='quick_sync',
        name='Quick Sync (Activities + Wellness)',
        replace_existing=True
    )
    
    # Daily comprehensive sync (every day at 2 AM)
    scheduler.add_job(
        func=daily_sync_job,
        trigger=CronTrigger(hour=2, minute=0),
        id='daily_sync',
        name='Daily Activity Sync and Threshold Check',
        replace_existing=True
    )
    
    # Weekly threshold recalculation (Sunday at 3 AM)
    scheduler.add_job(
        func=weekly_threshold_job,
        trigger=CronTrigger(day_of_week='sun', hour=3, minute=0),
        id='weekly_thresholds',
        name='Weekly Threshold Recalculation',
        replace_existing=True
    )
    
    # Monthly UTL recalculation (1st of month at 4 AM)
    scheduler.add_job(
        func=monthly_utl_job,
        trigger=CronTrigger(day=1, hour=4, minute=0),
        id='monthly_utl',
        name='Monthly UTL Recalculation',
        replace_existing=True
    )
    
    # Resting HR update from wellness data (every 3 days at 5 AM)
    scheduler.add_job(
        func=resting_hr_update_job,
        trigger=CronTrigger(day='*/3', hour=5, minute=0),
        id='resting_hr_update',
        name='Resting HR Update from Wellness Data',
        replace_existing=True
    )
    
    scheduler.start()
    
    # Log all scheduled jobs
    jobs = scheduler.get_jobs()
    logging.info(f"APScheduler started with {len(jobs)} background jobs:")
    for job in jobs:
        next_run = job.next_run_time
        logging.info(f"  • {job.name}: next run at {next_run}")

@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()
    logging.info("APScheduler shut down.")

@app.get("/")
def root():
    return {"message": "Training Load API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": "2025-09-04T22:30:00Z"}

@app.get("/scheduler/jobs")
def get_scheduled_jobs():
    """Get status of all scheduled background jobs."""
    try:
        jobs = scheduler.get_jobs()
        job_status = []
        
        for job in jobs:
            job_info = {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
                "function": job.func.__name__ if hasattr(job.func, '__name__') else str(job.func)
            }
            job_status.append(job_info)
        
        return {
            "total_jobs": len(jobs),
            "scheduler_running": scheduler.running,
            "jobs": job_status
        }
        
    except Exception as e:
        return {"error": f"Failed to get job status: {str(e)}"}

@app.post("/scheduler/run/{job_id}")
def run_job_now(job_id: str):
    """Manually trigger a scheduled job to run now."""
    try:
        job = scheduler.get_job(job_id)
        if not job:
            return {"error": f"Job {job_id} not found"}
        
        # Run the job function directly
        if job_id == 'quick_sync':
            quick_sync_job()
        elif job_id == 'sync_strava_activities':  # Keep for backward compatibility
            sync_strava_activities()
        elif job_id == 'daily_sync':
            daily_sync_job()
        elif job_id == 'weekly_thresholds':
            weekly_threshold_job()
        elif job_id == 'monthly_utl':
            monthly_utl_job()
        elif job_id == 'resting_hr_update':
            resting_hr_update_job()
        else:
            return {"error": f"Job {job_id} cannot be run manually"}
        
        return {"message": f"Job {job_id} executed successfully"}
        
    except Exception as e:
        return {"error": f"Failed to run job {job_id}: {str(e)}"}

@app.post("/sync/test/{user_id}")
def test_user_sync(user_id: int, db: Session = Depends(get_db)):
    """Test sync for a specific user (Strava + Intervals.icu)"""
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            return {"error": f"User {user_id} not found"}
        
        # Test Strava sync
        pre_count = db.query(Activity).filter_by(user_id=user_id).count()
        _fetch_and_process_activities(user_id, db, backfill_days=3)
        post_count = db.query(Activity).filter_by(user_id=user_id).count()
        new_activities = post_count - pre_count
        
        # Test wellness sync
        wellness_synced = False
        if user.integrations and 'intervals_icu' in user.integrations:
            intervals_config = user.integrations['intervals_icu']
            if intervals_config.get('api_key') and intervals_config.get('athlete_id'):
                try:
                    from intervals_icu import _sync_wellness_data_task
                    _sync_wellness_data_task(
                        user_id, 
                        intervals_config['api_key'],
                        intervals_config['athlete_id'], 
                        7,
                        db
                    )
                    wellness_synced = True
                except Exception as e:
                    logging.error(f"Wellness sync failed: {e}")
        
        return {
            "message": f"Test sync completed for user {user_id}",
            "new_activities": new_activities,
            "wellness_synced": wellness_synced,
            "has_strava": user.strava_oauth_token is not None,
            "has_intervals": bool(user.integrations and 'intervals_icu' in user.integrations)
        }
        
    except Exception as e:
        logging.error(f"Test sync failed for user {user_id}: {e}")
        return {"error": f"Test sync failed: {str(e)}"}
    return {"status": "healthy"}
