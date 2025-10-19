#!/usr/bin/env python3
"""
Test script for Railway Cron Service
Run this to test if the cron service is working
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

def test_cron_service():
    """Test the cron service functionality"""
    logger.info("Testing Fantasy Hockey Cron Service")
    logger.info(f"Timestamp: {datetime.now()}")
    
    # Check if we're running as cron job
    cron_schedule = os.getenv("RAILWAY_CRON_SCHEDULE")
    if cron_schedule:
        logger.info(f"Running as cron job with schedule: {cron_schedule}")
    else:
        logger.info("Not running as cron job")
    
    # Check environment variables
    required_vars = ["ESPN_S2", "ESPN_SWID", "OPENAI_API_KEY", "LEAGUE_ID", "TEAM_ID", "YEAR"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing environment variables: {missing_vars}")
        return False
    else:
        logger.info("All required environment variables are present")
    
    # Test data collection
    logger.info("Testing data collection...")
    try:
        result = subprocess.run(
            [sys.executable, 'pipeline.py'], 
            capture_output=True, 
            text=True, 
            cwd=os.getcwd(),
            timeout=300  # 5 minute timeout for test
        )
        
        if result.returncode == 0:
            logger.info("Data collection test successful!")
            logger.info(f"STDOUT: {result.stdout[-200:]}")  # Last 200 chars
            return True
        else:
            logger.error("Data collection test failed!")
            logger.error(f"STDERR: {result.stderr[-200:]}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Data collection test timed out")
        return False
    except Exception as e:
        logger.error(f"Error during data collection test: {e}")
        return False

def main():
    """Main test function"""
    success = test_cron_service()
    
    if success:
        logger.info("Cron service test completed successfully!")
        logger.info("Ready for weekly data collection")
    else:
        logger.error("Cron service test failed!")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
