# TrainingLoad - System Architecture

## Overview
TrainingLoad is an evidence-based training load monitoring system that provides personalized training metrics using scientific algorithms (TSS, rTSS, TRIMP). It integrates with Strava and Intervals.icu to calculate Unit Training Load (UTL) scores enhanced with wellness data.

## Stack
FastAPI + React + PostgreSQL Cloud SQL + APScheduler + UV + Google App Engine

## Key Development Patterns
- **DB Access**: Use psql directly (`PGPASSWORD='...' psql -h 127.0.0.1 -U trainload -d trainload`)
- **Process Mgmt**: `./start.sh` / `./stop.sh` with PID tracking, logs in `logs/`
- **Environment**: UV virtual env (`.venv/`), deps in `pyproject.toml`
- **Scheduling**: APScheduler in `main.py` (not separate daemon), jobs API at `/scheduler/jobs`
- **Database**: Cloud SQL proxy running, connection from `.env` DATABASE_URL

## Application Flow
1. **Onboarding**: Strava OAuth → Research thresholds → Activity import (90d) → UTL calculation (TSS/rTSS/TRIMP)
2. **Wellness Integration**: Intervals.icu sync → UTL modifiers (HRV/sleep/readiness) + Resting HR updates → Auto recalculation  
3. **Background Processing**: 3.5h quick sync (activities + wellness), daily comprehensive sync, weekly thresholds, monthly UTL recalc, resting HR updates (every 3d)

## Background Jobs Schedule

### Quick Sync (Every 3.5 Hours)
- **Purpose**: Keep user dashboards current with latest data
- **Actions**: Fetch Strava activities (3d), sync wellness data (7d), auto-update thresholds
- **Benefit**: Users see new workouts within 3.5 hours instead of 24 hours

### Daily Comprehensive (2:00 AM)  
- **Purpose**: Deep maintenance and data validation
- **Actions**: Extended Strava sync (14d), comprehensive wellness (30d), threshold validation
- **Benefit**: Ensures data completeness and accuracy

### Weekly Threshold Recalculation (Sundays 3:00 AM)
- **Purpose**: Full threshold analysis using 12 months of data
- **Actions**: Power curve analysis, critical speed calculation, UTL recalc if >5% change
- **Benefit**: Accurate fitness tracking as performance evolves

### Monthly UTL Recalculation (1st of Month 4:00 AM) 
- **Purpose**: Accuracy maintenance and drift correction
- **Actions**: Recalculate all UTL scores for 90d, apply updated wellness modifiers
- **Benefit**: Maintains calculation accuracy over time

### Resting HR Updates (Every 3 Days 5:00 AM)
- **Purpose**: Keep resting HR current for TRIMP calculations
- **Actions**: 14-day average from wellness data, update thresholds
- **Benefit**: Accurate heart rate zone calculations

## UTL Calculation Hierarchy
**TSS** (power-based) > **rTSS** (pace-based) > **TRIMP** (HR-based) + wellness modifiers (0.8x-1.1x range)

## Debugging Quick Reference
- **Logs**: `tail -f logs/backend.log`
- **Database**: Direct SQL queries preferred over Python scripts  
- **Jobs**: `/scheduler/run/{job_id}` for manual execution
- **Health**: `/health` endpoint
- **Testing**: `/sync/test/{user_id}` for user-specific sync testing

## API Endpoints Summary

### Core APIs
- `POST /auth/strava/login` - Strava OAuth initiation
- `GET /activities/count/{user_id}` - Activity count for progress tracking  
- `POST /intervals/sync_wellness` - Wellness data sync
- `GET /recommendations/{user_id}` - Training recommendations with distance guidance

### Background Job Management
- `GET /scheduler/jobs` - View all scheduled jobs
- `POST /scheduler/run/{job_id}` - Manual job execution
- `POST /sync/test/{user_id}` - Test sync for specific user

### System Health
- `GET /health` - System health check
- `GET /` - API info and version

---

*This architecture supports ~1000+ users with real-time training insights and injury prevention capabilities.*
