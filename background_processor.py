#!/usr/bin/env python3
"""
Background Processing System for TrainingLoad using APScheduler

This system handles:
1. Periodic activity import from Strava (daily)
2. Threshold recalculation when new significant activities are imported
3. UTL score updates when thresholds change
4. Historical data backfill for new users (full Strava history)

Usage:
    python background_processor.py --start-scheduler    # Start background scheduler
    python background_processor.py --mode=full_import --user_id=1    # One-time operations
    python background_processor.py --mode=daily_sync
    python background_processor.py --mode=threshold_update --user_id=1
"""

import argparse
import logging
import sys
import time
import signal
import atexit
from datetime import datetime, timedelta
from typing import Optional, List

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

# Add backend to path
import os
from dotenv import load_dotenv

# Load environment from the project root
project_root = os.path.dirname(__file__)
load_dotenv(os.path.join(project_root, '.env'))

sys.path.insert(0, os.path.join(project_root, 'backend'))

from config import SessionLocal
from models import User, Activity, Threshold
from activities import _fetch_and_process_activities
from research_threshold_calculator import calculate_initial_thresholds_for_new_user
from utils import calculate_utl, estimate_thresholds_from_activities

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/background_processor.log'),
        logging.StreamHandler()
    ]
)

# Global scheduler instance
scheduler = None


def setup_scheduler():
    """
    Setup APScheduler with SQLite job store and proper configuration.
    """
    global scheduler
    
    # Job store configuration - use SQLite for persistence
    jobstores = {
        'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
    }
    
    # Executor configuration
    executors = {
        'default': ThreadPoolExecutor(20),
    }
    
    # Job defaults
    job_defaults = {
        'coalesce': False,
        'max_instances': 1
    }
    
    # Create scheduler
    scheduler = BackgroundScheduler(
        jobstores=jobstores,
        executors=executors, 
        job_defaults=job_defaults
    )
    
    return scheduler


def setup_scheduled_jobs():
    """
    Setup all scheduled background jobs.
    """
    global scheduler
    
    if not scheduler:
        scheduler = setup_scheduler()
    
    # Clear existing jobs to avoid duplicates
    scheduler.remove_all_jobs()
    
    logging.info("Setting up scheduled background jobs...")
    
    # 1. Daily sync - every day at 2:00 AM
    scheduler.add_job(
        func=daily_sync_job,
        trigger=CronTrigger(hour=2, minute=0),
        id='daily_sync',
        name='Daily Activity Sync and Threshold Check',
        replace_existing=True
    )
    logging.info("✓ Scheduled daily sync at 2:00 AM")
    
    # 2. Weekly threshold recalculation - Sunday at 3:00 AM  
    scheduler.add_job(
        func=weekly_threshold_job,
        trigger=CronTrigger(day_of_week='sun', hour=3, minute=0),
        id='weekly_thresholds',
        name='Weekly Threshold Recalculation',
        replace_existing=True
    )
    logging.info("✓ Scheduled weekly threshold recalc on Sunday at 3:00 AM")
    
    # 3. Monthly UTL recalculation - 1st of each month at 4:00 AM
    scheduler.add_job(
        func=monthly_utl_job,
        trigger=CronTrigger(day=1, hour=4, minute=0),
        id='monthly_utl',
        name='Monthly UTL Recalculation',
        replace_existing=True
    )
    logging.info("✓ Scheduled monthly UTL recalc on 1st at 4:00 AM")
    
    # 4. Health check every hour - make sure system is responsive
    scheduler.add_job(
        func=health_check_job,
        trigger=IntervalTrigger(hours=1),
        id='health_check',
        name='System Health Check',
        replace_existing=True
    )
    logging.info("✓ Scheduled health check every hour")
    
    logging.info(f"All {len(scheduler.get_jobs())} background jobs scheduled successfully!")


def daily_sync_job():
    """Daily job: sync activities and check for threshold updates."""
    logging.info("🔄 Starting daily sync job")
    try:
        processor = BackgroundProcessor()
        result = processor.daily_sync()
        logging.info(f"Daily sync completed: {result}")
    except Exception as e:
        logging.error(f"Daily sync failed: {e}")


def weekly_threshold_job():
    """Weekly job: full threshold recalculation for all users."""
    logging.info("🧮 Starting weekly threshold recalculation")
    try:
        processor = BackgroundProcessor()
        db = SessionLocal()
        
        users = db.query(User).filter(User.strava_oauth_token.isnot(None)).all()
        db.close()
        
        for user in users:
            try:
                result = processor.recalculate_thresholds(user.user_id)
                logging.info(f"Weekly threshold update for user {user.user_id}: {result.get('message', 'completed')}")
            except Exception as e:
                logging.error(f"Weekly threshold update failed for user {user.user_id}: {e}")
                
    except Exception as e:
        logging.error(f"Weekly threshold job failed: {e}")


