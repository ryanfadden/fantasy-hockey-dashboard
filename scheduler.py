#!/usr/bin/env python3
"""
Weekly Fantasy Hockey Data Collection Scheduler
Runs data collection every Monday at 9 AM EST
"""

import schedule
import time
import subprocess
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_weekly_data_collection():
    """Run the weekly data collection process"""
    print(f"🔄 Starting weekly data collection - {datetime.now()}")
    
    try:
        # Run data collection
        result = subprocess.run(
            [sys.executable, 'pipeline.py'], 
            capture_output=True, 
            text=True, 
            cwd=os.getcwd(),
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode == 0:
            print("✅ Weekly data collection completed successfully!")
            if result.stdout:
                print("STDOUT:", result.stdout[-500:])  # Last 500 chars
            return True
        else:
            print("❌ Weekly data collection failed!")
            if result.stdout:
                print("STDOUT:", result.stdout[-500:])
            if result.stderr:
                print("STDERR:", result.stderr[-500:])
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Weekly data collection timed out after 10 minutes")
        return False
    except Exception as e:
        print(f"❌ Error during weekly data collection: {e}")
        return False

def main():
    """Main scheduler function"""
    print("📅 Fantasy Hockey Weekly Scheduler Started")
    print(f"Current time: {datetime.now()}")
    
    # Schedule weekly data collection every Monday at 9 AM EST
    schedule.every().monday.at("09:00").do(run_weekly_data_collection)
    
    print("⏰ Scheduled: Weekly data collection every Monday at 9:00 AM EST")
    print("🔄 Running initial data collection...")
    
    # Run initial data collection
    run_weekly_data_collection()
    
    # Keep the scheduler running
    print("🔄 Scheduler running... Press Ctrl+C to stop")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n🛑 Scheduler stopped by user")

if __name__ == "__main__":
    main()
