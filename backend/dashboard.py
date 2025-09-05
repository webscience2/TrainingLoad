# Dashboard endpoints for user analytics and metrics
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import logging
from models import User, Activity, Threshold, WellnessData
from config import get_db

router = APIRouter()

class UTLMethodExplanation(BaseModel):
    method: str
    name: str
    description: str
    accuracy: str
    typical_range: str
    best_for: str

@router.get("/utl-methods")
def get_utl_method_explanations():
    """
    Explain the different UTL calculation methods to help users understand their scores.
    """
    methods = [
        {
            "method": "TSS",
            "name": "Training Stress Score",
            "description": "Power-based calculation using your Functional Threshold Power (FTP). Most accurate for cycling with power meters.",
            "accuracy": "Very High",
            "typical_range": "50-300 (50=easy 1hr, 100=1hr at FTP, 200+=very hard/long)",
            "best_for": "Cycling activities with power data"
        },
        {
            "method": "rTSS", 
            "name": "Running Training Stress Score",
            "description": "Pace-based calculation using your Functional Threshold Pace (FThP). Accurate for running activities.",
            "accuracy": "High",
            "typical_range": "40-250 (similar to TSS but pace-based)",
            "best_for": "Running activities with GPS pace data"
        },
        {
            "method": "TRIMP",
            "name": "Training Impulse",
            "description": "Heart rate-based calculation. Uses your max and resting HR to estimate training stress. Scaled by activity type - hiking/walking get lower scores than running at the same HR because they're less demanding.",
            "accuracy": "Medium-High",
            "typical_range": "20-150 (varies by activity type and duration)",
            "best_for": "Activities with heart rate data but no power/pace (hiking, swimming, etc.)"
        },
        {
            "method": "conservative_time_based",
            "name": "Duration-Based Estimate", 
            "description": "Fallback method using activity duration and type when no detailed data is available. Conservative to avoid overestimating stress.",
            "accuracy": "Low-Medium",
            "typical_range": "30-120 (based on duration and activity intensity factors)",
            "best_for": "Activities without detailed heart rate, power, or pace data"
        }
    ]
    
    return {
        "methods": methods,
        "explanation": "UTL scores help normalize training stress across different activities. A hiking TRIMP of 60 represents different physiological stress than a running TSS of 60, but both indicate moderate training load relative to that activity type.",
        "wellness_modifiers": "When available, wellness data (HRV, sleep quality, readiness) can modify your UTL score by ±20% to reflect your body's ability to handle stress on that day."
    }

class ActivitySummary(BaseModel):
    total_activities: int
    total_distance: float
    total_moving_time: int
    total_elevation_gain: float
    avg_pace: float
    recent_activities: List[dict]

class TrainingTotals(BaseModel):
    this_week: dict
    this_month: dict
    this_year: dict

class DashboardData(BaseModel):
    user: dict
    thresholds: dict
    activity_summary: ActivitySummary
    training_totals: TrainingTotals
    recent_activities: List[dict]
    wellness_data: Optional[List[dict]] = None

