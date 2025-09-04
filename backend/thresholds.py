# Threshold estimation and management endpoints
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging
from models import User, Threshold, Activity, WellnessData
from utils import estimate_thresholds_from_activities
from config import get_db

router = APIRouter()

def get_best_resting_hr_from_wellness(user_id: int, db: Session, days: int = 30) -> int:
    """Get the best (lowest valid) resting HR from recent wellness data"""
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        wellness_entries = db.query(WellnessData).filter(
            WellnessData.user_id == user_id,
            WellnessData.date >= cutoff_date.date(),
            WellnessData.resting_hr.isnot(None),
            WellnessData.resting_hr >= 35,  # Reasonable minimum
            WellnessData.resting_hr <= 100  # Reasonable maximum
        ).order_by(WellnessData.resting_hr.asc()).all()
        
        if wellness_entries:
            # Return the 10th percentile (very low but not anomalous)
            sorted_hrs = [w.resting_hr for w in wellness_entries]
            percentile_10_index = max(0, int(len(sorted_hrs) * 0.1))
            best_resting_hr = sorted_hrs[percentile_10_index]
            logging.info(f"Found best resting HR from wellness data: {best_resting_hr} bpm (from {len(sorted_hrs)} entries)")
            return best_resting_hr
        
        return None
        
    except Exception as e:
        logging.error(f"Error getting resting HR from wellness data: {str(e)}")
        return None

class ThresholdUpdate(BaseModel):
    user_id: int
    ftp_watts: float = None
    fthp_mps: float = None
    max_hr: int = None
    resting_hr: int = None
    estimate_from_activities: bool = False
    preserve_user_resting_hr: bool = True  # Don't overwrite user-provided resting HR

@router.post("/update_thresholds")
def update_thresholds(threshold_data: ThresholdUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(user_id=threshold_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    threshold = db.query(Threshold).filter_by(user_id=threshold_data.user_id).first()
    if not threshold:
        threshold = Threshold(user_id=threshold_data.user_id)
        db.add(threshold)

    if threshold_data.estimate_from_activities:
        # Get activities from last 3 months
        three_months_ago = datetime.now() - timedelta(days=90)
        activities = db.query(Activity).filter(
            Activity.user_id == threshold_data.user_id,
            Activity.start_date >= three_months_ago
        ).all()

        # Extract activity data for estimation including streams
        activity_data = []
        for act in activities:
            activity_data.append({
                'type': act.type,
                'moving_time': act.moving_time,
                'average_speed': act.average_speed,
                'average_watts': act.data.get('average_watts') if act.data else None,
                'max_heartrate': act.data.get('max_heartrate') if act.data else None,
                'streams': act.data.get('streams', {}) if act.data else {}
            })

        estimates = estimate_thresholds_from_activities(activity_data, user.gender)
        if estimates:
            threshold.ftp_watts = estimates['ftp_watts'] or threshold.ftp_watts
            threshold.fthp_mps = estimates['fthp_mps'] or threshold.fthp_mps
            threshold.max_hr = estimates['max_hr'] or threshold.max_hr
            
            # Enhanced resting HR logic using wellness data
            if threshold_data.preserve_user_resting_hr and threshold.resting_hr:
                # Keep existing user-provided resting HR
                logging.info(f"Preserving user-provided resting HR: {threshold.resting_hr}")
            else:
                # Try to get resting HR from intervals.icu wellness data first
                wellness_resting_hr = get_best_resting_hr_from_wellness(threshold_data.user_id, db)
                if wellness_resting_hr:
                    threshold.resting_hr = wellness_resting_hr
                    logging.info(f"Using resting HR from wellness data: {wellness_resting_hr}")
                else:
                    # Fall back to estimated resting HR
                    threshold.resting_hr = estimates['resting_hr'] or threshold.resting_hr
                    logging.info(f"Using estimated resting HR: {threshold.resting_hr}")
                
            logging.info(f"Estimated thresholds for user {threshold_data.user_id}: FTP={threshold.ftp_watts}, FThP={threshold.fthp_mps}, MaxHR={threshold.max_hr}, RestHR={threshold.resting_hr}")

    # Update with provided values (overrides estimates)
    if threshold_data.ftp_watts is not None:
        threshold.ftp_watts = threshold_data.ftp_watts
    if threshold_data.fthp_mps is not None:
        threshold.fthp_mps = threshold_data.fthp_mps
    if threshold_data.max_hr is not None:
        threshold.max_hr = threshold_data.max_hr
    if threshold_data.resting_hr is not None:
        threshold.resting_hr = threshold_data.resting_hr

    threshold.date_updated = datetime.now()
    db.commit()

    return {
        "message": "Thresholds updated successfully.",
        "thresholds": {
            "ftp_watts": threshold.ftp_watts,
            "fthp_mps": threshold.fthp_mps,
            "max_hr": threshold.max_hr,
            "resting_hr": threshold.resting_hr
        }
    }
