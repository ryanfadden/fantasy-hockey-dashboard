#!/usr/bin/env python3
"""
Manual Fantasy Hockey Data Collection Trigger
Use this to manually trigger data collection outside of the weekly schedule
"""

import subprocess
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_data_collection():
    """Run the data collection process"""
    print(f"🔄 Starting manual data collection - {datetime.now()}")
    
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
            print("✅ Data collection completed successfully!")
            if result.stdout:
                print("STDOUT:", result.stdout[-500:])  # Last 500 chars
            return True
        else:
            print("❌ Data collection failed!")
            if result.stdout:
                print("STDOUT:", result.stdout[-500:])
            if result.stderr:
                print("STDERR:", result.stderr[-500:])
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Data collection timed out after 10 minutes")
        return False
    except Exception as e:
        print(f"❌ Error during data collection: {e}")
        return False

def main():
    """Main function"""
    print("🏒 Fantasy Hockey Manual Data Collection")
    print(f"Timestamp: {datetime.now()}")
    
    success = run_data_collection()
    
    if success:
        print("✅ Manual data collection completed successfully!")
        print("💡 You can now refresh your dashboard to see updated data")
    else:
        print("❌ Manual data collection failed!")
        print("💡 Check the error messages above for troubleshooting")

if __name__ == "__main__":
    main()
