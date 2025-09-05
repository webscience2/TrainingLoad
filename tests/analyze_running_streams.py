#!/usr/bin/env python3
"""
Analyze detailed speed/pace streams from running activities to find true threshold pace.
"""

import sys
import os
sys.path.append('/Users/adam/src/TrainingLoad/backend')

from config import engine
from sqlalchemy import text
import json

def analyze_running_streams():
    """Analyze detailed speed streams to find best threshold pace efforts."""
    
    try:
        print('🏃 ANALYZING DETAILED RUNNING STREAMS')
        print('=' * 42)
        
        with engine.connect() as conn:
            # Get running activities with streams data
            result = conn.execute(text("""
                SELECT a.name, a.type, a.moving_time, a.distance,
                       a.average_speed, a.max_speed, a.start_date,
                       CASE 
                         WHEN a.data::json->'streams' IS NOT NULL THEN 'Yes'
                         ELSE 'No'
                       END as has_streams,
                       CASE 
                         WHEN a.data::json->'streams'->'velocity_smooth' IS NOT NULL THEN 'Yes'
                         ELSE 'No'
                       END as has_speed_stream
                FROM activities a
                WHERE a.type IN ('Run', 'VirtualRun')
                  AND a.average_speed > 1  -- Valid running speeds
                  AND a.moving_time > 1200  -- At least 20 minutes
                ORDER BY a.start_date DESC
                LIMIT 15
            """))
            
            running_activities = result.fetchall()
            
            print('Running activities with streams status:')
            print('Name                              | Date       | Distance | Avg Pace | Streams | Speed Stream')
            print('-' * 95)
            
            activities_with_speed_streams = []
            
            for activity in running_activities:
                name, sport, time, distance, avg_speed, max_speed, date, has_streams, has_speed_stream = activity
                distance_km = distance / 1000 if distance else 0
                avg_pace_km = (1000 / avg_speed) / 60 if avg_speed else 0
                
                print(f'{name[:32]:32} | {date.strftime("%Y-%m-%d")} | {distance_km:6.1f}km | {avg_pace_km:4.1f}min/km | {has_streams:7} | {has_speed_stream}')
                
                if has_speed_stream == 'Yes':
                    activities_with_speed_streams.append(activity)
            
            if not activities_with_speed_streams:
                print('\n❌ No running activities found with detailed speed streams')
                return
            
            print(f'\n🎯 Found {len(activities_with_speed_streams)} running activities with speed streams!')
            print('Analyzing best sustained pace efforts from each...')
            print()
            
            best_threshold_efforts = []
            
            for activity in activities_with_speed_streams:
                name, sport, time, distance, avg_speed, max_speed, date, has_streams, has_speed_stream = activity
                
                print(f'Analyzing: {name[:40]}...')
                
                # Get the detailed streams data
                result = conn.execute(text("""
                    SELECT a.data::json->'streams' as streams_data
                    FROM activities a
                    WHERE a.name = :name AND a.start_date = :date
                """), {"name": name, "date": date})
                
                stream_result = result.fetchone()
                if stream_result and stream_result[0]:
                    streams = stream_result[0]
                    
                    # Check available streams
                    available_streams = list(streams.keys())
                    speed_stream = None
                    
                    if 'velocity_smooth' in streams:
                        speed_stream = streams['velocity_smooth']['data']
                    elif 'velocity' in streams:
                        speed_stream = streams['velocity']['data']
                    
                    if speed_stream and len(speed_stream) >= 1200:  # At least 20 minutes
                        # Analyze different time intervals for threshold estimation
                        intervals = {
                            '20-min': 1200,  # Classic threshold test
                            '15-min': 900,   # Shorter threshold effort
                            '10-min': 600,   # Tempo/threshold
                            '5-min': 300     # VO2 max effort
                        }
                        
                        interval_results = {}
                        
                        for interval_name, seconds in intervals.items():
                            if len(speed_stream) >= seconds:
                                best_speed = calculate_best_sustained_speed(speed_stream, seconds)
                                best_pace_km = (1000 / best_speed) / 60 if best_speed > 0 else 0
                                interval_results[interval_name] = {
                                    'speed': best_speed,
                                    'pace_km': best_pace_km,
                                    'pace_mile': (1609.34 / best_speed) / 60 if best_speed > 0 else 0
                                }
                        
                        # Estimate threshold from different efforts
                        threshold_estimates = []
                        
                        if '20-min' in interval_results:
                            # 20-minute effort is close to threshold
                            threshold_estimates.append(interval_results['20-min']['speed'])
                            
                        if '15-min' in interval_results:
                            # 15-minute effort is slightly above threshold
                            threshold_estimates.append(interval_results['15-min']['speed'] * 0.98)
                            
                        if '10-min' in interval_results:
                            # 10-minute effort is above threshold (tempo/sweet spot)
                            threshold_estimates.append(interval_results['10-min']['speed'] * 0.95)
                        
                        if threshold_estimates:
                            # Use the most conservative estimate
                            estimated_threshold_speed = min(threshold_estimates)
                            estimated_threshold_pace = (1000 / estimated_threshold_speed) / 60
                            
                            best_threshold_efforts.append((
                                name, date, estimated_threshold_speed, estimated_threshold_pace, interval_results
                            ))
                            
                            print(f'  Best sustained efforts:')
                            for interval, data in interval_results.items():
                                print(f'    {interval:8}: {data["pace_km"]:.1f}min/km ({data["pace_mile"]:.1f}min/mi) - {data["speed"]:.2f}m/s')
                            print(f'  💪 Estimated threshold: {estimated_threshold_pace:.1f}min/km ({estimated_threshold_speed:.2f}m/s)')
                            print()
                    else:
                        print(f'  ❌ Insufficient speed stream data')
                else:
                    print(f'  ❌ No streams data found')
            
            if best_threshold_efforts:
                # Find the best threshold efforts
                best_threshold_efforts.sort(key=lambda x: x[2], reverse=True)  # Sort by speed (fastest first)
                
                print('🏆 BEST RUNNING THRESHOLD ANALYSIS')
                print('=' * 40)
                
                print('Top threshold pace efforts:')
                for i, (name, date, speed, pace, intervals) in enumerate(best_threshold_efforts[:5]):
                    pace_mile = (1609.34 / speed) / 60
                    print(f'{i+1}. {name[:35]:35} | {pace:.1f}min/km ({pace_mile:.1f}min/mi) | {speed:.2f}m/s | {date.strftime("%Y-%m-%d")}')
                
                # Best effort analysis
                best_effort = best_threshold_efforts[0]
                best_speed = best_effort[2]
                best_pace = best_effort[3]
                best_pace_mile = (1609.34 / best_speed) / 60
                
                print()
                print(f'🎯 RECOMMENDED RUNNING THRESHOLD')
                print(f'Activity: {best_effort[0]}')
                print(f'Date: {best_effort[1].strftime("%Y-%m-%d")}')
                print(f'Threshold Speed (FTHP): {best_speed:.2f} m/s')
                print(f'Threshold Pace: {best_pace:.1f} min/km ({best_pace_mile:.1f} min/mile)')
                
                # Compare with current threshold
                result = conn.execute(text("""
                    SELECT t.fthp_mps
                    FROM thresholds t
                    JOIN users u ON t.user_id = u.user_id
                    WHERE u.email LIKE '%adam%'
                    ORDER BY t.date_updated DESC
                    LIMIT 1
                """))
                
                current_threshold = result.fetchone()
                if current_threshold and current_threshold[0]:
                    current_fthp = current_threshold[0]
                    current_pace = (1000 / current_fthp) / 60
                    current_pace_mile = (1609.34 / current_fthp) / 60
                    
                    difference_speed = best_speed - current_fthp
                    difference_pace = current_pace - best_pace  # Pace difference (lower is faster)
                    
                    print()
                    print(f'Current FTHP: {current_fthp:.2f} m/s ({current_pace:.1f} min/km, {current_pace_mile:.1f} min/mile)')
                    print(f'Recommended FTHP: {best_speed:.2f} m/s ({best_pace:.1f} min/km, {best_pace_mile:.1f} min/mile)')
                    
                    if difference_speed > 0.2:  # 0.2 m/s is significant
                        print(f'🚨 MAJOR UNDERESTIMATE: Current pace is {difference_pace:.1f}min/km too slow!')
                        print(f'   Speed increase needed: {difference_speed:.2f} m/s')
                    elif difference_speed > 0.1:
                        print(f'⚠️  SIGNIFICANT UNDERESTIMATE: Current pace is {difference_pace:.1f}min/km too slow')
                    elif difference_speed > 0.05:
                        print(f'📈 UNDERESTIMATE: Current pace is {difference_pace:.1f}min/km too slow')
                    else:
                        print(f'✅ Current threshold seems reasonable')
                
                # Additional analysis - recent form
                print()
                print('📊 RECENT FORM ANALYSIS')
                print('=' * 25)
                
                recent_efforts = [effort for effort in best_threshold_efforts if effort[1] > (date - timedelta(days=60))]
                if len(recent_efforts) >= 3:
                    recent_avg_speed = sum(effort[2] for effort in recent_efforts[:3]) / 3
                    recent_avg_pace = (1000 / recent_avg_speed) / 60
                    print(f'Recent form (last 60 days): {recent_avg_pace:.1f} min/km average threshold')
                    
                    if recent_avg_speed > current_fthp * 1.05:
                        print('✅ Recent performances support threshold increase')
                    else:
                        print('⚠️  Recent performances suggest maintaining current threshold')

    except Exception as e:
        print(f'Error analyzing running streams: {e}')
        import traceback
        traceback.print_exc()

def calculate_best_sustained_speed(speed_data, duration_seconds):
    """Calculate the best sustained speed over a given duration."""
    if len(speed_data) < duration_seconds:
        return 0
    
    best_speed = 0
    
    # Sliding window to find best sustained pace
    for i in range(len(speed_data) - duration_seconds + 1):
        window_speeds = speed_data[i:i + duration_seconds]
        # Remove zeros and outliers
        valid_speeds = [s for s in window_speeds if 1 < s < 10]  # Reasonable running speeds
        
        if len(valid_speeds) > duration_seconds * 0.8:  # At least 80% valid data
            avg_speed = sum(valid_speeds) / len(valid_speeds)
            if avg_speed > best_speed:
                best_speed = avg_speed
    
    return best_speed

if __name__ == "__main__":
    from datetime import timedelta, datetime
    analyze_running_streams()
