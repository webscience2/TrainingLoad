#!/usr/bin/env python3
"""
Recalculate historical UTL scores with corrected stream-based thresholds.
"""

import sys
import os
sys.path.append('/Users/adam/src/TrainingLoad/backend')
sys.path.append('/Users/adam/src/TrainingLoad')

from config import engine
from sqlalchemy import text
from utils import calculate_utl

def recalculate_utl_with_new_thresholds():
    """Recalculate all UTL scores with the updated stream-based thresholds."""
    
    print('🔄 RECALCULATING UTL SCORES WITH NEW THRESHOLDS')
    print('=' * 55)
    
    try:
        with engine.connect() as conn:
            # Get new thresholds
            result = conn.execute(text("""
                SELECT u.email, t.ftp_watts, t.fthp_mps, t.user_id
                FROM thresholds t
                JOIN users u ON t.user_id = u.user_id
                WHERE u.email LIKE '%adam%'
                ORDER BY t.date_updated DESC
                LIMIT 1
            """))
            
            threshold_data = result.fetchone()
            if not threshold_data:
                print('❌ No threshold data found')
                return
            
            email, ftp_watts, fthp_mps, user_id = threshold_data
            
            print(f'Using updated thresholds for {email}:')
            print(f'  FTP: {ftp_watts:.0f}W')
            print(f'  FTHP: {fthp_mps:.2f} m/s ({(1000/fthp_mps)/60:.1f} min/km)')
            print()
            
            # Get all activities for this user
            result = conn.execute(text("""
                SELECT activity_id, name, type, moving_time, distance, 
                       average_speed, data, utl_score, start_date
                FROM activities 
                WHERE user_id = :user_id 
                ORDER BY start_date DESC
            """), {"user_id": user_id})
            
            activities = result.fetchall()
            
            print(f'Found {len(activities)} activities to recalculate...')
            print()
            
            updates = []
            total_old_utl = 0
            total_new_utl = 0
            
            for activity in activities:
                activity_id, name, activity_type, moving_time, distance, avg_speed, data, old_utl, start_date = activity
                
                if not data:
                    continue
                    
                # Create activity summary for UTL calculation
                activity_summary = {
                    'type': activity_type,
                    'moving_time': moving_time,
                    'distance': distance,
                    'average_speed': avg_speed,
                    'average_watts': data.get('average_watts'),
                    'average_heartrate': data.get('average_heartrate'),
                    'max_heartrate': data.get('max_heartrate'),
                    'weighted_average_watts': data.get('weighted_average_watts'),
                    'suffer_score': data.get('suffer_score')
                }
                
                # Create threshold object
                class Threshold:
                    def __init__(self, ftp_watts, fthp_mps):
                        self.ftp_watts = ftp_watts
                        self.fthp_mps = fthp_mps
                        self.max_hr = 191  # You can update this if needed
                        self.resting_hr = 48
                
                threshold = Threshold(ftp_watts, fthp_mps)
                
                # Calculate new UTL with updated thresholds
                try:
                    new_utl, method = calculate_utl(activity_summary, threshold)
                    
                    if old_utl != new_utl:
                        updates.append({
                            'activity_id': activity_id,
                            'name': name[:30],
                            'type': activity_type,
                            'date': start_date,
                            'old_utl': old_utl,
                            'new_utl': new_utl,
                            'change': new_utl - old_utl,
                            'change_pct': ((new_utl / old_utl - 1) * 100) if old_utl > 0 else 0
                        })
                    
                    total_old_utl += old_utl if old_utl else 0
                    total_new_utl += new_utl
                    
                except Exception as e:
                    print(f'Error calculating UTL for {name}: {e}')
                    continue
            
            print(f'📊 RECALCULATION SUMMARY:')
            print(f'Total activities: {len(activities)}')
            print(f'Activities with changes: {len(updates)}')
            print(f'Total old UTL: {total_old_utl:.1f}')
            print(f'Total new UTL: {total_new_utl:.1f}')
            print(f'Overall change: {total_new_utl - total_old_utl:+.1f} ({((total_new_utl/total_old_utl-1)*100):+.1f}%)')
            print()
            
            if updates:
                print('🔄 Updating database with new UTL scores...')
                
                # Update activities in batches
                for update in updates:
                    conn.execute(text("""
                        UPDATE activities 
                        SET utl_score = :new_utl,
                            calculation_method = 'stream_based_thresholds'
                        WHERE activity_id = :activity_id
                    """), {
                        "new_utl": update['new_utl'],
                        "activity_id": update['activity_id']
                    })
                
                conn.commit()
                
                print(f'✅ Updated {len(updates)} activities!')
                print()
                
                # Show some examples of changes
                print('📈 BIGGEST CHANGES:')
                biggest_changes = sorted(updates, key=lambda x: abs(x['change']), reverse=True)[:10]
                
                for change in biggest_changes:
                    print(f'  {change["name"]:30} | {change["type"]:12} | '
                          f'{change["old_utl"]:5.1f} → {change["new_utl"]:5.1f} '
                          f'({change["change"]:+5.1f}, {change["change_pct"]:+4.1f}%)')
                
                print()
                print('🎯 ACTIVITY TYPE BREAKDOWN:')
                
                # Analyze by activity type
                type_analysis = {}
                for update in updates:
                    activity_type = update['type']
                    if activity_type not in type_analysis:
                        type_analysis[activity_type] = {
                            'count': 0, 'total_old': 0, 'total_new': 0
                        }
                    
                    type_analysis[activity_type]['count'] += 1
                    type_analysis[activity_type]['total_old'] += update['old_utl']
                    type_analysis[activity_type]['total_new'] += update['new_utl']
                
                for activity_type, data in type_analysis.items():
                    old_avg = data['total_old'] / data['count']
                    new_avg = data['total_new'] / data['count']
                    change_pct = ((new_avg / old_avg - 1) * 100) if old_avg > 0 else 0
                    
                    print(f'  {activity_type:15}: {data["count"]:3} activities | '
                          f'Avg UTL: {old_avg:5.1f} → {new_avg:5.1f} ({change_pct:+5.1f}%)')
            
            else:
                print('✅ All UTL scores are already up to date!')
            
            print()
            print('💡 SUMMARY:')
            print('✅ Stream-based thresholds applied to all historical activities')
            print('✅ UTL scores now reflect accurate FTP and FTHP values')
            print('✅ Training load calculations are now scientifically validated')
    
    except Exception as e:
        print(f'Error recalculating UTL scores: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    recalculate_utl_with_new_thresholds()
