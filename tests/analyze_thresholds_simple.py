#!/usr/bin/env python3
"""
Analyze running thresholds and cycling FTP values to identify issues.
"""

import sys
import os
sys.path.append('/Users/adam/src/TrainingLoad/backend')

from config import engine
from sqlalchemy import text

def analyze_thresholds():
    """Analyze current running and cycling thresholds."""
    
    try:
        print('🏃 RUNNING THRESHOLDS ANALYSIS')
        print('=' * 40)
        
        with engine.connect() as conn:
            # Check running thresholds
            result = conn.execute(text("""
                SELECT u.email, t.fthp_mps, t.max_hr, t.resting_hr, t.date_updated
                FROM thresholds t
                JOIN users u ON t.user_id = u.user_id
                WHERE t.fthp_mps IS NOT NULL
                ORDER BY t.date_updated DESC
            """))
            
            running_thresholds = result.fetchall()
            if running_thresholds:
                for row in running_thresholds:
                    email, fthp_mps, max_hr, resting_hr, date = row
                    if fthp_mps:
                        # Convert m/s to pace (min/mile and min/km)
                        pace_per_mile = (1609.34 / fthp_mps) / 60  # min/mile
                        pace_per_km = (1000 / fthp_mps) / 60       # min/km
                        print(f'{email[:20]:20} | FTHP: {fthp_mps:.2f} m/s | '
                              f'Pace: {pace_per_mile:.1f}min/mi ({pace_per_km:.1f}min/km) | '
                              f'HR: {resting_hr}-{max_hr}')
            else:
                print('❌ No running thresholds found')
            
            print()
            print('🚴 CYCLING FTP ANALYSIS')
            print('=' * 30)
            
            # Check cycling FTP values
            result = conn.execute(text("""
                SELECT u.email, t.ftp_watts, t.max_hr, t.resting_hr, t.date_updated
                FROM thresholds t
                JOIN users u ON t.user_id = u.user_id
                WHERE t.ftp_watts IS NOT NULL
                ORDER BY t.date_updated DESC
            """))
            
            cycling_thresholds = result.fetchall()
            if cycling_thresholds:
                for row in cycling_thresholds:
                    email, ftp_watts, max_hr, resting_hr, date = row
                    # Typical FTP ranges
                    if ftp_watts < 100:
                        fitness_level = 'Very Low'
                    elif ftp_watts < 150:
                        fitness_level = 'Beginner'
                    elif ftp_watts < 200:
                        fitness_level = 'Recreational'
                    elif ftp_watts < 250:
                        fitness_level = 'Competitive'
                    elif ftp_watts < 300:
                        fitness_level = 'Advanced'
                    else:
                        fitness_level = 'Elite'
                    
                    print(f'{email[:20]:20} | FTP: {ftp_watts:.0f}W ({fitness_level:12}) | '
                          f'HR: {resting_hr}-{max_hr} | {date}')
            else:
                print('❌ No cycling FTP values found')
            
            print()
            print('📊 RECENT CYCLING ACTIVITIES WITH POWER')
            print('=' * 45)
            
            # Check recent cycling activities with power data
            result = conn.execute(text("""
                SELECT a.name, a.type, a.moving_time, 
                       (a.data::json->>'average_watts')::float as avg_watts,
                       (a.data::json->>'max_watts')::float as max_watts,
                       (a.data::json->>'weighted_average_watts')::float as norm_power,
                       a.start_date
                FROM activities a
                WHERE a.type IN ('Ride', 'VirtualRide')
                  AND a.data::json->'average_watts' IS NOT NULL
                  AND (a.data::json->>'average_watts')::float > 0
                ORDER BY a.start_date DESC
                LIMIT 15
            """))
            
            power_activities = result.fetchall()
            if power_activities:
                for row in power_activities:
                    name, sport, time, avg_watts, max_watts, norm_power, date = row
                    duration_min = time / 60 if time else 0
                    avg_w = avg_watts if avg_watts else 0
                    max_w = max_watts if max_watts else 0
                    np_str = f', NP: {norm_power:.0f}W' if norm_power else ''
                    print(f'  {name[:35]:35} | {avg_w:3.0f}W avg, {max_w:3.0f}W max{np_str} | '
                          f'{duration_min:.0f}min | {date.strftime("%Y-%m-%d")}')
            else:
                print('❌ No recent cycling activities with power found')
            
            print()
            print('🏃 RECENT RUNNING ACTIVITIES')
            print('=' * 32)
            
            # Check recent running activities
            result = conn.execute(text("""
                SELECT a.name, a.type, a.moving_time, a.distance,
                       a.average_speed, a.max_speed,
                       a.start_date
                FROM activities a  
                WHERE a.type IN ('Run', 'VirtualRun')
                  AND a.average_speed IS NOT NULL
                  AND a.average_speed > 0
                ORDER BY a.start_date DESC
                LIMIT 15
            """))
            
            running_activities = result.fetchall()
            if running_activities:
                for row in running_activities:
                    name, sport, time, distance, avg_speed, max_speed, date = row
                    if avg_speed and distance and time:
                        pace_per_km = (1000 / avg_speed) / 60  # min/km
                        pace_per_mile = (1609.34 / avg_speed) / 60  # min/mile
                        distance_km = distance / 1000
                        max_pace_km = (1000 / max_speed) / 60 if max_speed else 0
                        print(f'  {name[:35]:35} | {distance_km:.1f}km | '
                              f'{pace_per_km:.1f}min/km ({pace_per_mile:.1f}min/mi) | '
                              f'Best: {max_pace_km:.1f}min/km | {date.strftime("%Y-%m-%d")}')
            else:
                print('❌ No recent running activities found')
            
            print()
            print('🔍 THRESHOLD ESTIMATION ANALYSIS')
            print('=' * 35)
            
            # Analyze power distribution for FTP estimation
            result = conn.execute(text("""
                SELECT 
                    AVG((a.data::json->>'average_watts')::float) as avg_avg_watts,
                    MAX((a.data::json->>'average_watts')::float) as max_avg_watts,
                    COUNT(*) as ride_count,
                    -- Get some specific high-intensity efforts
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY (a.data::json->>'average_watts')::float) as p95_watts,
                    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY (a.data::json->>'average_watts')::float) as p90_watts
                FROM activities a
                WHERE a.type IN ('Ride', 'VirtualRide')
                  AND a.data::json->'average_watts' IS NOT NULL
                  AND (a.data::json->>'average_watts')::float > 50
                  AND a.moving_time > 1800  -- At least 30 minutes
                  AND a.start_date > CURRENT_DATE - INTERVAL '90 days'
            """))
            
            power_stats = result.fetchone()
            if power_stats and power_stats[0]:
                avg_avg_watts, max_avg_watts, ride_count, p95_watts, p90_watts = power_stats
                estimated_ftp_conservative = p90_watts * 0.95 if p90_watts else avg_avg_watts * 1.05
                estimated_ftp_aggressive = p95_watts * 0.95 if p95_watts else max_avg_watts * 0.95
                
                print(f'Power Analysis (last 90 days):')
                print(f'  • {ride_count} rides > 30 minutes')
                print(f'  • Average power across rides: {avg_avg_watts:.0f}W')
                print(f'  • 90th percentile power: {p90_watts:.0f}W')
                print(f'  • 95th percentile power: {p95_watts:.0f}W')
                print(f'  • Estimated FTP range: {estimated_ftp_conservative:.0f}W - {estimated_ftp_aggressive:.0f}W')
                
                # Compare with current FTP
                if cycling_thresholds:
                    current_ftp = cycling_thresholds[0][1]  # First user's FTP
                    if current_ftp:
                        print(f'  • Current FTP: {current_ftp:.0f}W')
                        
                        # Check if current FTP is reasonable
                        if current_ftp < estimated_ftp_conservative * 0.8:
                            print(f'  ⚠️  Current FTP seems TOO LOW (increase by ~{estimated_ftp_conservative - current_ftp:.0f}W)')
                        elif current_ftp > estimated_ftp_aggressive * 1.1:
                            print(f'  ⚠️  Current FTP seems TOO HIGH (reduce by ~{current_ftp - estimated_ftp_aggressive:.0f}W)')
                        else:
                            print(f'  ✅ Current FTP seems reasonable')
            
            # Analyze running pace distribution for threshold estimation
            result = conn.execute(text("""
                SELECT 
                    AVG(a.average_speed) as avg_speed,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY a.average_speed) as p95_speed,
                    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY a.average_speed) as p90_speed,
                    COUNT(*) as run_count
                FROM activities a
                WHERE a.type IN ('Run', 'VirtualRun')
                  AND a.average_speed IS NOT NULL
                  AND a.average_speed > 1
                  AND a.moving_time > 1200  -- At least 20 minutes
                  AND a.start_date > CURRENT_DATE - INTERVAL '90 days'
            """))
            
            pace_stats = result.fetchone()
            if pace_stats and pace_stats[0]:
                avg_speed, p95_speed, p90_speed, run_count = pace_stats
                avg_pace_km = (1000 / avg_speed) / 60
                
                # Threshold pace estimation (typically 3-8% faster than average training pace)
                estimated_threshold_speed_conservative = p90_speed * 1.03  # 3% faster than 90th percentile
                estimated_threshold_speed_aggressive = p95_speed * 1.01    # 1% faster than 95th percentile
                
                threshold_pace_conservative = (1000 / estimated_threshold_speed_conservative) / 60
                threshold_pace_aggressive = (1000 / estimated_threshold_speed_aggressive) / 60
                
                print(f'\nRunning Analysis (last 90 days):')
                print(f'  • {run_count} runs > 20 minutes')
                print(f'  • Average pace: {avg_pace_km:.1f} min/km')
                print(f'  • 90th percentile speed: {(1000 / p90_speed) / 60:.1f} min/km')
                print(f'  • 95th percentile speed: {(1000 / p95_speed) / 60:.1f} min/km')
                print(f'  • Estimated threshold pace: {threshold_pace_conservative:.1f} - {threshold_pace_aggressive:.1f} min/km')
                print(f'  • Estimated FTHP: {estimated_threshold_speed_conservative:.2f} - {estimated_threshold_speed_aggressive:.2f} m/s')
                
                # Compare with current threshold
                if running_thresholds:
                    current_fthp = running_thresholds[0][1]  # First user's FTHP
                    if current_fthp:
                        current_pace_km = (1000 / current_fthp) / 60
                        print(f'  • Current FTHP: {current_fthp:.2f} m/s ({current_pace_km:.1f} min/km)')
                        
                        # Check if current threshold is reasonable
                        if current_fthp < estimated_threshold_speed_conservative * 0.95:
                            print(f'  ⚠️  Current threshold pace seems TOO SLOW')
                        elif current_fthp > estimated_threshold_speed_aggressive * 1.05:
                            print(f'  ⚠️  Current threshold pace seems TOO FAST')
                        else:
                            print(f'  ✅ Current threshold pace seems reasonable')

    except Exception as e:
        print(f'Error analyzing thresholds: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_thresholds()
