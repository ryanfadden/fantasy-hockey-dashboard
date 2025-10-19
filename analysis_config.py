"""
Fantasy Hockey Analysis Configuration
Centralized, human-readable configuration for all analysis parameters and prompts
"""

# =============================================================================
# VALUE SCORING CONFIGURATION
# =============================================================================

VALUE_SCORING = {
    "weights": {
        "fantasy_points_per_game": 0.5,  # Primary factor - raw performance
        "consistency_rating": 0.25,  # Reliability factor
        "upside_potential": 0.2,  # Growth potential
        "position_scarcity": 0.05,  # Position rarity bonus
    },
    "consistency_thresholds": {
        "excellent": 0.8,  # 80%+ games with good production
        "good": 0.6,  # 60%+ games with good production
        "average": 0.4,  # 40%+ games with good production
        "poor": 0.2,  # 20%+ games with good production
    },
    "upside_categories": {
        "rookie": 0.3,  # Rookies get upside boost
        "sophomore": 0.2,  # Second year players
        "veteran": 0.1,  # Established veterans
        "declining": -0.1,  # Players showing decline
    },
    "position_scarcity_multipliers": {
        "C": 1.0,  # Centers are common
        "LW": 1.1,  # Left wings slightly scarce
        "RW": 1.2,  # Right wings more scarce
        "D": 1.3,  # Defensemen scarcer
        "G": 1.5,  # Goalies most scarce
    },
    "historical_bonus": {
        "all_star_games": 0.1,  # Per all-star appearance
        "awards": 0.2,  # Per major award
        "playoff_performance": 0.15,  # Per playoff appearance
    },
}

# =============================================================================
# RECOMMENDATION THRESHOLDS
# =============================================================================

RECOMMENDATION_THRESHOLDS = {
    "min_value_score": 4.0,  # Minimum value score for recommendations
    "min_fantasy_points": 2.0,  # Minimum FP/G for consideration
    "min_games_played": 5,  # Minimum games for analysis
    "max_recommendations": 20,  # Maximum players to recommend
}

# =============================================================================
# SWAP ANALYSIS CONFIGURATION
# =============================================================================

SWAP_ANALYSIS = {
    "thresholds": {
        "must_swap": 6.0,  # Strong upgrade threshold
        "consider_swap": 3.0,  # Moderate upgrade threshold
        "keep": 0.0,  # Below this = keep player
    },
    "bonus_factors": {
        "position_match": 2.0,  # Bonus for same position
        "historical_precedence": 1.5,  # Bonus for proven track record
        "sample_size": 1.0,  # Bonus for larger sample size
    },
    "penalty_factors": {
        "injury_risk": -1.0,  # Penalty for injury concerns
        "age_decline": -0.5,  # Penalty for aging players
        "limited_upside": -0.3,  # Penalty for capped potential
    },
}

# =============================================================================
# OPENAI PROMPTS
# =============================================================================

