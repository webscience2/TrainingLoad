#!/usr/bin/env python3
"""
Clear all user data to test new user experience.

This script safely deletes all user data from the database to simulate
a fresh new user signup and test the complete workflow:
1. User authentication
2. Activity sync with stream analysis  
3. Research-based threshold calculation
4. UTL calculation with new methods
5. Dashboard display

⚠️  WARNING: This will delete ALL user data!
"""

import sys
import os
sys.path.append('/Users/adam/src/TrainingLoad/backend')
sys.path.append('/Users/adam/src/TrainingLoad')

from config import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)

def clear_all_user_data():
    """Clear all user data from the database for fresh testing."""
    print('🧹 CLEARING ALL USER DATA FOR FRESH NEW USER TEST')
    print('=' * 60)
    
    try:
        with engine.connect() as conn:
            # Check what we have before deletion
            print('\n📊 Current Data Count:')
            
            # Count existing data
            tables_to_check = [
                'activities',
                'thresholds', 
                'wellness_data',
                'users'
            ]
            
            for table in tables_to_check:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f'  {table}: {count} records')
                except Exception as e:
                    print(f'  {table}: Error checking - {e}')
            
            # Ask for confirmation
            print(f'\n⚠️  WARNING: This will delete ALL user data!')
            print(f'Are you sure you want to proceed? (yes/no): ', end='')
            
            confirmation = input().lower().strip()
            if confirmation != 'yes':
                print('❌ Operation cancelled.')
                return False
                
            print('\n🗑️  Deleting data in proper order (respecting foreign keys)...')
            
            # Delete in proper order to respect foreign key constraints
            deletion_order = [
                'wellness_data',  # References users
                'activities',     # References users  
                'thresholds',     # References users
                'users'          # No dependencies
            ]
            
            total_deleted = 0
            
            for table in deletion_order:
                try:
                    # Get count before deletion
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    before_count = result.scalar()
                    
                    if before_count > 0:
                        # Delete all records
                        result = conn.execute(text(f"DELETE FROM {table}"))
                        deleted_count = result.rowcount
                        total_deleted += deleted_count
                        
                        print(f'  ✅ Deleted {deleted_count} records from {table}')
                    else:
                        print(f'  ⏭️  {table} was already empty')
                        
                except Exception as e:
                    print(f'  ❌ Error deleting from {table}: {e}')
            
            # Commit the transaction
            conn.commit()
            
            print(f'\n🎯 CLEANUP COMPLETE')
            print(f'Total records deleted: {total_deleted}')
            print(f'Database is now clean and ready for new user testing!')
            
            # Verify cleanup
            print(f'\n✅ Verification - Final record counts:')
            for table in tables_to_check:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    status = '✅' if count == 0 else '❌'
                    print(f'  {status} {table}: {count} records')
                except Exception as e:
                    print(f'  ❌ {table}: Error checking - {e}')
            
            return True
            
    except Exception as e:
        print(f'❌ Error clearing database: {e}')
        import traceback
        traceback.print_exc()
        return False

def print_next_steps():
    """Print instructions for testing the new user workflow."""
    print('\n🚀 NEXT STEPS - NEW USER TESTING WORKFLOW')
    print('=' * 50)
    print('1. 🌐 Start the web application:')
    print('   cd /Users/adam/src/TrainingLoad')
    print('   python backend/main.py')
    print()
    print('2. 🔐 Test user authentication:')
    print('   - Navigate to the app in browser')
    print('   - Sign up / authenticate with Strava')
    print('   - Complete onboarding questionnaire')
    print()
    print('3. 📊 Verify research-based thresholds:')
    print('   - Check that thresholds are calculated using stream analysis')
    print('   - Should show FTP ~215W and FTHP ~3.2 m/s based on historical data')
    print()
    print('4. 🔄 Test activity sync:')
    print('   - Activities should auto-sync from Strava with streams')
    print('   - UTL scores calculated with research-based methods')
    print('   - Threshold improvements detected automatically')
    print()
    print('5. 📈 Verify dashboard:')
    print('   - Training load charts display correctly')
    print('   - Activity analysis shows proper UTL scores')
    print('   - Performance metrics reflect accurate thresholds')
    print()
    print('6. 🧪 Run validation tests:')
    print('   python tests/test_new_user_thresholds.py')
    print('   python tests/validate_scientific_scaling.py')
    print()
    print('💡 This tests the complete new user experience with all improvements!')

if __name__ == "__main__":
    print('New User Testing - Database Reset')
    print('This will test the complete new user workflow with research-based methods')
    
    success = clear_all_user_data()
    
    if success:
        print_next_steps()
    else:
        print('\n❌ Database cleanup failed. Please check the errors above.')
