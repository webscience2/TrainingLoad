#!/usr/bin/env python3
"""
TrainingLoad Background Processing Setup

This script helps manage the APScheduler-based background processing system.
It's kept for backward compatibility but now recommends using service_manager.py.

Usage:
    python setup_cron.py --migrate-to-apscheduler   # Remove cron jobs and setup APScheduler
    python setup_cron.py --status                   # Show current setup
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def show_migration_info():
    """Show information about migrating to APScheduler."""
    print("🔄 TrainingLoad Background Processing Migration")
    print("=" * 60)
    print()
    print("ℹ️  TrainingLoad now uses APScheduler instead of cron jobs for better:")
    print("   • Reliability and error handling")
    print("   • Python integration and logging") 
    print("   • Job management and monitoring")
    print("   • Cross-platform compatibility")
    print()
    print("🚀 To start the new background scheduler:")
    print("   python service_manager.py start")
    print()
    print("📊 To check scheduler status:")
    print("   python service_manager.py status")
    print()
    print("📝 To view logs:")
    print("   python service_manager.py logs")
    print()
    print("🛑 To stop the scheduler:")
    print("   python service_manager.py stop")
    print()


def remove_old_cron_jobs():
    """Remove any old TrainingLoad cron jobs if they exist."""
    print("�️  Checking for old TrainingLoad cron jobs to remove...")
    
    try:
        # Get current crontab
        try:
            current_crontab = subprocess.check_output(['crontab', '-l'], stderr=subprocess.DEVNULL).decode('utf-8')
        except subprocess.CalledProcessError:
            print("✅ No existing crontab found")
            return True
        
        # Look for TrainingLoad entries
        lines = current_crontab.split('\n')
        trainload_lines = [line for line in lines if 'background_processor.py' in line or 'TrainingLoad' in line]
        
        if not trainload_lines:
            print("✅ No old TrainingLoad cron jobs found")
            return True
        
        print(f"🔍 Found {len(trainload_lines)} old TrainingLoad cron entries:")
        for line in trainload_lines:
            print(f"   {line}")
        
        # Remove TrainingLoad entries
        filtered_lines = []
        skip_next = False
        
        for line in lines:
            if 'TrainingLoad Background Processing Jobs' in line:
                skip_next = True
                continue
            elif skip_next and (line.startswith('#') or 'background_processor.py' in line or line.strip() == ''):
                continue
            else:
                skip_next = False
                if line.strip():
                    filtered_lines.append(line)
        
        # Install the filtered crontab
        new_crontab = '\n'.join(filtered_lines)
        
        if new_crontab.strip():
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_crontab)
        else:
            # Remove crontab entirely if empty
            subprocess.run(['crontab', '-r'], stderr=subprocess.DEVNULL)
        
        print("✅ Old TrainingLoad cron jobs removed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error removing cron jobs: {e}")
        return False


def migrate_to_apscheduler():
    """Full migration from cron to APScheduler."""
    print("� Migrating TrainingLoad to APScheduler-based background processing")
    print("=" * 80)
    
    # Remove old cron jobs
    success = remove_old_cron_jobs()
    if not success:
        return False
    
    print()
    print("✅ Migration preparation complete!")
    print()
    
    # Show next steps
    print("📋 Next steps:")
    print("1. Install new dependencies:")
    print("   uv sync")
    print()
    print("2. Start the background scheduler:")
    print("   python service_manager.py start")
    print()
    print("3. Verify it's working:")
    print("   python service_manager.py status")
    print()
    print("📚 The new system provides:")
    print("   • Better error handling and recovery")
    print("   • Detailed logging and monitoring") 
    print("   • Easy start/stop/restart management")
    print("   • Job status and health checking")
    
    return True


def show_current_status():
    """Show current background processing setup."""
    print("📊 TrainingLoad Background Processing Status")
    print("=" * 50)
    
    # Check for cron jobs
    try:
        current_crontab = subprocess.check_output(['crontab', '-l'], stderr=subprocess.DEVNULL).decode('utf-8')
        trainload_cron_jobs = [line for line in current_crontab.split('\n') if 'background_processor.py' in line]
        
        if trainload_cron_jobs:
            print(f"⚠️  Found {len(trainload_cron_jobs)} old cron jobs:")
            for job in trainload_cron_jobs:
                print(f"   {job}")
            print()
            print("🔄 Recommend migrating to APScheduler:")
            print("   python setup_cron.py --migrate-to-apscheduler")
        else:
            print("✅ No old cron jobs found")
            
    except subprocess.CalledProcessError:
        print("✅ No cron jobs found")
    
    print()
    
    # Check APScheduler status
    project_dir = Path(__file__).parent.absolute()
    service_manager = project_dir / "service_manager.py"
    
    if service_manager.exists():
        print("🚀 APScheduler service manager available")
        print("   Check status: python service_manager.py status")
        print("   Start scheduler: python service_manager.py start")
        
        # Try to get actual status
        try:
            result = subprocess.run([
                sys.executable, str(service_manager), 'status'
            ], capture_output=True, text=True, timeout=5)
            
            if 'Running' in result.stdout:
                print("   Current status: ✅ Running")
            elif 'Not running' in result.stdout:
                print("   Current status: ❌ Not running")
            else:
                print("   Current status: ❓ Unknown")
                
        except (subprocess.TimeoutExpired, Exception):
            print("   Current status: ❓ Could not determine")
    else:
        print("❌ APScheduler service manager not found")
        print("   Expected: service_manager.py")


def main():
    parser = argparse.ArgumentParser(description='TrainingLoad Background Processing Setup')
    parser.add_argument('--migrate-to-apscheduler', action='store_true',
                       help='Remove old cron jobs and setup APScheduler')
    parser.add_argument('--status', action='store_true',
                       help='Show current background processing status')
    parser.add_argument('--info', action='store_true',
                       help='Show migration information')
    
    args = parser.parse_args()
    
    if not any([args.migrate_to_apscheduler, args.status, args.info]):
        # Default to showing info
        show_migration_info()
        return
    
    if args.migrate_to_apscheduler:
        success = migrate_to_apscheduler()
        sys.exit(0 if success else 1)
    elif args.status:
        show_current_status()
    elif args.info:
        show_migration_info()


if __name__ == "__main__":
    main()