OPENAI_PROMPTS = {
    "swap_analysis": {
        "system_message": """You are a fantasy hockey expert analyst with deep knowledge of NHL players, team dynamics, and fantasy scoring systems. You provide detailed, actionable analysis for fantasy hockey decisions.

Your analysis should be:
- Data-driven and specific
- Considerate of sample size and recent trends
- Aware of team situations and role changes
- Focused on actionable recommendations
- Written in a professional but accessible tone""",
        "user_prompt_template": """Perform a comprehensive fantasy hockey analysis comparing {current_player_name} and {target_player_name}.

LEAGUE SCORING SYSTEM:
{scoring_system}

CURRENT PLAYER: {current_player_name}
- Position: {current_position}
- Team: {current_team}
- Current FP/G: {current_fp_per_game:.2f}
- Games Played: {current_games_played}
- Stats: {current_stats}
- Value Score: {current_value_score:.2f}

POTENTIAL TARGET: {target_player_name}
- Position: {target_position}
- Team: {target_team}
- Current FP/G: {target_fp_per_game:.2f}
- Games Played: {target_games_played}
- Stats: {target_stats}
- Value Score: {target_value_score:.2f}

ANALYSIS REQUEST:
I am considering dropping {current_player_name} for {target_player_name}.

Please analyze these players under our custom scoring system considering:
1. Current season performance and sample size
2. Historical track record and career trends
3. Team situations and role expectations
4. Position scarcity and roster construction
5. Risk vs reward factors

Provide your analysis in this format:

### Player Comparison
[Detailed comparison with exact FP/G calculations using our scoring system]

### Context
[Team roles, historical performance, and strategic considerations]

### Verdict
[Clear recommendation: DROP, KEEP, or CONSIDER with specific reasoning]

### Summary
[Actionable recommendation with key factors]

Be specific about fantasy point calculations using our exact scoring system.""",
        "scoring_system": """Skater Scoring:
- Goals (G): 2 points
- Assists (A): 1 point
- Power Play Points (PPP): 0.5 points
- Short Handed Points (SHP): 0.5 points
- Shots on Goal (SOG): 0.2 points
- Hits (HIT): 0.4 points
- Blocked Shots (BLK): 0.8 points

Goaltender Scoring:
- Wins (W): 4 points
- Goals Against (GA): -1 point
- Saves (SV): 0.2 points
- Shutouts (SO): 3 points
- Overtime Losses (OTL): 1 point""",
    },
    "team_analysis": {
        "system_message": """You are a fantasy hockey expert who provides concise, actionable recommendations for roster management. Focus on clear, data-driven advice.""",
        "analysis_instructions": """Analyze each player on the roster and provide:
1. Recommendation: Keep, Consider Swap, or Must Swap
2. Rationale: Brief explanation with specific metrics
3. Target: If swap recommended, suggest best available replacement
4. Reasoning: Why this recommendation makes sense

Consider:
- Current performance vs available alternatives
- Sample size and reliability
- Position scarcity
- Historical track record
- Team situation and role changes""",
    },
}

# =============================================================================
# ANALYSIS SETTINGS
# =============================================================================

ANALYSIS_SETTINGS = {
    "min_games_played": 5,
    "recent_games_weight": 0.7,
    "season_weight": 0.3,
    "max_recommendations": 20,
    "min_fantasy_points": 2.0,
}

# =============================================================================
# FANTASY SCORING CATEGORIES
# =============================================================================

SCORING_CATEGORIES = {
    # Skater Scoring
    "goals": 2.0,
    "assists": 1.0,
    "powerplay_points": 0.5,
    "shorthanded_points": 0.5,
    "shots_on_goal": 0.2,
    "hits": 0.4,
    "blocks": 0.8,
    # Goaltender Scoring
    "wins": 4.0,
    "goals_against": -1.0,
    "saves": 0.2,
    "shutouts": 3.0,
    "overtime_losses": 1.0,
}

# =============================================================================
# DASHBOARD CONFIGURATION
# =============================================================================

DASHBOARD_CONFIG = {
    "title": "Fantasy Hockey Analysis Dashboard",
    "refresh_interval": 5 * 60 * 1000,  # 5 minutes in milliseconds
    "max_display_players": 50,
    "tabs": ["recommendations", "my-team", "swap-analysis"],
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_value_score_weights():
    """Get the current value scoring weights"""
    return VALUE_SCORING["weights"].copy()


def get_recommendation_thresholds():
    """Get the current recommendation thresholds"""
    return RECOMMENDATION_THRESHOLDS.copy()


def get_swap_analysis_config():
    """Get the current swap analysis configuration"""
    return SWAP_ANALYSIS.copy()


def get_openai_prompt(prompt_type, **kwargs):
    """Get formatted OpenAI prompt with variables substituted"""
    if prompt_type not in OPENAI_PROMPTS:
        raise ValueError(f"Unknown prompt type: {prompt_type}")

    prompt_config = OPENAI_PROMPTS[prompt_type]

    if "user_prompt_template" in prompt_config:
        template = prompt_config["user_prompt_template"]
        return template.format(**kwargs)

    return prompt_config


def update_value_score_weight(factor, new_weight):
    """Update a value score weight"""
    if factor in VALUE_SCORING["weights"]:
        VALUE_SCORING["weights"][factor] = new_weight
        return True
    return False


def update_recommendation_threshold(threshold, new_value):
    """Update a recommendation threshold"""
    if threshold in RECOMMENDATION_THRESHOLDS:
        RECOMMENDATION_THRESHOLDS[threshold] = new_value
        return True
    return False


def update_swap_threshold(threshold_type, new_value):
    """Update a swap analysis threshold"""
    if threshold_type in SWAP_ANALYSIS["thresholds"]:
        SWAP_ANALYSIS["thresholds"][threshold_type] = new_value
        return True
    return False
