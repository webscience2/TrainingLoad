# User model and table creation for FastAPI/SQLAlchemy
from sqlalchemy import Column, Integer, String, JSON, Float, DateTime, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from db import engine

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    dob = Column(DateTime)
    gender = Column(String(10))
    weight = Column(String(20))
    strava_user_id = Column(String(255))
    strava_oauth_token = Column(String(255))
    strava_refresh_token = Column(String(255))
    strava_token_expires_at = Column(Integer)
    injury_history_flags = Column(JSON)
    integrations = Column(JSON)  # Store third-party integrations like intervals.icu


class Threshold(Base):
    __tablename__ = "thresholds"
    threshold_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    ftp_watts = Column(Float)  # Functional Threshold Power for cycling
    fthp_mps = Column(Float)  # Functional Threshold Pace for running (m/s)
    max_hr = Column(Integer)  # Maximum Heart Rate
    resting_hr = Column(Integer)  # Resting Heart Rate
    date_updated = Column(DateTime)


class Activity(Base):
    __tablename__ = "activities"
    activity_id = Column(Integer, primary_key=True, autoincrement=True)
    strava_activity_id = Column(String(255), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    name = Column(String(255))
    type = Column(String(50))
    distance = Column(Float)  # meters
    moving_time = Column(Integer)  # seconds
    elapsed_time = Column(Integer)  # seconds
    start_date = Column(DateTime)
    average_speed = Column(Float)
    max_speed = Column(Float)
    total_elevation_gain = Column(Float)
    utl_score = Column(Float)  # Training Load score
    calculation_method = Column(String(50))  # e.g., 'TSS', 'rTSS', 'TRIMP'
    data = Column(JSON)  # store full Strava activity JSON if needed


class WellnessData(Base):
    __tablename__ = "wellness_data"
    wellness_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    date = Column(Date, nullable=False)
    hrv = Column(Float)  # Heart Rate Variability (RMSSD)
    resting_hr = Column(Integer)  # Resting Heart Rate
    sleep_score = Column(Float)  # Sleep quality score
    sleep_duration = Column(Float)  # Hours of sleep
    readiness_score = Column(Float)  # Overall readiness/recovery score
    stress_score = Column(Float)  # Perceived stress level
    weight = Column(Float)  # Body weight
    body_fat = Column(Float)  # Body fat percentage
    hydration = Column(Float)  # Hydration level
    energy = Column(Float)  # Energy level
    motivation = Column(Float)  # Motivation level
    mood = Column(Float)  # Mood score
    soreness = Column(Float)  # Muscle soreness level
    fatigue = Column(Float)  # Fatigue level
    source = Column(String(50))  # Data source (e.g., 'intervals_icu', 'manual')
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

# Create the tables in the database
if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("User, Threshold, Activity, and WellnessData tables created (if not exists)")
