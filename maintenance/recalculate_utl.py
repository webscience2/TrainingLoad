#!/usr/bin/env python3
"""
Recalculate UTL scores with corrected FTP value
"""

import os
import sys
import logging
from pathlib import Path

# Add backend directory to path
sys.path.append('/Users/adam/src/TrainingLoad/backend')
sys.path.append('/Users/adam/src/TrainingLoad')

# Set environment
os.environ.setdefault("PYTHONPATH", "/Users/adam/src/TrainingLoad/backend")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    from config import SessionLocal
    from models import User, Activity, Threshold
    from utils import calculate_utl_score
    
    def recalculate_utl_with_new_ftp():
        """Recalculate UTL scores for cycling activities with corrected FTP"""
        db = SessionLocal()
        
        try:
            # Get user 1
            user = db.query(User).filter(User.user_id == 1).first()
            if not user:
                logging.error("User 1 not found")
                return
            
            # Get thresholds (should now have corrected FTP)
            threshold = db.query(Threshold).filter(Threshold.user_id == 1).first()
            if not threshold:
                logging.error("Thresholds not found for user 1")
                return
                
            logging.info(f"Using corrected FTP: {threshold.ftp_watts}W")
            
            # Get cycling activities with power data
            cycling_activities = db.query(Activity).filter(
                Activity.user_id == 1,
                Activity.type.ilike('%ride%')
            ).all()
            
            updated_count = 0
            
            for activity in cycling_activities:
                if activity.data and 'average_watts' in activity.data:
                    # Recalculate UTL score
                    new_utl_score, method = calculate_utl_score(activity, threshold)
                    
                    if new_utl_score is not None and new_utl_score != activity.utl_score:
                        old_score = activity.utl_score
                        activity.utl_score = new_utl_score
                        activity.calculation_method = method
                        updated_count += 1
                        
                        if updated_count <= 5:  # Log first 5 updates
                            logging.info(f"Activity '{activity.name}': {old_score:.1f} → {new_utl_score:.1f} TSS")
            
            db.commit()
            logging.info(f"✅ Updated {updated_count} cycling activities with corrected FTP-based TSS scores")
            
            # Show summary stats
            cycling_with_utl = db.query(Activity).filter(
                Activity.user_id == 1,
                Activity.type.ilike('%ride%'),
                Activity.utl_score.isnot(None)
            ).all()
            
            if cycling_with_utl:
                avg_tss = sum(a.utl_score for a in cycling_with_utl) / len(cycling_with_utl)
                max_tss = max(a.utl_score for a in cycling_with_utl)
                logging.info(f"📊 Cycling UTL Stats: Avg={avg_tss:.1f}, Max={max_tss:.1f}, Count={len(cycling_with_utl)}")
            
        except Exception as e:
            logging.error(f"Error recalculating UTL scores: {e}")
            db.rollback()
        finally:
            db.close()
    
    if __name__ == "__main__":
        logging.info("🔄 Recalculating UTL scores with corrected FTP...")
        recalculate_utl_with_new_ftp()
        logging.info("✅ UTL recalculation complete")
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the TrainingLoad directory")
