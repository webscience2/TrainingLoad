#!/usr/bin/env python3
"""
Test script to create sample data for dashboard testing
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from models import User, Activity, Threshold
from config import SessionLocal
from utils import calculate_utl
import random

def create_sample_data():
    db = SessionLocal()

    try:
        # Check if test user already exists
        test_user = db.query(User).filter_by(email="test@example.com").first()
        if not test_user:
            # Create a test user
            test_user = User(
                email="test@example.com",
                password_hash="hashed_password",
                name="Test Athlete",
                gender="male",
                weight="75"
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            print("✅ Created new test user")
        else:
            print("✅ Using existing test user")

        # Check if thresholds exist
        threshold = db.query(Threshold).filter_by(user_id=test_user.user_id).first()
        if not threshold:
            # Create thresholds for the user
            threshold = Threshold(
                user_id=test_user.user_id,
                ftp_watts=250,
                fthp_mps=4.5,
                max_hr=190,
                resting_hr=50,
                date_updated=datetime.now()
            )
            db.add(threshold)
            db.commit()
            print("✅ Created thresholds for user")
        else:
            print("✅ Using existing thresholds")

        # Create sample activities for the last 30 days (simplified version)
        base_date = datetime.now() - timedelta(days=30)

        for i in range(30):
            activity_date = base_date + timedelta(days=i)

            # Skip some days to make it more realistic
            if random.random() < 0.3:
                continue

            # Create a mix of ride and run activities
            activity_type = "Ride" if random.random() < 0.7 else "Run"

            if activity_type == "Ride":
                distance = random.randint(20000, 80000)  # 20-80km
                moving_time = int(distance / random.uniform(3.5, 5.5))  # 3.5-5.5 m/s average
                avg_speed = distance / moving_time
                avg_watts = random.randint(180, 280)
            else:
                distance = random.randint(5000, 15000)  # 5-15km
                moving_time = int(distance / random.uniform(3.0, 4.5))  # 3.0-4.5 m/s average
                avg_speed = distance / moving_time
                avg_watts = None

            # Create activity without UTL fields for now
            activity = Activity(
                strava_activity_id=f"test_activity_{i}_{random.randint(1000, 9999)}",
                user_id=test_user.user_id,
                name=f"{activity_type} on {activity_date.strftime('%Y-%m-%d')}",
                type=activity_type,
                distance=distance,
                moving_time=moving_time,
                elapsed_time=moving_time + random.randint(0, 300),
                start_date=activity_date,
                average_speed=avg_speed,
                max_speed=avg_speed * 1.2,
                total_elevation_gain=random.randint(100, 800),
                data={
                    "average_watts": avg_watts,
                    "max_heartrate": random.randint(150, 185) if random.random() < 0.8 else None
                }
            )

            db.add(activity)

        db.commit()

        print(f"✅ Created test user with ID: {test_user.user_id}")
        print(f"✅ Created {len(db.query(Activity).filter_by(user_id=test_user.user_id).all())} sample activities")
        print(f"✅ Thresholds: FTP={threshold.ftp_watts}W, FThP={threshold.fthp_mps}m/s, MaxHR={threshold.max_hr}bpm")

        return test_user.user_id

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating sample data: {e}")
        return None
    finally:
        db.close()

if __name__ == "__main__":
    user_id = create_sample_data()
    if user_id:
        print(f"\n🎉 Sample data created successfully!")
        print(f"📊 You can now test the dashboard at: http://localhost:5173/")
        print(f"🔗 Dashboard API endpoint: http://localhost:8000/dashboard/{user_id}")
        print(f"📱 API docs: http://localhost:8000/docs")
    else:
        print("❌ Failed to create sample data")
