#!/usr/bin/env python3
"""
Data collection script for Railway deployment
"""
import os
import sys
import subprocess
from datetime import datetime

def main():
    print("Starting Fantasy Hockey Data Collection...")
    print(f"Timestamp: {datetime.now()}")
    
    # Set up environment
    os.environ.setdefault('PYTHONPATH', '/app')
    
    try:
        # Run the main data collection
        print("Running main.py for data collection...")
        result = subprocess.run([sys.executable, 'main.py'], 
                              capture_output=True, 
                              text=True, 
                              cwd='/app')
        
        if result.returncode == 0:
            print("✅ Data collection completed successfully!")
            print("STDOUT:", result.stdout)
        else:
            print("❌ Data collection failed!")
            print("STDERR:", result.stderr)
            print("STDOUT:", result.stdout)
            
    except Exception as e:
        print(f"❌ Error running data collection: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
