# GitHub Copilot Instructions - TrainingLoad

## Project Overview
TrainingLoad is an evidence-based training load monitoring system that provides personalized training metrics using scientific algorithms (TSS, rTSS, TRIMP). It integrates with Strava and Intervals.icu to calculate Unit Training Load (UTL) scores enhanced with wellness data (HRV, sleep, readiness).

**Target Users**: Serious recreational athletes (cyclists/runners) who want coaching-level insights without the cost.

## Architecture & Stack

### Core Technologies
- **Backend**: FastAPI + SQLAlchemy ORM + PostgreSQL Cloud SQL
- **Frontend**: React + Vite build system  
- **Environment**: UV package manager with `.venv/` virtual environment
- **Database**: Cloud SQL PostgreSQL via `cloud-sql-proxy`
- **Scheduling**: APScheduler integrated into FastAPI `main.py` (not separate daemon)
- **Deployment**: Google App Engine + Cloud Scheduler
- **Authentication**: OAuth2 (Strava, Intervals.icu)

### File Structure
```
backend/
├── main.py              # FastAPI app + APScheduler background jobs
├── activities.py        # Strava integration, activity import, UTL calculation
├── dashboard.py         # Dashboard data aggregation and metrics
├── intervals_icu.py     # Intervals.icu wellness data integration
├── utils.py            # UTL algorithms (TSS/rTSS/TRIMP) + wellness modifiers
├── models.py           # SQLAlchemy database models
├── config.py           # Database connection + environment config
└── research_threshold_calculator.py  # Evidence-based threshold estimation

frontend/
├── OnboardingForm.jsx   # Multi-step onboarding with progress polling
└── Dashboard.jsx       # Main dashboard with UTL metrics/visualizations
```

## Development Patterns & Best Practices

### Environment Management
- **Always use UV**: `uv sync` for dependencies, `uv run` for execution
- **Dependencies**: Managed in `pyproject.toml` with `uv.lock`
- **Virtual environment**: `.venv/` directory (UV managed)

### Database Operations
- **Prefer SQL over Python scripts**: Use `PGPASSWORD='...' psql -h 127.0.0.1 -U trainload -d trainload`
- **Connection**: Via Cloud SQL proxy, config from `.env` DATABASE_URL
- **Schema**: Core entities: `users`, `activities`, `thresholds`, `wellness_data`
- **Activity data**: Detailed streams (power, HR, pace) stored as JSONB

### Process Management
- **Start services**: `./start.sh` (backend port 8000, frontend port 5173)
- **Stop services**: `./stop.sh` (graceful shutdown with PID tracking)
- **Logs**: `logs/backend.log`, `logs/frontend.log` for debugging
- **Hot reload**: FastAPI auto-reloads on file changes

### Background Processing
- **APScheduler**: Integrated in `main.py`, not separate daemon
- **Jobs**: 30min Strava sync, daily import, weekly thresholds, monthly UTL recalc, 3-day resting HR updates
- **Management**: `/scheduler/jobs` endpoint, `/scheduler/run/{job_id}` for manual execution
- **Persistence**: SQLite job store (`scheduler_jobs.sqlite`)

## Core Business Logic

### UTL Calculation Hierarchy (Priority Order)
1. **TSS (Training Stress Score)**: Power-based cycling (requires FTP watts)
2. **rTSS (running TSS)**: Pace-based running (requires FTHP m/s)
3. **TRIMP**: Heart rate-based fallback with activity-specific scaling
4. **Wellness Modifiers**: Applied to all methods
   - HRV: 0.8x - 1.1x multiplier
   - Sleep quality: 0.85x - 1.05x multiplier  
   - Readiness: 0.8x - 1.1x multiplier

### Application Flow
1. **Onboarding**: Strava OAuth → Research thresholds → 90-day activity import → UTL calculation
2. **Wellness Integration**: Intervals.icu sync (12 months) → UTL modifiers → Auto recalculation
3. **Threshold Updates**: Automatic via significant activities or wellness data → Resting HR from 2-week average

### Data Sync Timeframes
- **Initial activity import**: 90 days
- **Wellness data sync**: 365 days (12 months, matches Strava)
- **Threshold analysis**: 365 days lookback
- **Resting HR calculation**: 14 days average from wellness data

