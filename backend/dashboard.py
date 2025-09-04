# Dashboard endpoints for user analytics and metrics
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional
import logging
from models import User, Activity, Threshold
from config import get_db

router = APIRouter()

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

@router.get("/{user_id}", response_model=DashboardData)
def get_dashboard_data(user_id: int, db: Session = Depends(get_db)):
    # Get user info
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get thresholds
    threshold = db.query(Threshold).filter_by(user_id=user_id).first()
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

    return DashboardData(
        user=user_data,
        thresholds=thresholds_data,
        activity_summary=activity_summary,
        training_totals=training_totals,
        recent_activities=recent_activities_data
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
