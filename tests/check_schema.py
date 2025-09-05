#!/usr/bin/env python3
"""
Check database schema for activities table.
"""

import sys
import os
sys.path.append('/Users/adam/src/TrainingLoad/backend')

from config import engine
from sqlalchemy import text

def check_schema():
    try:
        with engine.connect() as conn:
            # Check activities table columns
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'activities' 
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            print('Activities table columns:')
            for col in columns:
                print(f'  {col[0]} ({col[1]})')
            
            # Sample a few activities to see the structure
            print('\nSample activities:')
            result = conn.execute(text("SELECT * FROM activities LIMIT 3"))
            activities = result.fetchall()
            if activities:
                cols = result.keys()
                for i, activity in enumerate(activities):
                    print(f'\nActivity {i+1}:')
                    for j, col_name in enumerate(cols):
                        value = activity[j]
                        if col_name == 'data' and value:
                            # Show just a snippet of JSON data
                            value_str = str(value)[:100] + '...' if len(str(value)) > 100 else str(value)
                        else:
                            value_str = str(value)
                        print(f'  {col_name}: {value_str}')

    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    check_schema()
