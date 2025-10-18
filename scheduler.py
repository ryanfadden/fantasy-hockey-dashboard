"""
Scheduled Analysis Runner
Runs the fantasy hockey analysis on a schedule
"""

import schedule
import time
import logging
from datetime import datetime
from main import FantasyHockeyPipeline
from utils import setup_logging, cleanup_old_files

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


class ScheduledAnalyzer:
    """Handles scheduled analysis runs"""

    def __init__(self):
        """Initialize the scheduled analyzer"""
        self.pipeline = FantasyHockeyPipeline()
        self.setup_schedule()

    def setup_schedule(self):
        """Set up the analysis schedule"""
        # Run analysis every Monday at 12 PM
        schedule.every().monday.at("12:00").do(self.run_analysis)

        # Run quick check every day at 9 AM
        schedule.every().day.at("09:00").do(self.run_quick_check)

        # Cleanup old files every Sunday at 11 PM
        schedule.every().sunday.at("23:00").do(self.cleanup_files)

        logger.info("Scheduled analysis tasks:")
        logger.info("- Full analysis: Every Monday at 12:00 PM")
        logger.info("- Quick check: Every day at 9:00 AM")
        logger.info("- File cleanup: Every Sunday at 11:00 PM")

    def run_analysis(self):
        """Run the full analysis pipeline"""
        logger.info("Starting scheduled full analysis")
        try:
            result = self.pipeline.run_full_analysis()

            if result.get("status") == "success":
                logger.info(f"Analysis completed successfully: {result}")
            else:
                logger.error(f"Analysis failed: {result}")

        except Exception as e:
            logger.error(f"Scheduled analysis failed: {e}")

    def run_quick_check(self):
        """Run a quick check for immediate insights"""
        logger.info("Starting scheduled quick check")
        try:
            result = self.pipeline.run_quick_check()

            if result.get("status") == "success":
                logger.info(f"Quick check completed: {result}")
            else:
                logger.warning(f"Quick check failed: {result}")

        except Exception as e:
            logger.error(f"Scheduled quick check failed: {e}")

    def cleanup_files(self):
        """Clean up old files"""
        logger.info("Starting file cleanup")
        try:
            cleanup_old_files("data", days_to_keep=7)
            cleanup_old_files("output", days_to_keep=14)
            cleanup_old_files("reports", days_to_keep=30)
            logger.info("File cleanup completed")
        except Exception as e:
            logger.error(f"File cleanup failed: {e}")

    def run_scheduler(self):
        """Run the scheduler loop"""
        logger.info("Starting scheduler...")
        logger.info(f"Current time: {datetime.now()}")

        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


def main():
    """Main entry point for scheduled analysis"""
    analyzer = ScheduledAnalyzer()

    print("🕐 Fantasy Hockey Scheduled Analyzer")
    print("=" * 50)
    print("Scheduled tasks:")
    print("- Full analysis: Every Monday at 12:00 PM")
    print("- Quick check: Every day at 9:00 AM")
    print("- File cleanup: Every Sunday at 11:00 PM")
    print("=" * 50)
    print("Press Ctrl+C to stop")

    try:
        analyzer.run_scheduler()
    except KeyboardInterrupt:
        print("\n👋 Scheduler stopped by user")
        logger.info("Scheduler stopped by user")


if __name__ == "__main__":
    main()


