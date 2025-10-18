#!/usr/bin/env python3
"""
Railway Cron Service for Fantasy Hockey Data Collection
This service runs weekly to collect fresh data
"""

import os
import sys
import subprocess
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_data_collection():
    """Run the data collection process"""
    logger.info("🔄 Starting weekly data collection...")
    
    try:
        # Run data collection with a timeout
        result = subprocess.run(
            [sys.executable, 'pipeline.py'], 
            capture_output=True, 
            text=True, 
            cwd=os.getcwd(),
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode == 0:
            logger.info("✅ Weekly data collection completed successfully!")
            if result.stdout:
                logger.info(f"STDOUT: {result.stdout[-500:]}")  # Last 500 chars
            return True
        else:
            logger.error("❌ Weekly data collection failed!")
            if result.stdout:
                logger.error(f"STDOUT: {result.stdout[-500:]}")
            if result.stderr:
                logger.error(f"STDERR: {result.stderr[-500:]}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("⏰ Data collection timed out after 10 minutes")
        return False
    except Exception as e:
        logger.error(f"❌ Error during data collection: {e}")
        return False

def main():
    """Main cron job function"""
    logger.info("🏒 Fantasy Hockey Weekly Data Collection")
    logger.info(f"Timestamp: {datetime.now()}")
    
    # Ensure necessary directories exist
    directories = ["data", "output", "reports", "logs"]
    for directory in directories:
        if not os.path.exists(directory):
            logger.info(f"📁 Creating directory: {directory}")
            os.makedirs(directory, exist_ok=True)
    
    # Run data collection
    success = run_data_collection()
    
    if success:
        logger.info("✅ Weekly data collection completed successfully!")
        logger.info("💡 Fresh data is now available for the dashboard")
    else:
        logger.error("❌ Weekly data collection failed!")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