@router.get("/{user_id}", response_model=DashboardData)
def get_dashboard_data(user_id: int, db: Session = Depends(get_db)):
    # Get user info
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if user has completed onboarding
    # A user needs both activities and thresholds to be considered "onboarded"
    activity_count = db.query(Activity).filter_by(user_id=user_id).count()
    threshold = db.query(Threshold).filter_by(user_id=user_id).first()
    
    if activity_count == 0 or not threshold:
        logging.info(f"🔍 BACKEND DEBUG: User {user_id} needs onboarding - activities: {activity_count}, thresholds: {'exists' if threshold else 'none'}")
        raise HTTPException(status_code=400, detail="User has not completed onboarding")
    
    logging.info(f"🔍 BACKEND DEBUG: User {user_id} has completed onboarding - returning dashboard data")

    # Get thresholds
    thresholds_data = {
        "ftp_watts": threshold.ftp_watts if threshold else None,
        "fthp_mps": threshold.fthp_mps if threshold else None,
        "max_hr": threshold.max_hr if threshold else None,
        "resting_hr": threshold.resting_hr if threshold else None,
        "date_updated": threshold.date_updated.isoformat() if threshold and threshold.date_updated else None
    }

    # Get recent activities (last 10) - handle missing columns gracefully
    try:
        # Use a more specific query to avoid issues with missing columns
        recent_activities_query = db.query(
            Activity.activity_id,
            Activity.name,
            Activity.type,
            Activity.distance,
            Activity.moving_time,
            Activity.start_date,
            Activity.average_speed,
            Activity.data,
            Activity.utl_score,
            Activity.calculation_method
        ).filter_by(user_id=user_id).order_by(Activity.start_date.desc()).limit(10)
        recent_activities = recent_activities_query.all()
        recent_activities_data = []
        for act in recent_activities:
            activity_data = {
                "id": act.activity_id,
                "name": act.name,
                "type": act.type,
                "distance": act.distance,
                "moving_time": act.moving_time,
                "start_date": act.start_date.isoformat() if act.start_date else None,
                "average_speed": act.average_speed,
                "utl_score": act.utl_score,
                "calculation_method": act.calculation_method
            }
            recent_activities_data.append(activity_data)
    except Exception as e:
        # If there's an issue with the Activity model, return empty list
        recent_activities_data = []
        logging.warning(f"Could not fetch activities: {e}")

    # Calculate activity summary
    try:
        # Use specific column selection to avoid missing column issues
        activities_query = db.query(
            Activity.distance,
            Activity.moving_time,
            Activity.total_elevation_gain,
            Activity.start_date
        ).filter_by(user_id=user_id)
        activities = activities_query.all()
        total_activities = len(activities)
        total_distance = sum(act.distance or 0 for act in activities)
        total_moving_time = sum(act.moving_time or 0 for act in activities)
        total_elevation_gain = sum(act.total_elevation_gain or 0 for act in activities)

        # Calculate average pace (min/km)
        avg_pace = 0
        if total_distance > 0 and total_moving_time > 0:
            avg_pace = (total_moving_time / 60) / (total_distance / 1000)
    except Exception as e:
        # If there's an issue with activities, use default values
        total_activities = 0
        total_distance = 0
        total_moving_time = 0
        total_elevation_gain = 0
        avg_pace = 0
        activities = []
        logging.warning(f"Could not calculate activity summary: {e}")

    activity_summary = ActivitySummary(
        total_activities=total_activities,
        total_distance=round(total_distance, 2),
        total_moving_time=total_moving_time,
        total_elevation_gain=round(total_elevation_gain, 2),
        avg_pace=round(avg_pace, 2),
        recent_activities=recent_activities_data
    )

    # Calculate training totals for different periods
    now = datetime.now()
    week_start = now - timedelta(days=now.weekday())
    month_start = now.replace(day=1)
    year_start = now.replace(month=1, day=1)

    def calculate_period_totals(start_date):
        try:
            period_activities = [act for act in activities if act.start_date and act.start_date >= start_date]
            return {
                "activities": len(period_activities),
                "distance": round(sum(act.distance or 0 for act in period_activities), 2),
                "moving_time": sum(act.moving_time or 0 for act in period_activities),
                "elevation_gain": round(sum(act.total_elevation_gain or 0 for act in period_activities), 2)
            }
        except Exception as e:
            logging.warning(f"Could not calculate period totals: {e}")
            return {"activities": 0, "distance": 0, "moving_time": 0, "elevation_gain": 0}

    training_totals = TrainingTotals(
        this_week=calculate_period_totals(week_start),
        this_month=calculate_period_totals(month_start),
        this_year=calculate_period_totals(year_start)
    )

    user_data = {
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "gender": user.gender,
        "weight": user.weight,
        "strava_user_id": user.strava_user_id
    }

    # Get recent wellness data (last 30 days)
    wellness_data = None
    try:
        thirty_days_ago = datetime.now() - timedelta(days=30)
        wellness_records = db.query(WellnessData).filter(
            WellnessData.user_id == user_id,
            WellnessData.date >= thirty_days_ago.date()
        ).order_by(WellnessData.date.desc()).all()
        
        if wellness_records:
            wellness_data = []
            for record in wellness_records:
                wellness_data.append({
                    "date": record.date.isoformat() if record.date else None,
                    "hrv": record.hrv,
                    "resting_hr": record.resting_hr,
                    "sleep_score": record.sleep_score,
                    "readiness_score": record.readiness_score,
                    "sleep_duration": record.sleep_duration,
                    "stress_score": record.stress_score,
                    "weight": record.weight,
                    "body_fat": record.body_fat,
                    "hydration": record.hydration,
                    "energy": record.energy,
                    "motivation": record.motivation,
                    "mood": record.mood,
                    "soreness": record.soreness,
                    "fatigue": record.fatigue,
                    "source": record.source
                })
    except Exception as e:
        logging.warning(f"Could not fetch wellness data for user {user_id}: {e}")

    return DashboardData(
        user=user_data,
        thresholds=thresholds_data,
        activity_summary=activity_summary,
        training_totals=training_totals,
        recent_activities=recent_activities_data,
        wellness_data=wellness_data
    )

