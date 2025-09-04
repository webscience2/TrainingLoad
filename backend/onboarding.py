# Onboarding related endpoints
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging
from models import User, Threshold, Activity
from utils import estimate_thresholds_from_activities
from config import get_db

router = APIRouter()

class OnboardingQuestionnaire(BaseModel):
    user_id: int
    name: str = None
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

    # Estimate thresholds from recent activities
    three_months_ago = datetime.now() - timedelta(days=90)
    activities = db.query(Activity).filter(
        Activity.user_id == questionnaire.user_id,
        Activity.start_date >= three_months_ago
    ).all()

    if activities:
        activity_data = []
        for act in activities:
            activity_data.append({
                'type': act.type,
                'moving_time': act.moving_time,
                'average_speed': act.average_speed,
                'average_watts': act.data.get('average_watts') if act.data else None,
                'max_heartrate': act.data.get('max_heartrate') if act.data else None
            })

        estimates = estimate_thresholds_from_activities(activity_data, user.gender)
        if estimates:
            threshold = db.query(Threshold).filter_by(user_id=questionnaire.user_id).first()
            if not threshold:
                threshold = Threshold(user_id=questionnaire.user_id)
                db.add(threshold)

            threshold.ftp_watts = estimates['ftp_watts']
            threshold.fthp_mps = estimates['fthp_mps']
            threshold.max_hr = estimates['max_hr']
            threshold.resting_hr = estimates['resting_hr']
            threshold.date_updated = datetime.now()

            logging.info(f"Estimated thresholds during onboarding for user {questionnaire.user_id}: {estimates}")

    db.commit()
    return {"message": "Onboarding questionnaire saved with threshold estimation.", "user_id": user.user_id}
