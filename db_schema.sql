-- TrainSmart Database Schema (Postgres)

-- Users Table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    age INTEGER,
    gender VARCHAR(10),
    weight REAL,
    garmin_user_id VARCHAR(255),
    garmin_oauth_token VARCHAR(255),
    garmin_oauth_secret VARCHAR(255),
    injury_history_flags JSONB
);

-- Thresholds Table
CREATE TABLE thresholds (
    threshold_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    ftp_watts REAL,
    fthp_mps REAL,
    max_hr INTEGER,
    resting_hr INTEGER,
    date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Activities Table
CREATE TABLE activities (
    activity_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    garmin_activity_id VARCHAR(255),
    start_time TIMESTAMP,
    sport VARCHAR(50),
    duration_sec INTEGER,
    distance_m REAL,
    utl_score REAL,
    calculation_method VARCHAR(20),
    raw_fit_file_path VARCHAR(255)
);

-- Daily Health Summaries Table
CREATE TABLE daily_health_summaries (
    summary_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    calendar_date DATE,
    lnrmssd REAL,
    sleep_seconds INTEGER,
    deep_sleep_seconds INTEGER,
    resting_hr INTEGER,
    avg_stress_level REAL
);

-- Training Load Metrics Table
CREATE TABLE training_load_metrics (
    metric_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    calendar_date DATE,
    daily_utl REAL,
    ctl REAL,
    atl REAL,
    acwr REAL
);
