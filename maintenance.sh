#!/bin/bash

# TrainingLoad Data Maintenance Script
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "🔧 TrainingLoad Data Maintenance"
echo ""

# Function to calculate UTL for existing activities
calculate_utl_for_existing() {
    echo "📊 Calculating UTL scores for existing activities..."
    cd "$BACKEND_DIR"
    
    uv run python3 -c "
import sys
sys.path.append('.')

from config import SessionLocal
from models import User, Activity, Threshold
from utils import calculate_utl
import logging

logging.basicConfig(level=logging.INFO)

# Get database session
db = SessionLocal()

try:
    # Get all users with Strava data
    users = db.query(User).filter(User.strava_user_id.isnot(None)).all()
    print(f'Found {len(users)} users with Strava data')
    
    for user in users:
        print(f'Processing user {user.user_id}: {user.name}')
        
        # Get user's threshold data
        threshold = db.query(Threshold).filter_by(user_id=user.user_id).first()
        if not threshold:
            print(f'  No thresholds found for user {user.user_id}, skipping UTL calculation')
            continue
            
        # Get activities without UTL scores
        activities = db.query(Activity).filter(
            Activity.user_id == user.user_id,
            Activity.utl_score.is_(None)
        ).all()
        
        print(f'  Found {len(activities)} activities without UTL scores')
        
        updated_count = 0
        for activity in activities:
            try:
                # Prepare activity summary data (simplified)
                act_summary = {
                    'type': activity.type,
                    'moving_time': activity.moving_time,
                    'distance': activity.distance,
                    'average_speed': activity.average_speed,
                }
                
                # Calculate UTL (no detailed streams available for existing data)
                utl_score, method = calculate_utl(act_summary, threshold, None)
                
                if utl_score > 0:
                    activity.utl_score = utl_score
                    activity.calculation_method = method
                    updated_count += 1
                    
            except Exception as e:
                print(f'    Error calculating UTL for activity {activity.activity_id}: {e}')
                continue
        
        if updated_count > 0:
            db.commit()
            print(f'  Updated {updated_count} activities with UTL scores')
        else:
            print(f'  No activities updated')
            
    print('\\n✅ UTL calculation complete')
    
except Exception as e:
    print(f'❌ Error: {e}')
    db.rollback()
finally:
    db.close()
"
}

# Function to import recent Strava activities
import_recent_activities() {
    echo "📥 Importing recent Strava activities..."
    cd "$BACKEND_DIR"
    
    uv run python3 -c "
import sys
sys.path.append('.')

from activities import sync_strava_activities
import logging

logging.basicConfig(level=logging.INFO)

try:
    sync_strava_activities()
    print('✅ Strava activity sync complete')
except Exception as e:
    print(f'❌ Error syncing activities: {e}')
"
}

# Function to show data summary
show_data_summary() {
    echo "📊 Data Summary"
    cd "$BACKEND_DIR"
    
    uv run python3 -c "
import sys
sys.path.append('.')
from config import SessionLocal
from models import User, Activity, Threshold

db = SessionLocal()

try:
    # Users summary
    total_users = db.query(User).count()
    strava_users = db.query(User).filter(User.strava_user_id.isnot(None)).count()
    print(f'👥 Users: {total_users} total, {strava_users} with Strava')
    
    # Activities summary
    total_activities = db.query(Activity).count()
    activities_with_utl = db.query(Activity).filter(Activity.utl_score.isnot(None)).count()
    print(f'🏃 Activities: {total_activities} total, {activities_with_utl} with UTL scores')
    
    # Thresholds summary
    total_thresholds = db.query(Threshold).count()
    print(f'🎯 Thresholds: {total_thresholds} users with threshold data')
    
    # Recent activities
    from sqlalchemy import desc
    recent = db.query(Activity).order_by(desc(Activity.start_date)).limit(5).all()
    print(f'\\n📅 Recent Activities:')
    for act in recent:
        utl_info = f'UTL: {act.utl_score:.1f} ({act.calculation_method})' if act.utl_score else 'No UTL'
        print(f'  {act.start_date.strftime(\"%Y-%m-%d\") if act.start_date else \"Unknown\"}: {act.name} - {utl_info}')
        
finally:
    db.close()
"
}

# Parse command line arguments
case "${1:-}" in
    utl|--calculate-utl)
        calculate_utl_for_existing
        ;;
    sync|--sync-activities)
        import_recent_activities
        ;;
    summary|--summary)
        show_data_summary
        ;;
    all|--all)
        echo "🔧 Running complete data maintenance..."
        echo ""
        import_recent_activities
        echo ""
        calculate_utl_for_existing
        echo ""
        show_data_summary
        ;;
    *)
        echo "TrainingLoad Data Maintenance"
        echo ""
        echo "Usage: ./maintenance.sh [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  utl      Calculate UTL scores for existing activities"
        echo "  sync     Import recent Strava activities"
        echo "  summary  Show data summary"
        echo "  all      Run sync + UTL calculation + summary"
        echo ""
        echo "Examples:"
        echo "  ./maintenance.sh all     # Complete data refresh"
        echo "  ./maintenance.sh utl     # Just calculate UTL scores"
        echo "  ./maintenance.sh summary # Show current data status"
        echo ""
        ;;
esac
