#!/bin/bash
# Cloud Scheduler Setup for TrainingLoad Background Jobs

set -e

PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: No Google Cloud project configured"
    exit 1
fi

APP_URL="https://${PROJECT_ID}.appspot.com"

echo "🕐 Setting up Cloud Scheduler jobs for TrainingLoad"
echo "   Project: $PROJECT_ID"
echo "   App URL: $APP_URL"
echo ""

# Check if Cloud Scheduler API is enabled
if ! gcloud services list --enabled --filter="name:cloudscheduler.googleapis.com" --format="value(name)" | grep -q "cloudscheduler.googleapis.com"; then
    echo "Enabling Cloud Scheduler API..."
    gcloud services enable cloudscheduler.googleapis.com
fi

# Create or update scheduled jobs
echo "Creating Cloud Scheduler jobs..."

# 1. Quick Sync Job (Every 3.5 hours)
echo "📅 Quick Sync Job (every 3.5 hours)"
gcloud scheduler jobs create http quick-sync-job \
    --schedule="0 */4 * * *" \
    --uri="${APP_URL}/scheduler/run/quick_sync" \
    --http-method=POST \
    --headers="Content-Type=application/json" \
    --description="TrainingLoad quick sync - activities and wellness data" \
    --time-zone="America/New_York" \
    --attempt-deadline=300s \
    --max-retry-attempts=3 \
    --min-backoff-duration=5s \
    --max-backoff-duration=300s \
    --replace || echo "⚠️  Job may already exist, continuing..."

# 2. Daily Comprehensive Sync (2:00 AM daily)
echo "📅 Daily Comprehensive Sync (2:00 AM daily)"
gcloud scheduler jobs create http daily-sync-job \
    --schedule="0 2 * * *" \
    --uri="${APP_URL}/scheduler/run/daily_sync" \
    --http-method=POST \
    --headers="Content-Type=application/json" \
    --description="TrainingLoad daily comprehensive sync" \
    --time-zone="America/New_York" \
    --attempt-deadline=600s \
    --max-retry-attempts=2 \
    --min-backoff-duration=10s \
    --max-backoff-duration=600s \
    --replace || echo "⚠️  Job may already exist, continuing..."

# 3. Weekly Threshold Recalculation (Sundays 3:00 AM)
echo "📅 Weekly Threshold Recalculation (Sundays 3:00 AM)"
gcloud scheduler jobs create http weekly-thresholds-job \
    --schedule="0 3 * * 0" \
    --uri="${APP_URL}/scheduler/run/weekly_thresholds" \
    --http-method=POST \
    --headers="Content-Type=application/json" \
    --description="TrainingLoad weekly threshold recalculation" \
    --time-zone="America/New_York" \
    --attempt-deadline=900s \
    --max-retry-attempts=2 \
    --min-backoff-duration=30s \
    --max-backoff-duration=900s \
    --replace || echo "⚠️  Job may already exist, continuing..."

# 4. Monthly UTL Recalculation (1st of month 4:00 AM)
echo "📅 Monthly UTL Recalculation (1st of month 4:00 AM)"
gcloud scheduler jobs create http monthly-utl-job \
    --schedule="0 4 1 * *" \
    --uri="${APP_URL}/scheduler/run/monthly_utl" \
    --http-method=POST \
    --headers="Content-Type=application/json" \
    --description="TrainingLoad monthly UTL recalculation" \
    --time-zone="America/New_York" \
    --attempt-deadline=1200s \
    --max-retry-attempts=2 \
    --min-backoff-duration=60s \
    --max-backoff-duration=1200s \
    --replace || echo "⚠️  Job may already exist, continuing..."

# 5. Resting HR Updates (Every 3 days 5:00 AM)
echo "📅 Resting HR Updates (every 3 days 5:00 AM)"
gcloud scheduler jobs create http resting-hr-job \
    --schedule="0 5 */3 * *" \
    --uri="${APP_URL}/scheduler/run/resting_hr_update" \
    --http-method=POST \
    --headers="Content-Type=application/json" \
    --description="TrainingLoad resting HR updates from wellness data" \
    --time-zone="America/New_York" \
    --attempt-deadline=300s \
    --max-retry-attempts=3 \
    --min-backoff-duration=5s \
    --max-backoff-duration=300s \
    --replace || echo "⚠️  Job may already exist, continuing..."

echo ""
echo "✅ Cloud Scheduler setup complete!"
echo ""
echo "📋 Scheduled Jobs:"
echo "   • Quick Sync: Every 4 hours"
echo "   • Daily Sync: 2:00 AM daily"  
echo "   • Weekly Thresholds: Sundays 3:00 AM"
echo "   • Monthly UTL: 1st of month 4:00 AM"
echo "   • Resting HR: Every 3 days 5:00 AM"
echo ""
echo "🔍 View jobs: gcloud scheduler jobs list"
echo "▶️  Test job: gcloud scheduler jobs run JOB_NAME"
