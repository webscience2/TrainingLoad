#!/usr/bin/env python3
"""
Analyze 12 months of cycling data for proper FTP estimation using 20-minute power analysis.
"""

import sys
import os
sys.path.append('/Users/adam/src/TrainingLoad/backend')

from config import engine
from sqlalchemy import text
from datetime import datetime, timedelta

def analyze_ftp_12_months():
    """Analyze full 12 months of cycling data for FTP estimation."""
    
    try:
        print('🚴 COMPREHENSIVE CYCLING FTP ANALYSIS (12 MONTHS)')
        print('=' * 55)
        
        with engine.connect() as conn:
            # Get all cycling activities from the last 12 months with power data
            result = conn.execute(text("""
                SELECT a.name, a.type, a.moving_time, 
                       (a.data::json->>'average_watts')::float as avg_watts,
                       (a.data::json->>'max_watts')::float as max_watts,
                       (a.data::json->>'weighted_average_watts')::float as norm_power,
                       a.start_date, a.distance,
                       a.data::json as full_data
                FROM activities a
                WHERE a.type IN ('Ride', 'VirtualRide')
                  AND a.data::json->'average_watts' IS NOT NULL
                  AND (a.data::json->>'average_watts')::float > 50
                  AND a.moving_time > 1200  -- At least 20 minutes
                  AND a.start_date > CURRENT_DATE - INTERVAL '12 months'
                ORDER BY a.start_date DESC
            """))
            
            activities = result.fetchall()
            
            if not activities:
                print('❌ No cycling activities with power data found')
                return
                
            print(f'Found {len(activities)} cycling activities with power data (last 12 months)')
            print()
            
            # Analyze power distribution for better FTP estimation
            power_values = []
            best_20_min_estimates = []
            
            print('📊 DETAILED POWER ANALYSIS')
            print('=' * 30)
            
            for activity in activities:
                name, sport, time, avg_watts, max_watts, norm_power, date, distance, full_data = activity
                
                duration_min = time / 60 if time else 0
                avg_w = avg_watts if avg_watts else 0
                max_w = max_watts if max_watts else 0
                np_w = norm_power if norm_power else avg_w
                distance_km = distance / 1000 if distance else 0
                
                power_values.append(avg_w)
                
                # Estimate 20-minute power based on ride characteristics
                if duration_min >= 60:  # Long rides
                    # For longer rides, use normalized power as better FTP indicator
                    estimated_20min = np_w * 1.05 if np_w else avg_w * 1.05
                elif duration_min >= 45:  # Medium rides
                    estimated_20min = np_w * 1.02 if np_w else avg_w * 1.02
                elif duration_min >= 20:  # Short hard efforts
                    estimated_20min = avg_w * 0.98  # Likely closer to threshold
                else:
                    estimated_20min = avg_w * 0.95  # Very short, probably above threshold
                
                best_20_min_estimates.append(estimated_20min)
                
                print(f'{date.strftime("%Y-%m-%d")} | {name[:30]:30} | {duration_min:3.0f}min | '
                      f'{avg_w:3.0f}W avg | {np_w:3.0f}W NP | Est 20min: {estimated_20min:3.0f}W')
            
            # Statistical analysis
            power_values.sort(reverse=True)
            best_20_min_estimates.sort(reverse=True)
            
            print()
            print('🔢 STATISTICAL POWER ANALYSIS')
            print('=' * 35)
            
            # Current approach (last 90 days only was limited)
            recent_90_avg = sum(power_values[:15]) / min(15, len(power_values))
            
            # Better approach: Top 20-minute power estimates
            top_5_estimates = best_20_min_estimates[:5]
            top_10_estimates = best_20_min_estimates[:10]
            
            # FTP estimates using different methods
            ftp_conservative = sum(top_10_estimates) / len(top_10_estimates) * 0.95
            ftp_moderate = sum(top_5_estimates) / len(top_5_estimates) * 0.95
            ftp_aggressive = max(best_20_min_estimates) * 0.95
            
            # Percentile analysis
            p95_power = power_values[int(len(power_values) * 0.05)]  # 95th percentile
            p90_power = power_values[int(len(power_values) * 0.1)]   # 90th percentile
            p85_power = power_values[int(len(power_values) * 0.15)]  # 85th percentile
            
            print(f'Total activities analyzed: {len(activities)}')
            print(f'Average power (all rides): {sum(power_values) / len(power_values):.0f}W')
            print(f'95th percentile power: {p95_power:.0f}W')
            print(f'90th percentile power: {p90_power:.0f}W')
            print(f'85th percentile power: {p85_power:.0f}W')
            print()
            print(f'Top 5 estimated 20-min powers: {[f"{x:.0f}W" for x in top_5_estimates]}')
            print(f'Top 10 estimated 20-min powers: {[f"{x:.0f}W" for x in top_10_estimates]}')
            print()
            
            print('🎯 FTP ESTIMATES')
            print('=' * 20)
            print(f'Conservative FTP (top 10 avg × 0.95): {ftp_conservative:.0f}W')
            print(f'Moderate FTP (top 5 avg × 0.95):     {ftp_moderate:.0f}W')
            print(f'Aggressive FTP (best effort × 0.95):  {ftp_aggressive:.0f}W')
            print(f'Percentile-based FTP (95th × 0.95):   {p95_power * 0.95:.0f}W')
            print()
            
            # Get current FTP for comparison
            result = conn.execute(text("""
                SELECT u.email, t.ftp_watts
                FROM thresholds t
                JOIN users u ON t.user_id = u.user_id
                WHERE t.ftp_watts IS NOT NULL
                ORDER BY t.date_updated DESC
                LIMIT 1
            """))
            
            current_threshold = result.fetchone()
            if current_threshold:
                email, current_ftp = current_threshold
                print(f'Current FTP in database: {current_ftp:.0f}W')
                
                # Recommended FTP (average of moderate methods)
                recommended_ftp = (ftp_moderate + p95_power * 0.95) / 2
                print(f'RECOMMENDED FTP: {recommended_ftp:.0f}W')
                print()
                
                difference = recommended_ftp - current_ftp
                if difference > 20:
                    print(f'⚠️  SIGNIFICANT UNDERESTIMATE: Current FTP is {difference:.0f}W too low!')
                    print(f'   Increase from {current_ftp:.0f}W to {recommended_ftp:.0f}W')
                elif difference > 10:
                    print(f'⚠️  MODERATE UNDERESTIMATE: Current FTP is {difference:.0f}W low')
                elif difference < -10:
                    print(f'⚠️  POSSIBLE OVERESTIMATE: Current FTP might be {abs(difference):.0f}W too high')
                else:
                    print(f'✅ Current FTP seems reasonable (within {abs(difference):.0f}W)')
            
            print()
            print('💡 ANALYSIS INSIGHTS')
            print('=' * 22)
            
            # Check for training consistency
            recent_activities = [a for a in activities if a[6] > datetime.now() - timedelta(days=60)]
            if len(recent_activities) >= 8:
                recent_power_avg = sum(a[3] for a in recent_activities if a[3]) / len(recent_activities)
                print(f'Recent training power (60 days): {recent_power_avg:.0f}W avg')
                
                # Check if recent performance supports higher FTP
                if recent_power_avg > current_ftp * 0.7:
                    print('✅ Recent training supports higher FTP estimate')
                else:
                    print('⚠️  Recent training might not support higher FTP')
            
            # Look for breakthrough performances
            breakthrough_rides = [a for a in activities if a[3] and a[3] > 200]  # >200W average
            if breakthrough_rides:
                print(f'High-power performances (>200W avg): {len(breakthrough_rides)} rides')
                best_breakthrough = max(breakthrough_rides, key=lambda x: x[3])
                print(f'Best breakthrough: {best_breakthrough[3]:.0f}W avg, {best_breakthrough[5]:.0f}W NP')

    except Exception as e:
        print(f'Error analyzing FTP: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_ftp_12_months()
