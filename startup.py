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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def run_data_collection():
    """Run the data collection process"""
    print("Starting data collection...")

    try:
        # Run data collection with a longer timeout
        result = subprocess.run(
            [sys.executable, "pipeline.py"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),  # Use current directory instead of /app
            timeout=600,
        )  # 10 minute timeout

        if result.returncode == 0:
            print("Data collection completed successfully!")
            if result.stdout:
                print("STDOUT:", result.stdout[-500:])  # Last 500 chars
            return True
        else:
            print("Data collection failed!")
            if result.stderr:
                print("STDERR:", result.stderr[-500:])  # Last 500 chars
            if result.stdout:
                print("STDOUT:", result.stdout[-500:])  # Last 500 chars
            return False

    except subprocess.TimeoutExpired:
        print("Data collection timed out after 10 minutes")
        return False
    except Exception as e:
        print(f"Error during data collection: {e}")
        return False


def start_dashboard():
    """Start the Dash dashboard"""
    print("Starting Fantasy Hockey Dashboard...")

    # Import and run dashboard
    try:
        from dashboard import main as dashboard_main

        dashboard_main()
    except Exception as e:
        print(f"Error starting dashboard: {e}")
        return False

    return True


def main():
    print("Fantasy Hockey Dashboard Startup")
    print(f"Timestamp: {datetime.now()}")

    # Create all necessary directories
    directories = ["data", "output", "reports", "logs"]  # Use relative paths for local
    for directory in directories:
        if not os.path.exists(directory):
            print(f"Creating directory: {directory}")
            os.makedirs(directory, exist_ok=True)

    # Always run as web service - cron will be handled separately
    print("Running as web service")
    
    # Run data collection
    data_success = run_data_collection()

    if data_success:
        print("Data collection successful, starting dashboard...")
    else:
        print("Data collection failed, starting dashboard anyway...")
        print("You can manually trigger data collection later")

    # Start dashboard
    start_dashboard()


if __name__ == "__main__":
    main()
