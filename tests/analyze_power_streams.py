#!/usr/bin/env python3
"""
Analyze detailed power streams from Strava data to find true 20-minute power.
"""

import sys
import os
sys.path.append('/Users/adam/src/TrainingLoad/backend')
sys.path.append('/Users/adam/src/TrainingLoad')

from config import engine
from sqlalchemy import text
import json

def analyze_power_streams():
    """Analyze detailed power streams to find best 20-minute power."""
    
    try:
        print('🔍 ANALYZING DETAILED POWER STREAMS')
        print('=' * 40)
        
        with engine.connect() as conn:
            # Find the specific Zwift Road to Sky activity
            result = conn.execute(text("""
                SELECT a.name, a.type, a.moving_time, 
                       (a.data::json->>'average_watts')::float as avg_watts,
                       (a.data::json->>'max_watts')::float as max_watts,
                       a.start_date, a.data::json as full_data
                FROM activities a
                WHERE a.name ILIKE '%Road to Sky in Watopia%'
                ORDER BY a.start_date DESC
                LIMIT 1
            """))
            
            road_to_sky = result.fetchone()
            if not road_to_sky:
                print('❌ Road to Sky activity not found')
                return
                
            name, sport, time, avg_watts, max_watts, date, full_data = road_to_sky
            print(f'Found: {name}')
            print(f'Date: {date}')
            print(f'Duration: {time/60:.0f} minutes')
            print(f'Average Power: {avg_watts:.0f}W')
            print(f'Max Power: {max_watts:.0f}W')
            print()
            
            # Check if we have streams data
            if 'streams' in full_data:
                streams = full_data['streams']
                print('Available streams:')
                for stream_name in streams.keys():
                    print(f'  - {stream_name}')
                print()
                
                # Analyze power stream if available
                if 'watts' in streams:
                    power_data = streams['watts']['data']
                    print(f'Power stream has {len(power_data)} data points')
                    
                    # Calculate 20-minute best power (1200 seconds)
                    if len(power_data) >= 1200:
                        best_20_min_power = calculate_best_20_min_power(power_data)
                        print(f'🎯 BEST 20-MINUTE POWER: {best_20_min_power:.0f}W')
                        print(f'🎯 ESTIMATED FTP (95%): {best_20_min_power * 0.95:.0f}W')
                        print()
                        
                        # Show power distribution
                        analyze_power_distribution(power_data, time)
                    else:
                        print('⚠️  Ride too short for 20-minute analysis')
                else:
                    print('❌ No power stream data available')
            else:
                print('❌ No streams data available in activity')
            
            print()
            print('🔍 CHECKING OTHER ACTIVITIES FOR STREAMS')
            print('=' * 45)
            
            # Check what activities have streams data
            result = conn.execute(text("""
                SELECT a.name, a.type, a.moving_time, 
                       (a.data::json->>'average_watts')::float as avg_watts,
                       a.start_date,
                       CASE 
                         WHEN a.data::json->'streams' IS NOT NULL THEN 'Yes'
                         ELSE 'No'
                       END as has_streams,
                       CASE 
                         WHEN a.data::json->'streams'->'watts' IS NOT NULL THEN 'Yes'
                         ELSE 'No'
                       END as has_power_stream
                FROM activities a
                WHERE a.type IN ('Ride', 'VirtualRide')
                  AND (a.data::json->>'average_watts')::float > 100
                  AND a.moving_time > 1800  -- At least 30 minutes
                ORDER BY a.start_date DESC
                LIMIT 15
            """))
            
            activities_with_streams = result.fetchall()
            print('Recent activities with streams status:')
            print('Name                              | Date       | Duration | Avg W | Streams | Power Stream')
            print('-' * 90)
            
            for activity in activities_with_streams:
                name, sport, time, avg_watts, date, has_streams, has_power_stream = activity
                duration_min = time / 60 if time else 0
                avg_w = avg_watts if avg_watts else 0
                print(f'{name[:32]:32} | {date.strftime("%Y-%m-%d")} | {duration_min:3.0f}min   | {avg_w:3.0f}W | {has_streams:7} | {has_power_stream}')
            
            # Find activities with power streams for detailed analysis
            activities_with_power = [a for a in activities_with_streams if a[6] == 'Yes']
            
            if activities_with_power:
                print(f'\n🎯 Found {len(activities_with_power)} activities with power streams!')
                print('Analyzing best 20-minute efforts from each...')
                
                best_20_min_efforts = []
                
                for activity in activities_with_power[:5]:  # Analyze top 5
                    name, sport, time, avg_watts, date, has_streams, has_power_stream = activity
                    
                    # Get the detailed streams data
                    result = conn.execute(text("""
                        SELECT a.data::json->'streams'->'watts'->'data' as power_stream
                        FROM activities a
                        WHERE a.name = :name AND a.start_date = :date
                    """), {"name": name, "date": date})
                    
                    stream_result = result.fetchone()
                    if stream_result and stream_result[0]:
                        power_data = stream_result[0]
                        if len(power_data) >= 1200:  # At least 20 minutes of data
                            best_20_min = calculate_best_20_min_power(power_data)
                            best_20_min_efforts.append((name, date, best_20_min))
                            print(f'  {name[:35]:35} | {best_20_min:.0f}W (20-min best)')
                
                if best_20_min_efforts:
                    # Find the absolute best 20-minute effort
                    best_effort = max(best_20_min_efforts, key=lambda x: x[2])
                    best_power = best_effort[2]
                    
                    print()
                    print('🏆 BEST 20-MINUTE POWER ANALYSIS')
                    print('=' * 35)
                    print(f'Best effort: {best_effort[0]}')
                    print(f'Date: {best_effort[1].strftime("%Y-%m-%d")}')
                    print(f'20-minute power: {best_power:.0f}W')
                    print(f'Estimated FTP (95%): {best_power * 0.95:.0f}W')
                    print(f'Estimated FTP (93%): {best_power * 0.93:.0f}W')  # Some use 93%
                    
                    # Compare with current FTP
                    result = conn.execute(text("""
                        SELECT t.ftp_watts
                        FROM thresholds t
                        JOIN users u ON t.user_id = u.user_id
                        WHERE u.email LIKE '%adam%'
                        ORDER BY t.date_updated DESC
                        LIMIT 1
                    """))
                    
                    current_ftp = result.fetchone()
                    if current_ftp and current_ftp[0]:
                        current = current_ftp[0]
                        recommended = best_power * 0.95
                        difference = recommended - current
                        
                        print()
                        print(f'Current FTP: {current:.0f}W')
                        print(f'Recommended FTP: {recommended:.0f}W')
                        
                        if difference > 30:
                            print(f'🚨 MAJOR UNDERESTIMATE: {difference:.0f}W too low!')
                        elif difference > 15:
                            print(f'⚠️  SIGNIFICANT UNDERESTIMATE: {difference:.0f}W too low')
                        elif difference > 5:
                            print(f'📈 UNDERESTIMATE: {difference:.0f}W too low')
                        else:
                            print(f'✅ Current FTP seems reasonable')
            else:
                print('\n❌ No activities found with detailed power streams')
                print('This suggests we need to update the Strava data fetching to include streams')

    except Exception as e:
        print(f'Error analyzing power streams: {e}')
        import traceback
        traceback.print_exc()

