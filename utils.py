"""
Utility functions for the Fantasy Hockey Pipeline
"""

import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional


def setup_logging(log_level: str = "INFO") -> None:
    """Set up logging configuration"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler(
                f"logs/fantasy_hockey_{datetime.now().strftime('%Y%m%d')}.log"
            ),
            logging.StreamHandler(),
        ],
    )


def load_json_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Load JSON data from file"""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning(f"File not found: {filepath}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from {filepath}: {e}")
        return None


def save_json_file(data: Dict[str, Any], filepath: str) -> bool:
    """Save data to JSON file"""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logging.error(f"Error saving JSON to {filepath}: {e}")
        return False


def format_player_name(player_name: str) -> str:
    """Format player name for display"""
    return player_name.strip().title()


def calculate_fantasy_points_per_game(
    stats: Dict[str, Any], games_played: int
) -> float:
    """Calculate fantasy points per game"""
    if games_played <= 0:
        return 0.0

    # Basic fantasy scoring (adjust based on your league)
    points = (
        stats.get("goals", 0) * 3
        + stats.get("assists", 0) * 2
        + stats.get("plus_minus", 0) * 1
        + stats.get("powerplay_points", 0) * 1
        + stats.get("shots_on_goal", 0) * 0.5
        + stats.get("hits", 0) * 0.5
        + stats.get("blocks", 0) * 0.5
    )

    return points / games_played


def get_position_abbreviation(position: str) -> str:
    """Get position abbreviation"""
    position_map = {
        "Goalkeeper": "G",
        "Center": "C",
        "Left Wing": "LW",
        "Right Wing": "RW",
        "Defenseman": "D",
        "Defense": "D",
    }
    return position_map.get(position, position)


def send_notification(title: str, message: str) -> None:
    """Send notification (placeholder for future implementation)"""
    # This could be extended to send emails, Slack messages, etc.
    logging.info(f"NOTIFICATION: {title} - {message}")


def validate_espn_credentials() -> bool:
    """Validate ESPN credentials are available"""
    from config import ESPN_S2, ESPN_SWID, LEAGUE_ID

    if not LEAGUE_ID:
        logging.error("LEAGUE_ID not set in environment variables")
        return False

    if not ESPN_S2 or not ESPN_SWID:
        logging.warning("ESPN_S2 or ESPN_SWID not set - using public league access")

    return True


def validate_openai_credentials() -> bool:
    """Validate OpenAI credentials are available"""
    from config import OPENAI_API_KEY

    if not OPENAI_API_KEY:
        logging.warning("OPENAI_API_KEY not set - AI analysis will be limited")
        return False

    return True


def get_latest_data_file(directory: str, pattern: str) -> Optional[str]:
    """Get the most recent file matching a pattern"""
    try:
        files = [f for f in os.listdir(directory) if pattern in f]
        if not files:
            return None

        # Sort by modification time
        files.sort(
            key=lambda x: os.path.getmtime(os.path.join(directory, x)), reverse=True
        )
        return os.path.join(directory, files[0])
    except Exception as e:
        logging.error(f"Error getting latest file: {e}")
        return None


def cleanup_old_files(directory: str, days_to_keep: int = 7) -> None:
    """Clean up old files in directory"""
    try:
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)

        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                file_time = os.path.getmtime(filepath)
                if file_time < cutoff_time:
                    os.remove(filepath)
                    logging.info(f"Cleaned up old file: {filename}")

    except Exception as e:
        logging.error(f"Error cleaning up files: {e}")


def format_timestamp(timestamp: str) -> str:
    """Format timestamp for display"""
    try:
        dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return timestamp


def create_backup(data: Dict[str, Any], backup_type: str) -> str:
    """Create backup of data"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{backup_type}_{timestamp}.json"
    backup_path = f"data/backups/{backup_filename}"

    if save_json_file(data, backup_path):
        logging.info(f"Backup created: {backup_filename}")
        return backup_path
    else:
        logging.error(f"Failed to create backup: {backup_filename}")
        return ""


def check_system_requirements() -> Dict[str, bool]:
    """Check if system requirements are met"""
    requirements = {
        "python_version": True,  # Assume Python 3.7+
        "required_packages": True,  # Will be checked by import errors
        "data_directory": os.path.exists("data"),
        "output_directory": os.path.exists("output"),
        "reports_directory": os.path.exists("reports"),
        "espn_credentials": validate_espn_credentials(),
        "openai_credentials": validate_openai_credentials(),
    }

    return requirements


def print_system_status() -> None:
    """Print system status"""
    requirements = check_system_requirements()

    print("🔍 Fantasy Hockey Pipeline System Status:")
    print("=" * 50)

    for requirement, status in requirements.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {requirement.replace('_', ' ').title()}")

    print("=" * 50)

    if all(requirements.values()):
        print("🎉 All systems ready!")
    else:
        print("⚠️  Some requirements not met. Check configuration.")


if __name__ == "__main__":
    print_system_status()


