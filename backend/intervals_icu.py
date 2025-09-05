# Intervals.icu Integration Module
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from config import get_db
from models import User, WellnessData
import json

router = APIRouter(tags=["intervals"])

# Pydantic models for API requests/responses
class IntervalsConnection(BaseModel):
    user_id: int
    api_key: str
    intervals_user_id: str

class WellnessDataResponse(BaseModel):
    date: str
    hrv: Optional[float]
    resting_hr: Optional[int]
    sleep_score: Optional[float]
    sleep_duration: Optional[float]
    readiness_score: Optional[float]
    stress_score: Optional[float]

class IntervalsICUClient:
    """Client for intervals.icu API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://intervals.icu/api/v1"
        self.session = requests.Session()
        self.session.auth = ('API_KEY', api_key)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'TrainingLoad/1.0'
        })
    
    def test_connection(self, athlete_id: str = None) -> bool:
        """Test if the API key is valid"""
        try:
            # If athlete_id is provided, test with specific athlete endpoint
            if athlete_id:
                response = self.session.get(f"{self.base_url}/athlete/{athlete_id}")
            else:
                # Fallback to a general endpoint that should work
                response = self.session.get(f"{self.base_url}/heartrate")
            
            logging.info(f"intervals.icu API test response: {response.status_code}")
            if response.status_code != 200:
                logging.error(f"intervals.icu API error: {response.text}")
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Error testing intervals.icu connection: {str(e)}")
            return False
    
    def get_athlete_info(self, athlete_id: str = None) -> Optional[Dict]:
        """Get athlete information"""
        try:
            if athlete_id:
                response = self.session.get(f"{self.base_url}/athlete/{athlete_id}")
            else:
                response = self.session.get(f"{self.base_url}/athlete")
            
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"Error getting athlete info: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logging.error(f"Error getting athlete info: {str(e)}")
            return None
    
    def get_wellness_data(self, athlete_id: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Get wellness data (HRV, resting HR, sleep, etc.) for a date range
        """
        try:
            # Format dates for API
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            wellness_data = []
            
            # Get wellness entries - intervals.icu stores this as "wellness" entries
            response = self.session.get(
                f"{self.base_url}/athlete/{athlete_id}/wellness",
                params={
                    'oldest': start_str,
                    'newest': end_str
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                for entry in data:
                    # Parse wellness data from intervals.icu format using correct field names
                    wellness_entry = {
                        'date': entry.get('id'),  # Date is the ID in wellness entries
                        'hrv': entry.get('hrv'),  # HRV field
                        'resting_hr': entry.get('restingHR'),  # Resting heart rate
                        'sleep_score': entry.get('sleepScore'),  # Sleep quality score
                        'sleep_duration': entry.get('sleepSecs', 0) / 3600 if entry.get('sleepSecs') else None,  # Convert seconds to hours
                        'readiness_score': entry.get('readiness'),  # Readiness score
                        'stress_score': entry.get('stress'),  # Stress score
                        'weight': entry.get('weight'),
                        'body_fat': entry.get('bodyFat'),
                        'hydration': entry.get('hydration'),
                        'energy': entry.get('energy'),
                        'motivation': entry.get('motivation'),
                        'mood': entry.get('mood'),
                        'soreness': entry.get('soreness'),
                        'fatigue': entry.get('fatigue'),
                        'spO2': entry.get('spO2'),  # Blood oxygen saturation
                        'respiration': entry.get('respiration')  # Respiration rate
                    }
                    wellness_data.append(wellness_entry)
            
            return wellness_data
            
        except Exception as e:
            logging.error(f"Error getting wellness data from intervals.icu: {str(e)}")
            return []


# API Endpoints
@router.post("/connect")
async def connect_intervals_account(
    connection: IntervalsConnection,
    db: Session = Depends(get_db)
):
    """Connect an intervals.icu account"""
    try:
        # Test the connection
        client = IntervalsICUClient(connection.api_key)
        
        if not client.test_connection(connection.intervals_user_id):
            raise HTTPException(status_code=400, detail="Invalid intervals.icu API key or athlete ID")
        
        # Get athlete info
        athlete_info = client.get_athlete_info(connection.intervals_user_id)
        if not athlete_info:
            raise HTTPException(status_code=400, detail="Could not retrieve athlete information")
        
        # Store the API key securely (in production, encrypt this)
        user = db.query(User).filter(User.user_id == connection.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Store intervals.icu connection info
        if not user.integrations:
            user.integrations = {}
        
        user.integrations['intervals_icu'] = {
            'api_key': connection.api_key,  # In production, encrypt this
            'athlete_id': athlete_info.get('id'),
            'connected_at': datetime.utcnow().isoformat(),
            'athlete_name': athlete_info.get('name')
        }
        
        db.commit()
        
        return {
            "message": "intervals.icu account connected successfully",
            "athlete_name": athlete_info.get('name'),
            "athlete_id": athlete_info.get('id')
        }
        
    except HTTPException as e:
        # Re-raise HTTP exceptions to preserve status codes and details
        raise e
    except Exception as e:
        logging.error(f"Error connecting intervals.icu account: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to connect intervals.icu account")


@router.post("/sync_wellness")
async def sync_wellness_data(
    user_id: int,
    days: int = 365,  # Changed from 30 to 365 to match Strava sync timeframe (12 months)
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Sync wellness data from intervals.icu for the last 12 months (365 days)"""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.integrations or 'intervals_icu' not in user.integrations:
            raise HTTPException(status_code=400, detail="intervals.icu not connected for this user")
        
        # Get the athlete_id from integrations
        intervals_config = user.integrations['intervals_icu']
        athlete_id = intervals_config.get('athlete_id')
        if not athlete_id:
            raise HTTPException(status_code=400, detail="intervals.icu athlete_id not found in user profile")
        
        # Run sync in background
        background_tasks.add_task(
            _sync_wellness_data_task,
            user_id,
            intervals_config['api_key'],
            athlete_id,
            days,
            db
        )
        
        return {"message": f"Wellness data sync started for last {days} days"}
        
    except Exception as e:
        logging.error(f"Error starting wellness sync: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start wellness data sync")


def _sync_wellness_data_task(user_id: int, api_key: str, athlete_id: str, days: int, db: Session):
    """Background task to sync wellness data"""
    try:
        client = IntervalsICUClient(api_key)
        
        # Get date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get wellness data from intervals.icu
        wellness_data = client.get_wellness_data(athlete_id, start_date, end_date)
        
        # Store in database
        for entry in wellness_data:
            if not entry['date']:
                continue
                
            # Check if entry already exists
            existing = db.query(WellnessData).filter(
                WellnessData.user_id == user_id,
                WellnessData.date == entry['date']
            ).first()
            
            if existing:
                # Update existing entry
                for key, value in entry.items():
                    if key != 'date' and value is not None:
                        setattr(existing, key, value)
            else:
                # Create new entry
                wellness_entry = WellnessData(
                    user_id=user_id,
                    date=entry['date'],
                    hrv=entry.get('hrv'),
                    resting_hr=entry.get('resting_hr'),
                    sleep_score=entry.get('sleep_score'),
                    sleep_duration=entry.get('sleep_duration'),
                    readiness_score=entry.get('readiness_score'),
                    stress_score=entry.get('stress_score'),
                    weight=entry.get('weight'),
                    body_fat=entry.get('body_fat'),
                    hydration=entry.get('hydration'),
                    energy=entry.get('energy'),
                    motivation=entry.get('motivation'),
                    mood=entry.get('mood'),
                    soreness=entry.get('soreness'),
                    fatigue=entry.get('fatigue'),
                    source='intervals_icu'
                )
                db.add(wellness_entry)
        
        db.commit()
        logging.info(f"Successfully synced {len(wellness_data)} wellness entries for user {user_id}")
        
        # Automatically recalculate UTL scores with new wellness data
        if len(wellness_data) > 0:
            try:
                logging.info(f"Auto-recalculating UTL scores with wellness data for user {user_id}")
                from dashboard import recalculate_utl_with_wellness_internal
                result = recalculate_utl_with_wellness_internal(user_id, db)
                logging.info(f"Auto-recalculation complete: {result.get('message', 'Unknown result')}")
                
                # Update resting HR threshold from recent wellness data
                updated_resting_hr = update_resting_hr_from_wellness(user_id, db)
                if updated_resting_hr:
                    logging.info(f"Updated resting HR threshold for user {user_id}: {updated_resting_hr} bpm")
                    
            except Exception as recalc_error:
                logging.error(f"Error during auto UTL recalculation for user {user_id}: {str(recalc_error)}")
        
    except Exception as e:
        logging.error(f"Error syncing wellness data: {str(e)}")
        db.rollback()


def update_resting_hr_from_wellness(user_id: int, db: Session, lookback_days: int = 14) -> Optional[int]:
    """
    Calculate average resting HR from recent wellness data and update thresholds.
    
    Args:
        user_id: User ID to update
        db: Database session
        lookback_days: Number of recent days to analyze (default: 14 days)
    
    Returns:
        Updated resting HR value or None if no update made
    """
    try:
        from datetime import datetime, timedelta
        from models import WellnessData, Threshold
        
        # Get recent wellness data with resting HR
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        recent_wellness = db.query(WellnessData).filter(
            WellnessData.user_id == user_id,
            WellnessData.date >= cutoff_date,
            WellnessData.resting_hr.isnot(None),
            WellnessData.resting_hr > 30,  # Sanity check
            WellnessData.resting_hr < 120   # Sanity check
        ).order_by(WellnessData.date.desc()).all()
        
        if len(recent_wellness) < 3:  # Need at least 3 data points
            logging.debug(f"Insufficient wellness data for resting HR update (user {user_id}): {len(recent_wellness)} points")
            return None
        
        # Calculate average resting HR
        resting_hrs = [w.resting_hr for w in recent_wellness]
        avg_resting_hr = sum(resting_hrs) / len(resting_hrs)
        rounded_resting_hr = round(avg_resting_hr)
        
        logging.info(f"Calculated avg resting HR for user {user_id}: {avg_resting_hr:.1f} bpm from {len(resting_hrs)} measurements")
        
        # Get or create threshold record
        threshold = db.query(Threshold).filter_by(user_id=user_id).first()
        if not threshold:
            # Create new threshold record
            threshold = Threshold(user_id=user_id)
            db.add(threshold)
        
        # Check if this is a significant change (>5 bpm difference)
        old_resting_hr = threshold.resting_hr
        if old_resting_hr and abs(rounded_resting_hr - old_resting_hr) < 5:
            logging.debug(f"Resting HR change too small to update (user {user_id}): {old_resting_hr} -> {rounded_resting_hr}")
            return None
        
        # Update resting HR
        threshold.resting_hr = rounded_resting_hr
        threshold.date_updated = datetime.now()
        
        db.commit()
        
        logging.info(f"Updated resting HR threshold for user {user_id}: {old_resting_hr} -> {rounded_resting_hr} bpm")
        
        return rounded_resting_hr
        
    except Exception as e:
        logging.error(f"Error updating resting HR from wellness data: {str(e)}")
        db.rollback()
        return None


@router.post("/update_resting_hr/{user_id}")
async def update_resting_hr_endpoint(
    user_id: int,
    lookback_days: int = 14,
    db: Session = Depends(get_db)
):
    """
    Manually update resting HR threshold from recent wellness data.
    
    Args:
        user_id: User ID to update
        lookback_days: Number of recent days to analyze (default: 14)
    """
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        updated_rhr = update_resting_hr_from_wellness(user_id, db, lookback_days)
        
        if updated_rhr:
            return {
                "message": f"Resting HR updated to {updated_rhr} bpm from last {lookback_days} days of wellness data",
                "resting_hr": updated_rhr,
                "lookback_days": lookback_days
            }
        else:
            return {
                "message": "No resting HR update made - insufficient data or change too small",
                "resting_hr": None,
                "lookback_days": lookback_days
            }
        
    except Exception as e:
        logging.error(f"Error in resting HR update endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update resting HR: {str(e)}")


@router.get("/wellness/{user_id}")
async def get_wellness_data_endpoint(
    user_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get wellness data for a user"""
    try:
        # Get date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query wellness data from database
        wellness_data = db.query(WellnessData).filter(
            WellnessData.user_id == user_id,
            WellnessData.date >= start_date.date(),
            WellnessData.date <= end_date.date()
        ).order_by(WellnessData.date.desc()).all()
        
        # Convert to response format
        result = []
        for entry in wellness_data:
            result.append({
                'date': entry.date.isoformat(),
                'hrv': entry.hrv,
                'resting_hr': entry.resting_hr,
                'sleep_score': entry.sleep_score,
                'sleep_duration': entry.sleep_duration,
                'readiness_score': entry.readiness_score,
                'stress_score': entry.stress_score,
                'weight': entry.weight,
                'body_fat': entry.body_fat,
                'hydration': entry.hydration,
                'energy': entry.energy,
                'motivation': entry.motivation,
                'mood': entry.mood,
                'soreness': entry.soreness,
                'fatigue': entry.fatigue,
                'source': entry.source
            })
        
        return {
            "wellness_data": result,
            "count": len(result)
        }
        
    except Exception as e:
        logging.error(f"Error getting wellness data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get wellness data")


@router.get("/connection_status/{user_id}")
async def get_connection_status(user_id: int, db: Session = Depends(get_db)):
    """Get intervals.icu connection status for a user"""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.integrations or 'intervals_icu' not in user.integrations:
            return {"connected": False}
        
        intervals_config = user.integrations['intervals_icu']
        return {
            "connected": True,
            "athlete_name": intervals_config.get('athlete_name'),
            "athlete_id": intervals_config.get('athlete_id'),
            "connected_at": intervals_config.get('connected_at')
        }
        
    except Exception as e:
        logging.error(f"Error getting connection status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get connection status")
