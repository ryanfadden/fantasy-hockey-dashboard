#!/usr/bin/env python3
"""
Startup script for Railway deployment
Runs data collection first, then starts the dashboard
"""
import os
import sys
import subprocess
import time
from datetime import datetime

def run_data_collection():
    """Run the data collection process"""
    print("🔄 Starting data collection...")
    
    try:
        # Run data collection
        result = subprocess.run([sys.executable, 'main.py'], 
                              capture_output=True, 
                              text=True, 
                              cwd='/app',
                              timeout=300)  # 5 minute timeout
        
        if result.returncode == 0:
            print("✅ Data collection completed successfully!")
            return True
        else:
            print("❌ Data collection failed!")
            print("STDERR:", result.stderr)
            print("STDOUT:", result.stdout)
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Data collection timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Error during data collection: {e}")
        return False

def start_dashboard():
    """Start the Dash dashboard"""
    print("🚀 Starting Fantasy Hockey Dashboard...")
    
    # Import and run dashboard
    try:
        from dashboard import main as dashboard_main
        dashboard_main()
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        return False
    
    return True

def main():
    print("🏒 Fantasy Hockey Dashboard Startup")
    print(f"Timestamp: {datetime.now()}")
    
    # Check if data directories exist
    if not os.path.exists('/app/data') or not os.path.exists('/app/output'):
        print("📁 Creating data directories...")
        os.makedirs('/app/data', exist_ok=True)
        os.makedirs('/app/output', exist_ok=True)
    
    # Run data collection
    if run_data_collection():
        print("✅ Data collection successful, starting dashboard...")
    else:
        print("⚠️ Data collection failed, starting dashboard anyway...")
    
    # Start dashboard
    start_dashboard()

if __name__ == '__main__':
    main()
