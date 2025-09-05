# TrainingLoad - Quick Architecture Reference

## Stack
FastAPI + React + PostgreSQL Cloud SQL + APScheduler + UV + Google App Engine

## Key Patterns
- **DB Access**: Use psql directly (`PGPASSWORD='...' psql -h 127.0.0.1 -U trainload -d trainload`)
- **Process Mgmt**: `./start.sh` / `./stop.sh` with PID tracking, logs in `logs/`
- **Environment**: UV virtual env (`.venv/`), deps in `pyproject.toml`
- **Scheduling**: APScheduler in `main.py` (not separate daemon), jobs API at `/scheduler/jobs`
- **Database**: Cloud SQL proxy running, connection from `.env` DATABASE_URL

## Core Flow
1. Strava OAuth → Research thresholds → Activity import (90d) → UTL calculation (TSS/rTSS/TRIMP)
2. Wellness data (Intervals.icu) → UTL modifiers (HRV/sleep/readiness) + Resting HR updates → Auto recalculation
3. Background jobs: 30min sync, daily import, weekly thresholds, monthly UTL recalc, resting HR updates (every 3d)

## UTL Hierarchy
TSS (power) > rTSS (pace) > TRIMP (HR) + wellness modifiers (0.8x-1.1x range)

## Debugging
- Logs: `tail -f logs/backend.log`
- DB: Direct SQL queries preferred over Python scripts
- Jobs: `/scheduler/run/{job_id}` for manual execution
- Health: `/health` endpoint