def monthly_utl_job():
    """Monthly job: recalculate UTL scores for accuracy."""
    logging.info("📊 Starting monthly UTL recalculation")
    try:
        processor = BackgroundProcessor()
        db = SessionLocal()
        
        users = db.query(User).filter(User.strava_oauth_token.isnot(None)).all()
        db.close()
        
        for user in users:
            try:
                result = processor.recalculate_utl_scores(user.user_id, days_back=90)
                logging.info(f"Monthly UTL recalc for user {user.user_id}: {result.get('message', 'completed')}")
            except Exception as e:
                logging.error(f"Monthly UTL recalc failed for user {user.user_id}: {e}")
                
    except Exception as e:
        logging.error(f"Monthly UTL job failed: {e}")


def health_check_job():
    """Hourly job: basic system health check."""
    try:
        # Test database connection
        db = SessionLocal()
        user_count = db.query(User).count()
        db.close()
        
        # Test scheduler health
        job_count = len(scheduler.get_jobs())
        
        logging.debug(f"Health check OK: {user_count} users, {job_count} scheduled jobs")
        
    except Exception as e:
        logging.warning(f"Health check failed: {e}")


def start_scheduler_daemon():
    """Start the background scheduler as a daemon process."""
    global scheduler
    
    if not scheduler:
        setup_scheduled_jobs()
    
    # Setup graceful shutdown
    def shutdown_handler(signum, frame):
        logging.info("🛑 Shutdown signal received, stopping scheduler...")
        if scheduler and scheduler.running:
            scheduler.shutdown(wait=True)
        logging.info("✅ Scheduler stopped gracefully")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    atexit.register(lambda: scheduler.shutdown(wait=True) if scheduler and scheduler.running else None)
    
    try:
        logging.info("🚀 Starting TrainingLoad background scheduler...")
        scheduler.start()
        
        # Log initial job status
        jobs = scheduler.get_jobs()
        logging.info(f"📋 Active jobs ({len(jobs)}):")
        for job in jobs:
            next_run = job.next_run_time
            logging.info(f"  • {job.name}: next run at {next_run}")
        
        # Keep the main thread alive
        logging.info("🔄 Background scheduler running... Press Ctrl+C to stop")
        
        # Use a blocking scheduler for the main thread
        while True:
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logging.info("🛑 Keyboard interrupt received")
    except Exception as e:
        logging.error(f"❌ Scheduler error: {e}")
    finally:
        if scheduler and scheduler.running:
            scheduler.shutdown(wait=True)
        logging.info("✅ Background scheduler stopped")


