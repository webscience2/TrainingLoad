#!/usr/bin/env python3
"""
Debug running threshold calculation
"""

import sys
import os
sys.path.append('/Users/adam/src/TrainingLoad/backend')

from config import engine
from sqlalchemy import text
import json
import logging

logging.basicConfig(level=logging.INFO)

def debug_running_streams():
    """Debug why running threshold calculation is returning 0.00"""
    print('🔍 DEBUGGING RUNNING THRESHOLD CALCULATION')
    print('=' * 50)
    
    try:
        with engine.connect() as conn:
            # Check what running activities we have with streams
            result = conn.execute(text("""
                SELECT a.strava_activity_id, a.type, a.moving_time, a.distance, 
                       a.average_speed, a.data::json->'streams' as streams_data
                FROM activities a
                WHERE a.user_id = 1
                  AND a.type IN ('Run', 'VirtualRun')
                  AND a.data IS NOT NULL
                  AND a.data::json->'streams' IS NOT NULL
                  AND a.moving_time > 600  -- At least 10 minutes
                ORDER BY a.start_date DESC
                LIMIT 3
            """))
            
            activities = result.fetchall()
            
            if not activities:
                print('❌ No running activities with streams found')
                return
                
            for activity in activities:
                activity_id, activity_type, moving_time, distance, avg_speed, streams_data = activity
                
                print(f'\n📊 Activity {activity_id} ({activity_type})')
                print(f'  Duration: {moving_time}s ({moving_time/60:.1f} min)')
                print(f'  Distance: {distance}m ({distance/1000:.1f}km)')
                print(f'  Avg Speed: {avg_speed:.2f} m/s' if avg_speed else 'No avg speed')
                
                if streams_data:
                    print(f'  Available streams: {list(streams_data.keys())}')
                    
                    if 'velocity_smooth' in streams_data:
                        velocity_data = streams_data['velocity_smooth']['data']
                        if velocity_data:
                            print(f'  Velocity data points: {len(velocity_data)}')
                            print(f'  Velocity range: {min(velocity_data):.2f} - {max(velocity_data):.2f} m/s')
                            
                            # Check for zero values which might cause issues
                            zero_count = sum(1 for v in velocity_data if v <= 0.1)
                            print(f'  Zero/very low velocity points: {zero_count}/{len(velocity_data)} ({zero_count/len(velocity_data)*100:.1f}%)')
                            
                        else:
                            print('  ❌ Velocity data is empty')
                    else:
                        print('  ❌ No velocity_smooth data in streams')
                        
                else:
                    print('  ❌ No streams data')
    
    except Exception as e:
        print(f'❌ Error debugging running streams: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_running_streams()
