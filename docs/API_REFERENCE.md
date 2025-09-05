# API Reference

## Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://trainload-app-[project-id].uc.r.appspot.com`

## Authentication
All API endpoints requiring user authentication expect valid OAuth2 tokens from Strava or Intervals.icu integrations.

## Core Endpoints

### Training Recommendations
```http
GET /recommendations/{user_id}
```
Generate science-based training recommendations for the next 5 days.

**Parameters**:
- `user_id` (int): User identifier

**Response**:
```json
{
  "status": "success",
  "data": {
    "recommendations": [
      {
        "date": "2025-09-06",
        "activity_type": "running",
        "distance_range": "5-7 km",
        "utl_target": "45-55",
        "intensity": "easy",
        "rationale": "ACWR 1.1, good recovery status"
      }
    ],
    "weekly_targets": {
      "total_utl": 280,
      "running_utl": 180,
      "cycling_utl": 100
    },
    "acwr_status": {
      "overall": 1.1,
      "running": 1.0,
      "cycling": 1.2,
      "risk_level": "optimal"
    }
  }
}
```

### System Health
```http
GET /health
```
Check system health and availability.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-09-05T10:30:00Z"
}
```

## Background Job Management

### Job Status
```http
GET /scheduler/jobs
```
Get status of all scheduled background jobs.

**Response**:
```json
{
  "total_jobs": 5,
  "scheduler_running": true,
  "jobs": [
    {
      "id": "quick_sync",
      "name": "Quick Sync (Activities + Wellness)",
      "next_run_time": "2025-09-05T14:00:00Z",
      "trigger": "interval[3:30:00]",
      "function": "quick_sync_job"
    }
  ]
}
```

### Manual Job Execution
```http
POST /scheduler/run/{job_id}
```
Manually trigger a scheduled job.

**Parameters**:
- `job_id` (string): Job identifier (`quick_sync`, `daily_sync`, `weekly_thresholds`, `monthly_utl`, `resting_hr_update`)

**Response**:
```json
{
  "message": "Job quick_sync executed successfully"
}
```

### User-Specific Testing
```http
POST /sync/test/{user_id}
```
Test synchronization for a specific user.

**Parameters**:
- `user_id` (int): User identifier

**Response**:
```json
{
  "message": "Test sync completed for user 1",
  "new_activities": 2,
  "wellness_synced": true,
  "has_strava": true,
  "has_intervals": true
}
```

## User Management

### Activity Count
```http
GET /activities/count/{user_id}
```
Get total activity count for progress tracking.

**Response**:
```json
{
  "activity_count": 156
}
```

## Authentication Endpoints

### Strava OAuth
```http
POST /auth/strava/login
```
Initiate Strava OAuth flow.

### Intervals.icu Integration
```http
POST /intervals/sync_wellness
```
Sync wellness data from Intervals.icu.

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": "Error description",
  "detail": "Additional error details"
}
```

### HTTP Status Codes
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `401`: Unauthorized (authentication required)
- `404`: Not Found (user/resource not found)
- `500`: Internal Server Error

## Rate Limiting

- **General API**: 100 requests per minute per user
- **Background Jobs**: Internal rate limiting prevents excessive execution
- **Sync Operations**: Limited by Strava/Intervals.icu API constraints

## Data Formats

### Dates
All dates in ISO 8601 format: `2025-09-05T10:30:00Z`

### UTL Scores
Numeric values representing Unit Training Load:
- **Easy session**: 20-40 UTL
- **Moderate session**: 40-80 UTL  
- **Hard session**: 80-150 UTL
- **Race/Time Trial**: 150+ UTL

### ACWR Values
Acute:Chronic Workload Ratios:
- **< 0.5**: Detraining risk
- **0.5 - 0.8**: Low load
- **0.8 - 1.3**: Optimal zone
- **1.3 - 1.5**: Elevated risk
- **> 1.5**: High injury risk

---

*For detailed implementation examples and integration guides, see the [ARCHITECTURE.md](ARCHITECTURE.md) documentation.*