class BackgroundProcessor:
    def __init__(self):
        self.db = SessionLocal()
    
    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()
    
    def full_historical_import(self, user_id: int, days_back: int = 365 * 2) -> dict:
        """
        Import full Strava history for a user to get the most accurate thresholds.
        This should be run for new users or when they want better threshold accuracy.
        """
        logging.info(f"Starting full historical import for user {user_id} ({days_back} days)")
        
        user = self.db.query(User).filter_by(user_id=user_id).first()
        if not user:
            return {"error": f"User {user_id} not found"}
        
        # Import activities in chunks to avoid API rate limits
        chunk_size = 90  # 90-day chunks
        total_imported = 0
        
        for chunk_start in range(0, days_back, chunk_size):
            chunk_end = min(chunk_start + chunk_size, days_back)
            logging.info(f"Importing days {chunk_start}-{chunk_end} for user {user_id}")
            
            try:
                # Import this chunk
                pre_count = self.db.query(Activity).filter_by(user_id=user_id).count()
                _fetch_and_process_activities(user_id, self.db, backfill_days=chunk_end)
                post_count = self.db.query(Activity).filter_by(user_id=user_id).count()
                chunk_imported = post_count - pre_count
                total_imported += chunk_imported
                
                logging.info(f"Imported {chunk_imported} activities in chunk {chunk_start}-{chunk_end}")
                
                # Rate limiting - wait between chunks
                if chunk_end < days_back:
                    time.sleep(2)
                    
            except Exception as e:
                logging.error(f"Error importing chunk {chunk_start}-{chunk_end}: {e}")
                continue
        
        logging.info(f"Total imported: {total_imported} activities for user {user_id}")
        
        # Now recalculate thresholds with full dataset
        self.recalculate_thresholds(user_id)
        
        return {
            "message": f"Full historical import complete for user {user_id}",
            "activities_imported": total_imported,
            "days_imported": days_back
        }
    
    def recalculate_thresholds(self, user_id: int) -> dict:
        """
        Recalculate thresholds based on all available activity data.
        Uses stream analysis to find actual best performances.
        """
        logging.info(f"Recalculating thresholds for user {user_id}")
        
        user = self.db.query(User).filter_by(user_id=user_id).first()
        if not user:
            return {"error": f"User {user_id} not found"}
        
        # Get all activities from the last 12 months for threshold analysis
        one_year_ago = datetime.now() - timedelta(days=365)
        activities = self.db.query(Activity).filter(
            Activity.user_id == user_id,
            Activity.start_date >= one_year_ago
        ).all()
        
        logging.info(f"Analyzing {len(activities)} activities for threshold calculation")
        
        # Prepare activity data for threshold estimation
        activity_data = []
        activities_with_streams = []
        
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
            
            # Include stream data for advanced analysis
            if act.data and 'streams' in act.data and act.data['streams']:
                activities_with_streams.append((activity_summary, act.data['streams']))
        
        # Calculate new thresholds
        try:
            # First try research-based calculation
            estimates = calculate_initial_thresholds_for_new_user(user_id)
            logging.info(f"Research-based thresholds: {estimates}")
        except Exception as e:
            logging.warning(f"Research-based calculation failed, using activity analysis: {e}")
            # Fall back to activity-based estimation
            estimates = estimate_thresholds_from_activities(activity_data, user.gender, activities_with_streams)
        
        if not estimates:
            return {"error": "Could not calculate thresholds from available data"}
        
        # Update thresholds in database
        threshold = self.db.query(Threshold).filter_by(user_id=user_id).first()
        if not threshold:
            threshold = Threshold(user_id=user_id)
            self.db.add(threshold)
        
        old_ftp = threshold.ftp_watts
        old_fthp = threshold.fthp_mps
        
        threshold.ftp_watts = estimates.get('ftp_watts')
        threshold.fthp_mps = estimates.get('fthp_mps')
        threshold.max_hr = estimates.get('max_hr')
        threshold.resting_hr = estimates.get('resting_hr')
        threshold.date_updated = datetime.now()
        
        # Check if thresholds changed significantly (>5%)
        ftp_change = abs((threshold.ftp_watts or 0) - (old_ftp or 0)) / max(old_ftp or 1, 1)
        fthp_change = abs((threshold.fthp_mps or 0) - (old_fthp or 0)) / max(old_fthp or 1, 1)
        
        significant_change = ftp_change > 0.05 or fthp_change > 0.05
        
        self.db.commit()
        
        result = {
            "message": f"Thresholds recalculated for user {user_id}",
            "old_ftp": old_ftp,
            "new_ftp": threshold.ftp_watts,
            "old_fthp": old_fthp,
            "new_fthp": threshold.fthp_mps,
            "significant_change": significant_change,
            "activities_analyzed": len(activities)
        }
        
        # If thresholds changed significantly, trigger UTL recalculation
        if significant_change:
            logging.info(f"Significant threshold change detected, triggering UTL recalculation")
            self.recalculate_utl_scores(user_id)
            result["utl_recalculated"] = True
        
        return result
    
    def recalculate_utl_scores(self, user_id: int, days_back: int = 90) -> dict:
        """
        Recalculate UTL scores for recent activities using current thresholds.
        """
        logging.info(f"Recalculating UTL scores for user {user_id} (last {days_back} days)")
        
        threshold = self.db.query(Threshold).filter_by(user_id=user_id).first()
        if not threshold:
            return {"error": "No thresholds found for user"}
        
        # Get recent activities
        cutoff_date = datetime.now() - timedelta(days=days_back)
        activities = self.db.query(Activity).filter(
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
                
                activity_streams = None
                if activity.data and isinstance(activity.data, dict):
                    activity_streams = activity.data.get('streams')
                
                # Recalculate UTL
                new_utl, new_method = calculate_utl(activity_summary, threshold, activity_streams)
                
                # Update if significantly different (>5% or method changed)
                old_utl = activity.utl_score or 0
                if abs(new_utl - old_utl) > 0.05 * max(old_utl, 1) or activity.calculation_method != new_method:
                    activity.utl_score = float(new_utl)
                    activity.calculation_method = new_method
                    updated_count += 1
                    
                    if updated_count <= 5:  # Log first few for verification
                        logging.info(f"Updated UTL for {activity.strava_activity_id}: {old_utl:.2f} -> {new_utl:.2f}")
            
            except Exception as e:
                logging.error(f"Error recalculating UTL for activity {activity.strava_activity_id}: {e}")
                continue
        
        self.db.commit()
        
        return {
            "message": f"Recalculated UTL for {updated_count} activities",
            "activities_checked": len(activities),
            "activities_updated": updated_count
        }
    
    def daily_sync(self) -> dict:
        """
        Daily sync process for all users:
        1. Import last 7 days of activities
        2. Check for threshold updates if significant new activities
        """
        logging.info("Starting daily sync for all users")
        
        users = self.db.query(User).filter(User.strava_oauth_token.isnot(None)).all()
        results = []
        
        for user in users:
            try:
                logging.info(f"Daily sync for user {user.user_id}")
                
                # Import last 7 days
                pre_count = self.db.query(Activity).filter_by(user_id=user.user_id).count()
                _fetch_and_process_activities(user.user_id, self.db, backfill_days=7)
                post_count = self.db.query(Activity).filter_by(user_id=user.user_id).count()
                new_activities = post_count - pre_count
                
                result = {
                    "user_id": user.user_id,
                    "new_activities": new_activities,
                    "threshold_updated": False
                }
                
                # Check if we should update thresholds (if >3 significant activities this week)
                week_ago = datetime.now() - timedelta(days=7)
                recent_significant = self.db.query(Activity).filter(
                    Activity.user_id == user.user_id,
                    Activity.start_date >= week_ago,
                    Activity.type.in_(['Ride', 'VirtualRide', 'Run', 'VirtualRun']),
                    Activity.moving_time > 1800  # >30 minutes
                ).count()
                
                if recent_significant >= 3:
                    logging.info(f"Found {recent_significant} significant activities, updating thresholds")
                    threshold_result = self.recalculate_thresholds(user.user_id)
                    result["threshold_updated"] = threshold_result.get("significant_change", False)
                
                results.append(result)
                
            except Exception as e:
                logging.error(f"Error in daily sync for user {user.user_id}: {e}")
                results.append({"user_id": user.user_id, "error": str(e)})
        
        return {
            "message": f"Daily sync complete for {len(users)} users",
            "results": results
        }


def main():
    parser = argparse.ArgumentParser(description='TrainingLoad Background Processor with APScheduler')
    parser.add_argument('--start-scheduler', action='store_true', 
                      help='Start the background scheduler daemon')
    parser.add_argument('--mode', 
                      choices=['full_import', 'daily_sync', 'threshold_update', 'utl_recalc'],
                      help='One-time processing mode')
    parser.add_argument('--user_id', type=int, help='User ID for user-specific operations')
    parser.add_argument('--days', type=int, default=730, help='Days to look back for full import')
    parser.add_argument('--list-jobs', action='store_true',
                      help='List currently scheduled jobs')
    parser.add_argument('--stop-scheduler', action='store_true',
                      help='Stop the background scheduler')
    
    args = parser.parse_args()
    
    if args.start_scheduler:
        # Start the background scheduler daemon
        start_scheduler_daemon()
        return
    
    if args.list_jobs:
        # Show scheduled jobs status
        global scheduler
        if not scheduler:
            scheduler = setup_scheduler()
        
        try:
            scheduler.start()
            jobs = scheduler.get_jobs()
            
            print(f"📋 Scheduled Jobs ({len(jobs)}):")
            if jobs:
                for job in jobs:
                    next_run = job.next_run_time or "Not scheduled"
                    print(f"  • {job.name} (ID: {job.id})")
                    print(f"    Next run: {next_run}")
                    print()
            else:
                print("  No jobs currently scheduled")
                print("  Run with --start-scheduler to setup default jobs")
            
        except Exception as e:
            print(f"Error accessing scheduler: {e}")
        finally:
            if scheduler and scheduler.running:
                scheduler.shutdown(wait=False)
        return
    
    if args.stop_scheduler:
        print("To stop the scheduler, use Ctrl+C or send SIGTERM to the running process")
        print("You can also check for running processes with: ps aux | grep background_processor")
        return
    
    if not args.mode:
        parser.print_help()
        print("\nExamples:")
        print("  python background_processor.py --start-scheduler")
        print("  python background_processor.py --mode=full_import --user_id=1")
        print("  python background_processor.py --list-jobs")
        return
    
    # One-time operations
    processor = BackgroundProcessor()
    
    try:
        if args.mode == 'full_import':
            if not args.user_id:
                print("--user_id required for full_import mode")
                return
            result = processor.full_historical_import(args.user_id, args.days)
            
        elif args.mode == 'daily_sync':
            result = processor.daily_sync()
            
        elif args.mode == 'threshold_update':
            if not args.user_id:
                print("--user_id required for threshold_update mode")
                return
            result = processor.recalculate_thresholds(args.user_id)
            
        elif args.mode == 'utl_recalc':
            if not args.user_id:
                print("--user_id required for utl_recalc mode")
                return
            result = processor.recalculate_utl_scores(args.user_id)
        
        print(f"Result: {result}")
        logging.info(f"Operation {args.mode} completed: {result}")
        
    except Exception as e:
        error_msg = f"Error in {args.mode}: {str(e)}"
        print(error_msg)
        logging.error(error_msg)


if __name__ == "__main__":
    main()
