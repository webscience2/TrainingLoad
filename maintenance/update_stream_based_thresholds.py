#!/usr/bin/env python3
"""
Update thresholds based on our stream analysis findings.
"""

import sys
import os
sys.path.append('/Users/adam/src/TrainingLoad/backend')
sys.path.append('/Users/adam/src/TrainingLoad')

from config import engine
from sqlalchemy import text
from datetime import datetime

def update_thresholds_with_stream_analysis():
    """Update thresholds based on our comprehensive stream analysis."""
    
    print('🔬 UPDATING THRESHOLDS BASED ON STREAM ANALYSIS')
    print('=' * 55)
    
    try:
        with engine.connect() as conn:
            # Get current thresholds
            result = conn.execute(text("""
                SELECT u.email, t.ftp_watts, t.fthp_mps, t.user_id
                FROM thresholds t
                JOIN users u ON t.user_id = u.user_id
                WHERE u.email LIKE '%adam%'
                ORDER BY t.date_updated DESC
                LIMIT 1
            """))
            
            current = result.fetchone()
            if current:
                email, current_ftp, current_fthp, user_id = current
                
                print(f'Current thresholds for {email}:')
                print(f'  FTP: {current_ftp:.0f}W')
                print(f'  FTHP: {current_fthp:.2f} m/s ({(1000/current_fthp)/60:.1f} min/km)')
                print()
                
                # Based on our stream analysis:
                # Cycling: 207W best 20-min → 197W FTP (95%)
                # Running: 3.36 m/s best sustained threshold pace
                
                new_ftp = 197  # From "Road to Sky" 207W × 0.95
                new_fthp = 3.36  # From "Morning Run" best 20-min sustained
                
                print('🎯 RECOMMENDED UPDATES (from stream analysis):')
                print(f'  FTP: {current_ftp:.0f}W → {new_ftp:.0f}W (+{new_ftp-current_ftp:.0f}W, +{((new_ftp/current_ftp-1)*100):.1f}%)')
                print(f'  FTHP: {current_fthp:.2f} m/s → {new_fthp:.2f} m/s (+{new_fthp-current_fthp:.2f} m/s)')
                
                old_pace = (1000/current_fthp)/60
                new_pace = (1000/new_fthp)/60
                print(f'  Pace: {old_pace:.1f} min/km → {new_pace:.1f} min/km ({old_pace-new_pace:.1f} min/km faster)')
                print()
                
                # Update the database
                conn.execute(text("""
                    UPDATE thresholds 
                    SET ftp_watts = :new_ftp,
                        fthp_mps = :new_fthp,
                        date_updated = CURRENT_TIMESTAMP
                    WHERE user_id = :user_id
                """), {
                    "new_ftp": new_ftp, 
                    "new_fthp": new_fthp, 
                    "user_id": user_id
                })
                conn.commit()
                
                print('✅ THRESHOLDS UPDATED SUCCESSFULLY!')
                print()
                print('📈 Impact on Training Zones:')
                
                # Show new zones
                ftp_zones = {
                    'Zone 1 (Active Recovery)': f'< {new_ftp * 0.55:.0f}W',
                    'Zone 2 (Endurance)': f'{new_ftp * 0.55:.0f}-{new_ftp * 0.75:.0f}W',
                    'Zone 3 (Tempo)': f'{new_ftp * 0.75:.0f}-{new_ftp * 0.90:.0f}W',
                    'Zone 4 (Lactate Threshold)': f'{new_ftp * 0.90:.0f}-{new_ftp * 1.05:.0f}W',
                    'Zone 5 (VO2 Max)': f'{new_ftp * 1.05:.0f}-{new_ftp * 1.20:.0f}W',
                    'Zone 6 (Anaerobic)': f'> {new_ftp * 1.20:.0f}W'
                }
                
                print('🚴 Cycling Power Zones:')
                for zone, range_str in ftp_zones.items():
                    print(f'  {zone}: {range_str}')
                print()
                
                run_zones = {
                    'Zone 1 (Easy)': f'> {((1000/(new_fthp*0.65))/60):.1f} min/km',
                    'Zone 2 (Aerobic)': f'{((1000/(new_fthp*0.85))/60):.1f}-{((1000/(new_fthp*0.65))/60):.1f} min/km',
                    'Zone 3 (Tempo)': f'{((1000/(new_fthp*0.95))/60):.1f}-{((1000/(new_fthp*0.85))/60):.1f} min/km',
                    'Zone 4 (Threshold)': f'{((1000/(new_fthp*1.05))/60):.1f}-{((1000/(new_fthp*0.95))/60):.1f} min/km',
                    'Zone 5 (VO2 Max)': f'< {((1000/(new_fthp*1.05))/60):.1f} min/km'
                }
                
                print('🏃 Running Pace Zones:')
                for zone, range_str in run_zones.items():
                    print(f'  {zone}: {range_str}')
                print()
                
                print('💡 NEXT STEPS:')
                print('1. ✅ Thresholds updated with stream-based analysis')
                print('2. 🔄 Recalculate historical UTL scores with new thresholds')
                print('3. 🔗 Integrate stream analysis into Strava sync process')
                print('4. 📊 Monitor threshold changes over time')
                
            else:
                print('❌ No user thresholds found')
    
    except Exception as e:
        print(f'Error updating thresholds: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_thresholds_with_stream_analysis()
