# Onboarding related endpoints
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging
from models import User, Threshold, Activity
from utils import estimate_thresholds_from_activities
from research_threshold_calculator import ResearchBasedThresholdCalculator, calculate_initial_thresholds_for_new_user
from config import get_db

router = APIRouter()

class OnboardingQuestionnaire(BaseModel):
    user_id: int
    name: str = None
    email: str = None  # User's real email address
    dob: str = None  # ISO date string
    demographics: dict = None  # e.g. {"gender": "male", "weight": "70kg"}
    injury_history: dict = None  # e.g. {"knee": True, "ankle": False}

@router.post("/")
def onboarding(questionnaire: OnboardingQuestionnaire, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(user_id=questionnaire.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Store name and dob
    if questionnaire.name:
        user.name = questionnaire.name
    if questionnaire.email:
        # Update user's email with their real email address
        logging.info(f"Updating user {questionnaire.user_id} email from {user.email} to {questionnaire.email}")
        user.email = questionnaire.email
    if questionnaire.dob:
        try:
            user.dob = datetime.fromisoformat(questionnaire.dob)
        except Exception:
            pass

    # Store demographics
    if questionnaire.demographics:
        if "gender" in questionnaire.demographics:
            user.gender = questionnaire.demographics["gender"]
        if "weight" in questionnaire.demographics:
            user.weight = questionnaire.demographics["weight"]

    # Store injury history
    if questionnaire.injury_history:
        user.injury_history_flags = questionnaire.injury_history

    # For new users completing onboarding, import activities and calculate thresholds
    logging.info(f"Starting activity import and threshold calculation for user {questionnaire.user_id}")
    
    try:
        # Import activities from Strava
        from activities import _fetch_and_process_activities
        logging.info(f"Importing activities for user {questionnaire.user_id}")
        _fetch_and_process_activities(questionnaire.user_id, db, backfill_days=90)
        
        # Now get the imported activities for threshold calculation
        three_months_ago = datetime.now() - timedelta(days=90)
        activities = db.query(Activity).filter(
            Activity.user_id == questionnaire.user_id,
            Activity.start_date >= three_months_ago
        ).all()
        
        logging.info(f"Found {len(activities)} activities for threshold calculation")
        
    except Exception as e:
        logging.error(f"Error importing activities for user {questionnaire.user_id}: {e}")
        activities = []

    # Estimate thresholds from recent activities
    if activities:
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
            
            # Check if activity has streams data
            if act.data and 'streams' in act.data and act.data['streams']:
                activities_with_streams.append((activity_summary, act.data['streams']))

        # Use research-based threshold calculation for new users
        try:
            estimates = calculate_initial_thresholds_for_new_user(user.user_id)
            logging.info(f"Using research-based threshold estimation for new user {questionnaire.user_id}: {estimates}")
        except Exception as e:
            logging.warning(f"Research-based threshold calculation failed, falling back to basic estimation: {e}")
            # Fallback to original method
            estimates = estimate_thresholds_from_activities(activity_data, user.gender, activities_with_streams)
        
        if estimates:
            threshold = db.query(Threshold).filter_by(user_id=questionnaire.user_id).first()
            if not threshold:
                threshold = Threshold(user_id=questionnaire.user_id)
                db.add(threshold)

            threshold.ftp_watts = estimates.get('ftp_watts')
            threshold.fthp_mps = estimates.get('fthp_mps')
            threshold.max_hr = estimates.get('max_hr')
            threshold.resting_hr = estimates.get('resting_hr')
            threshold.date_updated = datetime.now()

            logging.info(f"Set research-based thresholds during onboarding for user {questionnaire.user_id}: {estimates}")
            
            # Now recalculate UTL scores for the imported activities using the new thresholds
            logging.info(f"Recalculating UTL scores for {len(activities)} activities with new thresholds")
            from utils import calculate_utl
            
            updated_count = 0
            for activity in activities:
                try:
                    # Reconstruct activity summary for UTL calculation
                    activity_summary = {
                        'type': activity.type,
                        'moving_time': activity.moving_time,
                        'distance': activity.distance,
                        'average_speed': activity.average_speed,
                        'start_date': activity.start_date.isoformat() if activity.start_date else None
                    }
                    
                    # Get streams data from stored data
                    activity_streams = None
                    if activity.data and isinstance(activity.data, dict):
                        activity_streams = activity.data.get('streams')
                    
                    # Calculate UTL with the new thresholds
                    utl_score, method = calculate_utl(activity_summary, threshold, activity_streams)
                    
                    # Update the activity
                    activity.utl_score = float(utl_score)
                    activity.calculation_method = method
                    updated_count += 1
                    
                    logging.info(f"Updated UTL for activity {activity.strava_activity_id}: {utl_score:.2f} using {method}")
                    
                except Exception as e:
                    logging.error(f"Error calculating UTL for activity {activity.strava_activity_id}: {e}")
                    continue
            
            logging.info(f"Updated UTL scores for {updated_count} activities during onboarding")

    db.commit()
    return {"message": "Onboarding questionnaire saved with threshold estimation.", "user_id": user.user_id}
