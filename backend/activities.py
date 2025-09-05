# Activity import and management endpoints
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import requests
import time
import logging
from models import User, Activity, Threshold
from utils import calculate_utl
from config import get_db, SessionLocal
from research_threshold_calculator import update_thresholds_from_activity_streams

router = APIRouter()

class ActivityImportRequest(BaseModel):
    user_id: int

def _fetch_and_process_activities(user_id: int, db: Session, backfill_days: int = 90):
    """
    Fetches activities for a user from Strava, calculates UTL, and stores them.
    - PRD specifies Garmin API, but current implementation uses Strava. This should be reconciled.
    - Fetches activity streams for accurate UTL calculation.
    """
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user or not user.strava_oauth_token:
        logging.warning(f"No Strava token for user {user_id}")
        return

    threshold = db.query(Threshold).filter_by(user_id=user_id).first()
    access_token = user.strava_oauth_token
    headers = {"Authorization": f"Bearer {access_token}"}
    
    activities_url = "https://www.strava.com/api/v3/athlete/activities"
    per_page = 200
    after_timestamp = int(time.time()) - backfill_days * 24 * 60 * 60
    page = 1
    total_imported = 0

    while True:
        params = {"per_page": per_page, "page": page, "after": after_timestamp}
        try:
            resp = requests.get(activities_url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(f"Strava API error fetching activities for user {user_id}: {e}")
            break

        activities = resp.json()
        if not activities:
            break

        for act_summary in activities:
            strava_id = str(act_summary["id"])
            if db.query(Activity).filter_by(strava_activity_id=strava_id).first():
                logging.info(f"Skipping duplicate activity {strava_id} for user {user_id}")
                continue

            # Fetch activity stream for detailed data
            stream_url = f"https://www.strava.com/api/v3/activities/{strava_id}/streams"
            stream_params = {"keys": "time,latlng,distance,altitude,velocity_smooth,heartrate,cadence,watts", "key_by_type": True}
            try:
                stream_resp = requests.get(stream_url, headers=headers, params=stream_params, timeout=15)
                stream_resp.raise_for_status()
                activity_streams = stream_resp.json()
            except requests.exceptions.RequestException as e:
                logging.warning(f"Could not fetch streams for activity {strava_id} for user {user_id}: {e}. UTL calculation may be less accurate.")
                activity_streams = None

            activity = Activity(
                strava_activity_id=strava_id,
                user_id=user.user_id,
                name=act_summary.get("name"),
                type=act_summary.get("type"),
                distance=act_summary.get("distance"),
                moving_time=act_summary.get("moving_time"),
                elapsed_time=act_summary.get("elapsed_time"),
                start_date=act_summary.get("start_date"),
                average_speed=act_summary.get("average_speed"),
                max_speed=act_summary.get("max_speed"),
                total_elevation_gain=act_summary.get("total_elevation_gain"),
                data={
                    **act_summary,  # Store all summary data
                    "streams": activity_streams  # Add streams data
                }
            )

            if threshold:
                # Get wellness data for the activity date (if available)
                activity_date = act_summary.get("start_date")
                wellness_data = None
                if activity_date:
                    try:
                        from datetime import datetime
                        from models import WellnessData
                        # Parse the activity date
                        if isinstance(activity_date, str):
                            activity_dt = datetime.fromisoformat(activity_date.replace('Z', '+00:00'))
                        else:
                            activity_dt = activity_date
                        
                        # Look for wellness data on the same date
                        wellness_entry = db.query(WellnessData).filter(
                            WellnessData.user_id == user_id,
                            WellnessData.date == activity_dt.date()
                        ).first()
                        
                        if wellness_entry:
                            wellness_data = {
                                'hrv': wellness_entry.hrv,
                                'sleepScore': wellness_entry.sleep_score,
                                'readiness': wellness_entry.readiness_score,  # Fixed: use readiness_score
                                'restingHR': wellness_entry.resting_hr
                            }
                    except Exception as e:
                        logging.warning(f"Could not fetch wellness data for activity {strava_id}: {e}")
                
                # Pass summary, stream data, and wellness data to UTL calculation
                utl_score, method = calculate_utl(act_summary, threshold, activity_streams, wellness_data)
                activity.utl_score = float(utl_score)  # Ensure it's a Python float, not numpy
                activity.calculation_method = method
                
                wellness_info = " (with wellness data)" if wellness_data else ""
                logging.info(f"Calculated UTL {utl_score:.2f} using {method} for activity {strava_id}{wellness_info}")
            else:
                logging.warning(f"No threshold data for user {user_id}, skipping UTL calculation for activity {strava_id}")

            db.add(activity)
            total_imported += 1
            
            # Analyze streams for threshold updates if this is a significant activity
            if activity_streams and (act_summary.get("type") in ["Ride", "VirtualRide", "Run", "VirtualRun"]):
                try:
                    threshold_analysis = update_thresholds_from_activity_streams(
                        strava_id, user_id
                    )
                    if threshold_analysis.get('thresholds_updated'):
                        logging.info(f"Updated thresholds from activity {strava_id}: {threshold_analysis}")
                except Exception as e:
                    logging.warning(f"Could not analyze thresholds for activity {strava_id}: {e}")
            
            logging.info(f"Imported activity {strava_id}: {act_summary.get('name')} for user {user_id}")

        db.commit()
        if len(activities) < per_page:
            break
        page += 1

    logging.info(f"Imported {total_imported} new Strava activities for user {user_id}")

@router.post("/import_activities")
def import_activities(request: ActivityImportRequest, background_tasks: BackgroundTasks):
    """API endpoint to trigger a background import of a user's Strava activities."""
    def import_task():
        db = SessionLocal()
        try:
            _fetch_and_process_activities(request.user_id, db)
        finally:
            db.close()
            
    background_tasks.add_task(import_task)
    return {"message": "Activity import started in background."}

def sync_strava_activities():
    """Background job to sync activities for all users."""
    logging.info("Starting scheduled Strava activity sync for all users.")
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.strava_oauth_token.isnot(None)).all()
        for user in users:
            logging.info(f"Checking for new activities for user {user.user_id}")
            # Sync last 7 days for existing users
            _fetch_and_process_activities(user.user_id, db, backfill_days=7)
    finally:
        db.close()
    logging.info("Finished scheduled Strava activity sync.")

@router.get("/count/{user_id}")
def get_activity_count(user_id: int, db: Session = Depends(get_db)):
    """Get the count of activities for a user"""
    try:
        logging.info(f"Getting activity count for user {user_id}")
        count = db.query(Activity).filter_by(user_id=user_id).count()
        logging.info(f"Found {count} activities for user {user_id}")
        return {"activity_count": count}
    except Exception as e:
        logging.error(f"Error getting activity count for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching activity count")
