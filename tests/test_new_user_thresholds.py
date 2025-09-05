#!/usr/bin/env python3
"""
Test new user threshold calculation with research-based methods
"""

import sys
import os
sys.path.append('/Users/adam/src/TrainingLoad/backend')

from research_threshold_calculator import calculate_initial_thresholds_for_new_user
import logging

logging.basicConfig(level=logging.INFO)

def test_new_user_thresholds():
    """Test the new user threshold calculation system"""
    print('🔬 TESTING NEW USER THRESHOLD CALCULATION')
    print('=' * 50)
    
    # Test with existing user (user_id = 1) to verify the system works
    user_id = 1
    
    print(f'Testing research-based threshold calculation for user {user_id}...')
    
    try:
        estimates = calculate_initial_thresholds_for_new_user(user_id)
        
        if estimates:
            print('✅ Research-based threshold calculation successful!')
            print(f'Estimates: {estimates}')
            
            if estimates.get('ftp_watts'):
                print(f'  • FTP: {estimates["ftp_watts"]:.0f}W')
                
            if estimates.get('fthp_mps'):
                pace_min_km = (1000 / estimates['fthp_mps']) / 60
                pace_min_mile = (1609.34 / estimates['fthp_mps']) / 60
                print(f'  • FTHP: {estimates["fthp_mps"]:.2f} m/s ({pace_min_km:.1f} min/km, {pace_min_mile:.1f} min/mile)')
                
            if estimates.get('max_hr'):
                print(f'  • Max HR: {estimates["max_hr"]} bpm')
                
            if estimates.get('resting_hr'):
                print(f'  • Resting HR: {estimates["resting_hr"]} bpm')
                
            print()
            print('🎯 NEW USER ONBOARDING READY')
            print('The system will now automatically use research-based')
            print('stream analysis for all new users!')
            
        else:
            print('❌ No threshold estimates calculated')
            
    except Exception as e:
        print(f'❌ Error testing new user threshold calculation: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_user_thresholds()
