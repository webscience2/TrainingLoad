#!/usr/bin/env python3
"""
Test script to validate the new wellness-enhanced UTL calculations
and update existing activities with improved TRIMP scoring.
"""

import sys
import os
sys.path.append('/Users/adam/src/TrainingLoad/backend')
sys.path.append('/Users/adam/src/TrainingLoad')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Activity, Threshold, WellnessData, User
from utils import calculate_utl
import json

# Database connection
DATABASE_URL = "postgresql://trainload:SAq](J$N3*\"eP8z]@127.0.0.1:5432/trainload"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_new_utl_calculations():
    db = SessionLocal()
    
    try:
        # Get user 1's threshold data
        threshold = db.query(Threshold).filter_by(user_id=1).first()
        if not threshold:
            print("❌ No threshold data found for user 1")
            return
        
        print(f"📊 User 1 Thresholds:")
        print(f"   FTP: {threshold.ftp_watts}W")
        print(f"   FThP: {threshold.fthp_mps} m/s")
        print(f"   Max HR: {threshold.max_hr} bpm")
        print(f"   Rest HR: {threshold.resting_hr} bpm")
        print()
        
        # Get recent hiking activities
        hiking_activities = db.query(Activity).filter(
            Activity.user_id == 1,
            Activity.type == 'Hike'
        ).order_by(Activity.start_date.desc()).limit(3).all()
        
        print(f"🥾 Testing {len(hiking_activities)} hiking activities with new UTL calculation:")
        print()
        
        for activity in hiking_activities:
            print(f"Activity: {activity.name}")
            print(f"Date: {activity.start_date}")
            print(f"Duration: {activity.moving_time/3600:.1f} hours")
            print(f"Old UTL: {activity.utl_score:.2f} ({activity.calculation_method})")
            
            # Reconstruct activity summary
            activity_summary = {
                'type': activity.type,
                'moving_time': activity.moving_time,
                'distance': activity.distance,
                'average_speed': activity.average_speed,
                'start_date': activity.start_date.isoformat() if activity.start_date else None
            }
            
            # Get activity streams from stored data
            activity_streams = None
            if activity.data and isinstance(activity.data, dict):
                activity_streams = activity.data.get('streams')
            
            # Get wellness data for this date
            wellness_data = None
            if activity.start_date:
                wellness_entry = db.query(WellnessData).filter(
                    WellnessData.user_id == 1,
                    WellnessData.date == activity.start_date.date()
                ).first()
                
                if wellness_entry:
                    wellness_data = {
                        'hrv': wellness_entry.hrv,
                        'sleepScore': wellness_entry.sleep_score,
                        'readiness': wellness_entry.readiness_score,
                        'restingHR': wellness_entry.resting_hr
                    }
                    print(f"Wellness: HRV={wellness_entry.hrv:.1f}, Sleep={wellness_entry.sleep_score}, Readiness={wellness_entry.readiness_score}")
            
            # Calculate new UTL
            new_utl, new_method = calculate_utl(activity_summary, threshold, activity_streams, wellness_data)
            
            print(f"New UTL: {new_utl:.2f} ({new_method})")
            print(f"Change: {new_utl - activity.utl_score:+.2f} ({((new_utl - activity.utl_score) / activity.utl_score * 100):+.1f}%)")
            print("-" * 60)
            
            # Update the activity in database
            activity.utl_score = float(new_utl)  # Convert numpy float to Python float
            activity.calculation_method = new_method
        
        # Commit changes
        db.commit()
        print("✅ Updated hiking activities with new UTL calculations")
        print()
        
        # Test a running activity
        running_activities = db.query(Activity).filter(
            Activity.user_id == 1,
            Activity.type == 'Run'
        ).order_by(Activity.start_date.desc()).limit(2).all()
        
        print(f"🏃 Testing {len(running_activities)} running activities:")
        print()
        
        for activity in running_activities:
            print(f"Activity: {activity.name}")
            print(f"Old UTL: {activity.utl_score:.2f} ({activity.calculation_method})")
            
            # Same reconstruction as above
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
            
            wellness_data = None
            if activity.start_date:
                wellness_entry = db.query(WellnessData).filter(
                    WellnessData.user_id == 1,
                    WellnessData.date == activity.start_date.date()
                ).first()
                
                if wellness_entry:
                    wellness_data = {
                        'hrv': wellness_entry.hrv,
                        'sleepScore': wellness_entry.sleep_score,
                        'readiness': wellness_entry.readiness_score,
                        'restingHR': wellness_entry.resting_hr
                    }
            
            new_utl, new_method = calculate_utl(activity_summary, threshold, activity_streams, wellness_data)
            
            print(f"New UTL: {new_utl:.2f} ({new_method})")
            print(f"Change: {new_utl - activity.utl_score:+.2f}")
            print("-" * 40)
            
            activity.utl_score = float(new_utl)  # Convert numpy float to Python float
            activity.calculation_method = new_method
        
        db.commit()
        print("✅ Updated running activities")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_new_utl_calculations()
