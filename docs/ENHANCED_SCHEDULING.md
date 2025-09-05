# Enhanced Background Processing Schedule

## Overview
Updated the background job scheduling system to provide more frequent data updates and comprehensive sync processing.

## New Scheduling System

### 1. Quick Sync Job (Every 3.5 Hours)
**Purpose**: Regular data updates to keep user dashboards current
**Frequency**: Every 3 hours 30 minutes
**Actions**:
- ✅ Fetch Strava activities (last 3 days)
- ✅ Sync Intervals.icu wellness data (last 7 days)
- ✅ Auto-update thresholds if 3+ significant activities this week
- ✅ Process UTL calculations for new activities

**Benefits**:
- Users see new workouts within 3.5 hours instead of 24 hours
- Wellness data stays current for accurate UTL modifiers
- Automatic threshold updates when training patterns change

### 2. Daily Comprehensive Sync (2:00 AM)
**Purpose**: Deep maintenance and data validation
**Frequency**: Once daily at 2 AM
**Actions**:
- ✅ Extended Strava sync (last 14 days)
- ✅ Comprehensive wellness sync (last 30 days)
- ✅ Threshold validation and updates
- ✅ Resting HR recalculation from wellness data

### 3. Weekly Threshold Recalculation (Sundays 3:00 AM)
**Purpose**: Full threshold analysis using power curves and critical speed
**Frequency**: Weekly on Sundays
**Actions**:
- ✅ Full threshold recalculation from 12 months of data
- ✅ Extended wellness analysis (30-day lookback)
- ✅ UTL recalculation if thresholds change >5%

### 4. Monthly UTL Recalculation (1st of month 4:00 AM)
**Purpose**: Accuracy maintenance and drift correction
**Frequency**: First day of each month
**Actions**:
- ✅ Recalculate all UTL scores for last 90 days
- ✅ Apply updated wellness modifiers retroactively
- ✅ Fix any calculation drift from threshold updates

### 5. Resting HR Updates (Every 3 Days 5:00 AM)
**Purpose**: Keep resting HR current for accurate TRIMP calculations
**Frequency**: Every 3 days
**Actions**:
- ✅ Calculate 14-day average resting HR from wellness data
- ✅ Update user thresholds with new resting HR
- ✅ Critical for accurate heart rate zone calculations

## Improvements Over Previous System

| Aspect | Before | After |
|--------|--------|-------|
| Activity Updates | 24 hours | 3.5 hours |
| Wellness Integration | Manual only | Automatic every 3.5 hours |
| Data Freshness | Stale for long periods | Always current |
| User Experience | Static dashboards | Live, updating metrics |
| Error Recovery | Daily only | Multiple checkpoints |

## API Endpoints for Testing

### Manual Job Triggers
```bash
# Test quick sync
curl -X POST http://localhost:8000/scheduler/run/quick_sync

# Test daily sync  
curl -X POST http://localhost:8000/scheduler/run/daily_sync

# View all scheduled jobs
curl http://localhost:8000/scheduler/jobs
```

### User-Specific Testing
```bash
# Test sync for specific user (replace 1 with actual user_id)
curl -X POST http://localhost:8000/sync/test/1
```

## Benefits for Users

### Immediate Impact
- **New workouts appear within hours** instead of waiting until the next day
- **Wellness data stays current** for accurate training load calculations
- **Training recommendations update automatically** as fitness changes

### Long-term Benefits
- **More accurate UTL scores** from frequent wellness integration
- **Better threshold tracking** with regular power curve analysis
- **Improved training recommendations** from current fitness data

## Technical Implementation

### Memory & Performance
- Quick sync uses shorter lookback windows (3-7 days)
- Daily sync handles larger data sets (14-30 days) during low-usage hours
- Background processing doesn't impact user-facing API performance

### Error Handling
- Each user sync is isolated (one failure doesn't stop others)
- Multiple recovery opportunities (quick sync failures are retried daily)
- Detailed logging for troubleshooting sync issues

### Data Consistency
- Wellness data synchronized alongside activity data
- Threshold updates trigger automatic UTL recalculation
- Resting HR updates ensure accurate heart rate calculations

## Future Enhancements

### Potential Improvements
- **Smart sync intervals** based on user activity patterns
- **Push notifications** when new activities are processed
- **Predictive sync** for users with regular training schedules
- **Real-time webhooks** from Strava API for instant updates

This enhanced scheduling system transforms TrainingLoad from a daily-batch system to a near real-time training monitoring platform while maintaining data accuracy and system reliability.