class ThresholdOverride(BaseModel):
    ftp_watts: Optional[float] = None
    fthp_mps: Optional[float] = None
    max_hr: Optional[int] = None
    resting_hr: Optional[int] = None

@router.put("/{user_id}/thresholds")
def update_user_thresholds(user_id: int, overrides: ThresholdOverride, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    threshold = db.query(Threshold).filter_by(user_id=user_id).first()
    if not threshold:
        threshold = Threshold(user_id=user_id)
        db.add(threshold)

    # Update only provided values
    if overrides.ftp_watts is not None:
        threshold.ftp_watts = overrides.ftp_watts
    if overrides.fthp_mps is not None:
        threshold.fthp_mps = overrides.fthp_mps
    if overrides.max_hr is not None:
        threshold.max_hr = overrides.max_hr
    if overrides.resting_hr is not None:
        threshold.resting_hr = overrides.resting_hr

    threshold.date_updated = datetime.now()
    db.commit()

    return {
        "message": "Thresholds updated successfully",
        "thresholds": {
            "ftp_watts": threshold.ftp_watts,
            "fthp_mps": threshold.fthp_mps,
            "max_hr": threshold.max_hr,
            "resting_hr": threshold.resting_hr,
            "date_updated": threshold.date_updated.isoformat()
        }
    }


@router.post("/{user_id}/recalculate-utl")
def recalculate_utl_with_wellness(user_id: int, db: Session = Depends(get_db)):
    """
    Recalculate UTL scores for existing activities using wellness data.
    This is useful after connecting intervals.icu to apply wellness modifiers retroactively.
    """
    from utils import calculate_utl
    
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    threshold = db.query(Threshold).filter_by(user_id=user_id).first()
    if not threshold:
        raise HTTPException(status_code=400, detail="No thresholds found. Please set up thresholds first.")
    
    # Get activities from the last 90 days
    cutoff_date = datetime.now() - timedelta(days=90)
    activities = db.query(Activity).filter(
        Activity.user_id == user_id,
        Activity.start_date >= cutoff_date
    ).all()
    
    updated_count = 0
    wellness_applied_count = 0
    
    for activity in activities:
        try:
            # Get wellness data for this activity's date
            activity_date = activity.start_date.date() if activity.start_date else None
            wellness_data = None
            
            if activity_date:
                wellness_entry = db.query(WellnessData).filter(
                    WellnessData.user_id == user_id,
                    WellnessData.date == activity_date
                ).first()
                
                if wellness_entry:
                    wellness_data = {
                        'hrv': wellness_entry.hrv,
                        'sleepScore': wellness_entry.sleep_score,
                        'readiness': wellness_entry.readiness_score,  # Fixed: use readiness_score
                        'restingHR': wellness_entry.resting_hr
                    }
                    wellness_applied_count += 1
            
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
            
            # Recalculate UTL
            new_utl, new_method = calculate_utl(activity_summary, threshold, activity_streams, wellness_data)
            
            # Update if the score or method changed
            if activity.utl_score != new_utl or activity.calculation_method != new_method:
                old_utl = activity.utl_score
                activity.utl_score = new_utl
                activity.calculation_method = new_method
                updated_count += 1
                
                logging.info(f"Updated activity {activity.strava_activity_id}: UTL {old_utl:.2f} -> {new_utl:.2f} ({new_method})")
        
        except Exception as e:
            logging.error(f"Error recalculating UTL for activity {activity.strava_activity_id}: {str(e)}")
            continue
    
    db.commit()
    
    return {
        "message": f"Recalculated UTL for {len(activities)} activities",
        "updated_count": updated_count,
        "wellness_applied_count": wellness_applied_count,
        "details": f"{wellness_applied_count} activities had wellness data applied as modifiers"
    }


def recalculate_utl_with_wellness_internal(user_id: int, db: Session):
    """
    Internal function to recalculate UTL scores with wellness data.
    Used for automatic recalculation when wellness data is synced.
    """
    from utils import calculate_utl
    
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        return {"error": "User not found"}
    
    threshold = db.query(Threshold).filter_by(user_id=user_id).first()
    if not threshold:
        return {"error": "No thresholds found"}
    
    # Get activities from the last 90 days
    cutoff_date = datetime.now() - timedelta(days=90)
    activities = db.query(Activity).filter(
        Activity.user_id == user_id,
        Activity.start_date >= cutoff_date
    ).all()
    
    updated_count = 0
    wellness_applied_count = 0
    
    for activity in activities:
        try:
            # Get wellness data for this activity's date
            activity_date = activity.start_date.date() if activity.start_date else None
            wellness_data = None
            
            if activity_date:
                wellness_entry = db.query(WellnessData).filter(
                    WellnessData.user_id == user_id,
                    WellnessData.date == activity_date
                ).first()
                
                if wellness_entry:
                    wellness_data = {
                        'hrv': wellness_entry.hrv,
                        'sleepScore': wellness_entry.sleep_score,
                        'readiness': wellness_entry.readiness_score,  # Fixed: use readiness_score
                        'restingHR': wellness_entry.resting_hr
                    }
                    wellness_applied_count += 1
            
            # Only recalculate if we have wellness data for this date
            if wellness_data:
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
                
                # Recalculate UTL with wellness data
                new_utl, new_method = calculate_utl(activity_summary, threshold, activity_streams, wellness_data)
                
                # Update if the score changed significantly (more than 1% or method changed)
                if abs(activity.utl_score - new_utl) > 0.01 * activity.utl_score or activity.calculation_method != new_method:
                    old_utl = activity.utl_score
                    activity.utl_score = new_utl
                    activity.calculation_method = new_method
                    updated_count += 1
                    
                    logging.info(f"Auto-updated activity {activity.strava_activity_id}: UTL {old_utl:.2f} -> {new_utl:.2f} ({new_method})")
        
        except Exception as e:
            logging.error(f"Error auto-recalculating UTL for activity {activity.strava_activity_id}: {str(e)}")
            continue
    
    if updated_count > 0:
        db.commit()
    
    return {
        "message": f"Auto-recalculated UTL for {len(activities)} activities",
        "updated_count": updated_count,
        "wellness_applied_count": wellness_applied_count,
        "details": f"{wellness_applied_count} activities had wellness data, {updated_count} were updated"
    }


@router.post("/{user_id}/fix-null-utl")
def fix_null_utl_scores(user_id: int, db: Session = Depends(get_db)):
    """
    Fix activities that have null UTL scores by recalculating them.
    This can happen when activities are imported before thresholds are established.
    """
    from utils import calculate_utl
    
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    threshold = db.query(Threshold).filter_by(user_id=user_id).first()
    if not threshold:
        raise HTTPException(status_code=400, detail="No thresholds found. Please set up thresholds first.")
    
    # Get activities with null UTL scores
    activities = db.query(Activity).filter(
        Activity.user_id == user_id,
        Activity.utl_score.is_(None)
    ).all()
    
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
            
            # Calculate UTL
            utl_score, method = calculate_utl(activity_summary, threshold, activity_streams)
            
            # Update the activity
            activity.utl_score = float(utl_score)
            activity.calculation_method = method
            updated_count += 1
            
            logging.info(f"Fixed null UTL for activity {activity.strava_activity_id}: {utl_score:.2f} using {method}")
            
        except Exception as e:
            logging.error(f"Error fixing UTL for activity {activity.strava_activity_id}: {str(e)}")
            continue
    
    db.commit()
    
    return {
        "message": f"Fixed null UTL scores for {updated_count} activities",
        "activities_checked": len(activities),
        "activities_updated": updated_count
    }