## Coding Guidelines

### When Writing Code
- **Error handling**: Always wrap external API calls in try/catch with detailed logging
- **Logging**: Use structured logging with context (user_id, operation, timestamps)
- **Database sessions**: Always use dependency injection `db: Session = Depends(get_db)`
- **Async operations**: Use BackgroundTasks for long-running operations (imports, calculations)
- **Data validation**: Validate all data fields against schema models.py before writing code to avoid mismatched, incorrect fields/columns etc. 

### API Design
- **REST conventions**: Use appropriate HTTP methods and status codes
- **Response format**: Consistent JSON structure with `message` and `data` fields
- **Error responses**: Include detailed error messages and suggestions
- **Background tasks**: Return task status immediately, provide status endpoints

### Database Best Practices
- **Queries**: Prefer direct SQL for debugging, SQLAlchemy for application logic
- **Null handling**: Always check for null UTL scores, thresholds before calculations
- **Indexes**: Consider performance for user_id, date range queries
- **Transactions**: Commit after successful calculations, rollback on errors

## Testing & Debugging

### Common Debug Commands
```bash
# Environment
uv sync                                    # Update dependencies
tail -f logs/backend.log                   # Monitor backend logs

# Database
PGPASSWORD='...' psql -h 127.0.0.1 -U trainload -d trainload
SELECT COUNT(*) FROM activities WHERE user_id = 1 AND utl_score IS NULL;

# Scheduler
curl -s http://localhost:8000/scheduler/jobs    # Check scheduled jobs
curl -X POST http://localhost:8000/scheduler/run/daily_sync  # Manual job run

# Health checks
curl http://localhost:8000/health               # API health
ps aux | grep cloud-sql-proxy                  # Database proxy status
```

### Debugging Patterns
- **Database issues**: Verify cloud-sql-proxy running, check `.env` DATABASE_URL
- **Import problems**: Monitor activity count API, verify Strava token validity  
- **UTL calculation**: Query for null scores, verify thresholds exist, check wellness data schema
- **Scheduler issues**: Check `/scheduler/jobs`, review startup logs

## Deployment Considerations

### Local Development
- **Prerequisites**: Cloud SQL proxy running, `.env` configured
- **Process**: Use `./start.sh` for development, monitors file changes
- **APIs**: Backend on :8000, Frontend on :5173, API docs at :8000/docs

### Production (App Engine)
- **Configuration**: `app.yaml` for Python 3.11 runtime
- **Environment**: Variables from App Engine settings (not `.env`)
- **Database**: Built-in Cloud SQL proxy (no manual proxy)
- **Scheduling**: Cloud Scheduler replaces APScheduler jobs

## Common Issues & Solutions

1. **"UTL scores showing N/A"**: Run threshold recalculation, verify wellness data schema fields
2. **"Import hanging"**: Check Strava API rate limits, monitor with activity count endpoint  
3. **"Database connection errors"**: Restart cloud-sql-proxy, verify `.env` DATABASE_URL
4. **"Scheduler not starting"**: APScheduler integrated in main.py, check startup logs
5. **"Frontend build issues"**: Use `uv run` for consistent environment

## Key Endpoints for AI Reference
- `POST /auth/strava/login` - Strava OAuth initiation
- `GET /activities/count/{user_id}` - Activity count for progress tracking
- `POST /intervals/sync_wellness` - Wellness data sync (365 days)
- `GET /scheduler/jobs` - Background job status
- `POST /scheduler/run/{job_id}` - Manual job execution
- `GET /health` - System health check

## Code Context Notes
- **Wellness sync**: Now uses 365 days to match Strava (changed from 30 days)
- **Resting HR**: Auto-calculated from 2-week wellness average, updates thresholds
- **Progress tracking**: Real-time polling every 2 seconds during onboarding
- **UTL modifiers**: Applied based on date-matched wellness data
- **Stream analysis**: Power curves and critical speed for accurate thresholds

When suggesting code changes, consider the existing patterns, error handling, and logging practices. Always test database connectivity and verify the cloud-sql-proxy is running for local development.