def calculate_best_20_min_power(power_data):
    """Calculate the best 20-minute average power from power stream data."""
    if len(power_data) < 1200:  # Less than 20 minutes
        return 0
    
    best_power = 0
    window_size = 1200  # 20 minutes at 1Hz
    
    # Sliding window to find best 20-minute segment
    for i in range(len(power_data) - window_size + 1):
        window_power = power_data[i:i + window_size]
        avg_power = sum(window_power) / len(window_power)
        if avg_power > best_power:
            best_power = avg_power
    
    return best_power

def analyze_power_distribution(power_data, total_time):
    """Analyze power distribution for the activity."""
    if not power_data:
        return
    
    power_data_sorted = sorted([p for p in power_data if p > 0], reverse=True)
    total_points = len(power_data_sorted)
    
    # Power percentiles
    percentiles = {
        95: power_data_sorted[int(total_points * 0.05)],
        90: power_data_sorted[int(total_points * 0.10)],
        75: power_data_sorted[int(total_points * 0.25)],
        50: power_data_sorted[int(total_points * 0.50)]
    }
    
    print('Power Distribution:')
    for pct, power in percentiles.items():
        print(f'  {pct}th percentile: {power:.0f}W')
    
    # Time in zones (rough estimates)
    max_power = max(power_data)
    zones = {
        'Zone 5 (>120% FTP)': len([p for p in power_data if p > max_power * 0.8]),
        'Zone 4 (106-120% FTP)': len([p for p in power_data if max_power * 0.7 < p <= max_power * 0.8]),
        'Zone 3 (90-105% FTP)': len([p for p in power_data if max_power * 0.6 < p <= max_power * 0.7]),
    }
    
    print('Time in High Intensity Zones:')
    for zone, seconds in zones.items():
        minutes = seconds / 60
        print(f'  {zone}: {minutes:.1f} minutes')

if __name__ == "__main__":
    analyze_power_streams()
