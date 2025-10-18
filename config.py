"""
Configuration settings for Fantasy Hockey Pipeline
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ESPN Fantasy Configuration
ESPN_S2 = os.getenv("ESPN_S2")
ESPN_SWID = os.getenv("ESPN_SWID")
LEAGUE_ID = os.getenv("LEAGUE_ID")
YEAR = int(os.getenv("YEAR", 2026))
TEAM_ID = os.getenv("TEAM_ID")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Analysis Configuration
ANALYSIS_SETTINGS = {
    "min_games_played": 5,  # Minimum games for analysis
    "recent_games_weight": 0.7,  # Weight for recent performance
    "season_weight": 0.3,  # Weight for season-long performance
    "max_recommendations": 15,  # Max players to recommend
    "min_fantasy_points": 2.0,  # Minimum fantasy points per game
}

# Fantasy Scoring Categories (based on your league settings)
SCORING_CATEGORIES = {
    # Skater categories
    "goals": 2,
    "assists": 1,
    "powerplay_points": 0.5,
    "shorthanded_points": 0.5,
    "shots_on_goal": 0.2,
    "hits": 0.4,
    "blocks": 0.8,
    # Goaltender categories
    "wins": 4,
    "goals_against": -1,
    "saves": 0.2,
    "shutouts": 3,
    "overtime_losses": 1,
}

# Web Dashboard Configuration
DASHBOARD_CONFIG = {
    "host": "0.0.0.0",
    "port": 8050,
    "debug": True,
}

# File Paths
DATA_DIR = "data"
OUTPUT_DIR = "output"
REPORTS_DIR = "reports"
