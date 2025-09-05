#!/usr/bin/env python3
"""
TrainingLoad Background Service Manager

Easy management of the TrainingLoad background processing scheduler.

Usage:
    python service_manager.py start     # Start background scheduler  
    python service_manager.py stop      # Stop background scheduler
    python service_manager.py status    # Show scheduler status
    python service_manager.py logs      # Show recent logs
    python service_manager.py jobs      # List scheduled jobs
"""

import os
import sys
import subprocess
import argparse
import signal
import time
from pathlib import Path
import psutil


def get_project_dir() -> Path:
    """Get the absolute path to the project directory."""
    return Path(__file__).parent.absolute()


def get_pid_file() -> Path:
    """Get the path to the PID file."""
    return get_project_dir() / "logs" / "scheduler.pid"


def get_log_file() -> Path:
    """Get the path to the main log file.""" 
    return get_project_dir() / "logs" / "background_processor.log"


def is_scheduler_running() -> bool:
    """Check if the background scheduler is currently running."""
    pid_file = get_pid_file()
    
    if not pid_file.exists():
        return False
    
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # Check if process is still running
        return psutil.pid_exists(pid) and 'background_processor.py' in ' '.join(psutil.Process(pid).cmdline())
    
    except (ValueError, FileNotFoundError, psutil.NoSuchProcess):
        # Clean up stale PID file
        if pid_file.exists():
            pid_file.unlink()
        return False


def start_scheduler():
    """Start the background scheduler as a daemon process."""
    if is_scheduler_running():
        print("✅ Background scheduler is already running")
        return True
    
    print("🚀 Starting TrainingLoad background scheduler...")
    
    project_dir = get_project_dir()
    log_dir = project_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Start the background processor
    log_file = log_dir / "scheduler_daemon.log"
    
    try:
        # Start process in background
        process = subprocess.Popen([
            sys.executable, 
            str(project_dir / "background_processor.py"), 
            "--start-scheduler"
        ], 
        stdout=open(log_file, 'a'),
        stderr=subprocess.STDOUT,
        cwd=project_dir,
        preexec_fn=os.setsid  # Create new process group
        )
        
        # Save PID
        pid_file = get_pid_file()
        with open(pid_file, 'w') as f:
            f.write(str(process.pid))
        
        # Give it a moment to start up
        time.sleep(2)
        
        if is_scheduler_running():
            print(f"✅ Background scheduler started successfully (PID: {process.pid})")
            print(f"📝 Logs: {log_file}")
            print(f"🔍 Status: python service_manager.py status")
            return True
        else:
            print("❌ Failed to start background scheduler")
            print(f"📝 Check logs: {log_file}")
            return False
            
    except Exception as e:
        print(f"❌ Error starting scheduler: {e}")
        return False


def stop_scheduler():
    """Stop the background scheduler."""
    if not is_scheduler_running():
        print("⚠️  Background scheduler is not running")
        return True
    
    print("🛑 Stopping TrainingLoad background scheduler...")
    
    pid_file = get_pid_file()
    
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # Send SIGTERM for graceful shutdown
        os.kill(pid, signal.SIGTERM)
        
        # Wait for process to stop
        for i in range(30):  # Wait up to 30 seconds
            if not is_scheduler_running():
                pid_file.unlink()
                print("✅ Background scheduler stopped successfully")
                return True
            time.sleep(1)
        
        # Force kill if graceful shutdown failed
        print("⚠️  Graceful shutdown failed, forcing stop...")
        os.kill(pid, signal.SIGKILL)
        time.sleep(2)
        
        if not is_scheduler_running():
            pid_file.unlink()
            print("✅ Background scheduler stopped (forced)")
            return True
        else:
            print("❌ Failed to stop background scheduler")
            return False
            
    except (FileNotFoundError, ProcessLookupError):
        # Process already stopped
        if pid_file.exists():
            pid_file.unlink()
        print("✅ Background scheduler was not running")
        return True
    except Exception as e:
        print(f"❌ Error stopping scheduler: {e}")
        return False


def show_status():
    """Show the current status of the background scheduler."""
    print("📊 TrainingLoad Background Scheduler Status")
    print("=" * 50)
    
    if is_scheduler_running():
        pid_file = get_pid_file()
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        try:
            process = psutil.Process(pid)
            print(f"✅ Status: Running (PID: {pid})")
            print(f"⏰ Started: {process.create_time()}")
            print(f"💾 Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
            print(f"🔄 CPU: {process.cpu_percent():.1f}%")
        except psutil.NoSuchProcess:
            print("❌ Status: Process not found (stale PID file)")
    else:
        print("❌ Status: Not running")
    
    # Show recent log entries
    log_file = get_log_file()
    if log_file.exists():
        print(f"\n📝 Recent log entries ({log_file}):")
        try:
            result = subprocess.run(['tail', '-n', '10', str(log_file)], 
                                  capture_output=True, text=True)
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    print(f"  {line}")
            else:
                print("  No recent log entries")
        except Exception as e:
            print(f"  Error reading logs: {e}")
    else:
        print("\n📝 No log file found")
    
    # Show job status using the background processor
    print(f"\n📋 Scheduled Jobs:")
    try:
        result = subprocess.run([
            sys.executable,
            str(get_project_dir() / "background_processor.py"),
            "--list-jobs"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"  Error getting job status: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("  Timeout getting job status")
    except Exception as e:
        print(f"  Error: {e}")


def show_logs(lines=50):
    """Show recent log entries."""
    log_file = get_log_file()
    
    if not log_file.exists():
        print("📝 No log file found")
        return
    
    print(f"📝 Last {lines} log entries from {log_file}:")
    print("=" * 80)
    
    try:
        result = subprocess.run(['tail', '-n', str(lines), str(log_file)],
                              capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"❌ Error reading logs: {e}")


def list_jobs():
    """List currently scheduled jobs."""
    print("📋 Scheduled Background Jobs")
    print("=" * 40)
    
    try:
        subprocess.run([
            sys.executable,
            str(get_project_dir() / "background_processor.py"),
            "--list-jobs"
        ], timeout=10)
    except subprocess.TimeoutExpired:
        print("❌ Timeout getting job list")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    parser = argparse.ArgumentParser(description='TrainingLoad Background Service Manager')
    parser.add_argument('action', choices=['start', 'stop', 'status', 'logs', 'jobs', 'restart'],
                      help='Service management action')
    parser.add_argument('--lines', type=int, default=50,
                      help='Number of log lines to show (for logs command)')
    
    args = parser.parse_args()
    
    if args.action == 'start':
        success = start_scheduler()
        sys.exit(0 if success else 1)
    
    elif args.action == 'stop':
        success = stop_scheduler()
        sys.exit(0 if success else 1)
    
    elif args.action == 'restart':
        print("🔄 Restarting background scheduler...")
        stop_scheduler()
        time.sleep(2)
        success = start_scheduler()
        sys.exit(0 if success else 1)
    
    elif args.action == 'status':
        show_status()
    
    elif args.action == 'logs':
        show_logs(args.lines)
    
    elif args.action == 'jobs':
        list_jobs()


if __name__ == "__main__":
    main()
