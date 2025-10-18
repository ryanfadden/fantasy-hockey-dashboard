"""
Fantasy Hockey Analysis Engine
Uses AI and statistical analysis to provide player recommendations
"""

import json
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from openai import OpenAI
from config import OPENAI_API_KEY, ANALYSIS_SETTINGS, SCORING_CATEGORIES

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FantasyHockeyAnalyzer:
    """Main analysis engine for fantasy hockey recommendations"""

    def __init__(self):
        """Initialize the analyzer with OpenAI client"""
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
        self.scoring_categories = SCORING_CATEGORIES
        self.analysis_settings = ANALYSIS_SETTINGS

    def analyze_player_pickups(
        self, my_team: Dict[str, Any], free_agents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze free agents and recommend pickups"""
        try:
            # Calculate fantasy points for all players
            analyzed_agents = []

            for agent in free_agents:
                try:
                    # Ensure fantasy points are calculated correctly
                    fantasy_points = self._calculate_fantasy_points(agent["stats"])
                    games_played = max(agent["stats"].get("games_played", 1), 1)
                    fantasy_points_per_game = fantasy_points / games_played

                    # Update agent data
                    agent["fantasy_points"] = fantasy_points
                    agent["fantasy_points_per_game"] = fantasy_points_per_game

                    # Add analysis metrics
                    agent["analysis"] = self._analyze_player_metrics(agent)
                    analyzed_agents.append(agent)

                    # Debug logging for defensemen
                    if (
                        agent.get("position") == "Defense"
                        and fantasy_points_per_game > 0
                    ):
                        logger.info(
                            f"Processed defenseman {agent.get('name', 'Unknown')}: {fantasy_points_per_game:.2f} FP/G"
                        )

                except Exception as e:
                    logger.warning(
                        f"Error processing player {agent.get('name', 'Unknown')}: {e}"
                    )
                    # Still add the player with basic data
                    agent["fantasy_points"] = 0
                    agent["fantasy_points_per_game"] = 0
                    agent["analysis"] = {
                        "consistency_rating": 0,
                        "upside_potential": 0,
                        "injury_risk": 0,
                        "position_scarcity": 0,
                        "recent_trend": "unknown",
                        "value_score": 0,
                    }
                    analyzed_agents.append(agent)

            # Filter and rank players
            recommendations = self._rank_and_filter_players(analyzed_agents, my_team)

            # Add AI insights
            if self.openai_client:
                recommendations = self._add_ai_insights(recommendations, my_team)

            return recommendations

        except Exception as e:
            logger.error(f"Error analyzing player pickups: {e}")
            return []

    def _calculate_fantasy_points(self, stats: Dict[str, Any]) -> float:
        """Calculate fantasy points based on league scoring"""
        total_points = 0.0

        for category, points_per_unit in self.scoring_categories.items():
            value = stats.get(category, 0)
            total_points += value * points_per_unit

        return total_points

    def _analyze_player_metrics(self, player: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze individual player metrics"""
        stats = player["stats"]
        games_played = max(stats.get("games_played", 1), 1)

        analysis = {
            "consistency_rating": self._calculate_consistency(stats),
            "upside_potential": self._calculate_upside(stats),
            "injury_risk": self._assess_injury_risk(player),
            "position_scarcity": self._assess_position_scarcity(player["position"]),
            "recent_trend": self._analyze_trend(player),
            "value_score": 0.0,  # Will be calculated later
        }

        return analysis

    def _calculate_consistency(self, stats: Dict[str, Any]) -> float:
        """Calculate player consistency rating (0-10)"""
        # This is a simplified version - in practice, you'd use historical game-by-game data
        games_played = stats.get("games_played", 0)
        if games_played < 5:
            return 5.0  # Neutral rating for small sample size

        # Higher consistency for players with more games and steady production
        consistency = min(10.0, games_played / 2.0)
        return consistency

    def _calculate_upside(self, stats: Dict[str, Any]) -> float:
        """Calculate upside potential (0-10)"""
        # Look for indicators of high upside
        upside_indicators = 0

        # High shooting percentage
        goals = stats.get("goals", 0)
        shots = stats.get("shots_on_goal", 0)
        if shots > 0 and goals / shots > 0.15:  # High shooting %
            upside_indicators += 2

        # Power play production
        if stats.get("powerplay_points", 0) > 0:
            upside_indicators += 1

        # Recent performance trend
        if stats.get("points", 0) > 10:  # Decent point total
            upside_indicators += 1

        return min(10.0, upside_indicators * 2.5)

    def _assess_injury_risk(self, player: Dict[str, Any]) -> float:
        """Assess injury risk (0-10, higher = more risk)"""
        injury_status = player.get("injury_status", "").lower()

        if "out" in injury_status:
            return 10.0
        elif "doubtful" in injury_status:
            return 8.0
        elif "questionable" in injury_status:
            return 6.0
        elif "probable" in injury_status:
            return 3.0
        else:
            return 1.0

    def _assess_position_scarcity(self, position: str) -> float:
        """Assess position scarcity (0-10, higher = more scarce)"""
        # Goalies and centers are typically more scarce
        scarcity_map = {"G": 9.0, "C": 7.0, "LW": 6.0, "RW": 6.0, "D": 5.0}
        return scarcity_map.get(position, 5.0)

    def _analyze_trend(self, player: Dict[str, Any]) -> str:
        """Analyze recent performance trend"""
        # This would ideally use recent game data
        # For now, return a placeholder
        return "stable"

    def _rank_and_filter_players(
        self, players: List[Dict[str, Any]], my_team: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Rank and filter players based on analysis"""
        # Get dynamic thresholds based on season progress
        min_games, min_total_points = self._get_smart_thresholds(players)

        # Filter players using dynamic thresholds
        filtered_players = []
        for p in players:
            games_played = p.get("stats", {}).get("games_played", 0)
            total_fantasy_points = p.get("fantasy_points", 0)
            
            # Must meet both thresholds
            if games_played >= min_games and total_fantasy_points >= min_total_points:
                filtered_players.append(p)

        logger.info(
            f"Dynamic thresholds: min_games={min_games}, min_total_points={min_total_points}"
        )
        logger.info(
            f"Filtered {len(filtered_players)} players from {len(players)} total"
        )

        # Calculate value scores
        for player in filtered_players:
            try:
                value_score = self._calculate_value_score(player)
                player["analysis"]["value_score"] = value_score

                # Debug logging for defensemen
                if player.get("position") == "Defense" and value_score > 0:
                    logger.info(
                        f"Defenseman {player.get('name', 'Unknown')} value score: {value_score:.2f}"
                    )

            except Exception as e:
                logger.warning(
                    f"Error calculating value score for {player.get('name', 'Unknown')}: {e}"
                )
                player["analysis"]["value_score"] = 0.0

        # Sort by value score
        sorted_players = sorted(
            filtered_players, key=lambda x: x["analysis"]["value_score"], reverse=True
        )

        # Return top recommendations
        max_recs = self.analysis_settings["max_recommendations"]
        return sorted_players[:max_recs]

    def _get_smart_thresholds(self, players: List[Dict[str, Any]]) -> tuple:
        """Calculate dynamic thresholds based on season progress"""
        if not players:
            return 3, 10  # Default fallback

        # Find max games played to determine season progress
        games_played = [p.get("stats", {}).get("games_played", 0) for p in players]
        max_games = max(games_played) if games_played else 0

        # Early season: be lenient to catch breakouts
        if max_games <= 10:
            min_games = 1  # Allow 1-game players in early season
            min_total_points = 5
        # Mid season: moderate thresholds
        elif max_games <= 30:
            min_games = max(3, int(max_games * 0.15))  # 15% of max games
            min_total_points = max(10, int(max_games * 0.8))  # ~0.8 pts/game
        # Late season: strict thresholds to avoid flukes
        else:
            min_games = max(5, int(max_games * 0.2))  # 20% of max games
            min_total_points = max(20, int(max_games * 1.0))  # ~1.0 pts/game

        logger.info(
            f"Season progress: max_games={max_games}, thresholds: min_games={min_games}, min_total_points={min_total_points}"
        )
        return min_games, min_total_points

    def _calculate_value_score(self, player: Dict[str, Any]) -> float:
        """Calculate overall value score for a player"""
        analysis = player["analysis"]

        # Weighted scoring (removed ownership and fixed injury risk)
        weights = {
            "fantasy_points_per_game": 0.4,  # Increased weight
            "consistency_rating": 0.25,  # Increased weight
            "upside_potential": 0.25,  # Increased weight
            "position_scarcity": 0.1,  # Reduced weight
            "injury_risk": 0.1,  # Positive weight (healthy = good)
        }

        score = 0.0
        score += player["fantasy_points_per_game"] * weights["fantasy_points_per_game"]
        score += analysis["consistency_rating"] * weights["consistency_rating"]
        score += analysis["upside_potential"] * weights["upside_potential"]
        score += analysis["position_scarcity"] * weights["position_scarcity"]
        score += analysis["injury_risk"] * weights["injury_risk"]

        # Apply position-based adjustments based on roster slots
        position = player.get("position", "")
        if position == "Goalie":
            # Penalty for goalies (only 2 starting slots vs 11 skater slots)
            score *= 0.6  # 40% penalty for goalies
        elif position == "Defense":
            # Boost for defensemen (scarce position, only 4 starters needed)
            score *= 1.15  # 15% boost for defensemen
        elif position in ["Center", "Left Wing", "Right Wing"]:
            # No boost for forwards (abundant position, 6 starters needed)
            score *= 1.0  # No boost for forwards

        # Add historical performance bonus for proven players
        historical_bonus = self._calculate_historical_bonus(player)
        score += historical_bonus

        # Apply sample size penalty for small sample sizes
        games_played = player.get("stats", {}).get("games_played", 0)
        if games_played < 5:
            # Penalty increases as sample size decreases
            sample_penalty = max(0.5, 1.0 - (5 - games_played) * 0.1)
            score *= sample_penalty
            logger.debug(
                f"Applied sample size penalty {sample_penalty:.2f} for {player.get('name', 'Unknown')} ({games_played} games)"
            )

        return max(0.0, score)

    def _calculate_historical_bonus(self, player: Dict[str, Any]) -> float:
        """Calculate historical performance bonus for proven players"""
        try:
            player_name = player.get("name", "")

            # Load All-Star Game appearances from external file
            all_star_players = self._load_all_star_data()
            appearances = all_star_players.get(player_name, 0)

            # Calculate bonus based on appearances
            if appearances >= 5:
                return 0.4  # Elite tier (increased from 0.3)
            elif appearances >= 3:
                return 0.35  # High tier (increased from 0.25)
            elif appearances >= 2:
                return 0.3  # Medium tier (increased from 0.2)
            elif appearances >= 1:
                return 0.2  # Low tier (increased from 0.15)
            else:
                return 0.0  # No bonus

        except Exception as e:
            logger.warning(f"Error calculating historical bonus: {e}")
            return 0.0

    def _load_all_star_data(self) -> Dict[str, int]:
        """Load All-Star Game appearances from external file"""
        try:
            import json
            import os

            file_path = "data/all_star_appearances.json"
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    data = json.load(f)
                    return data.get("all_star_appearances", {})
            else:
                logger.warning("All-Star data file not found, using empty data")
                return {}

        except Exception as e:
            logger.warning(f"Error loading All-Star data: {e}")
            return {}

    def _get_espn_field_name(self, category: str) -> str:
        """Map our scoring categories to ESPN field names"""
        mapping = {
            "goals": "G",
            "assists": "A",
            "powerplay_points": "PPP",
            "shorthanded_points": "SHP",
            "shots_on_goal": "SOG",
            "hits": "HIT",
            "blocks": "BLK",
            "wins": "W",
            "goals_against": "GA",
            "saves": "SV",
            "shutouts": "SO",
            "overtime_losses": "OTL",
        }
        return mapping.get(category, category)

    def _add_ai_insights(
        self, recommendations: List[Dict[str, Any]], my_team: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Add AI-powered insights to recommendations"""
        try:
            for player in recommendations:
                # Create context for AI analysis
                context = self._create_ai_context(player, my_team)

                # Get AI analysis
                ai_insight = self._get_ai_analysis(context)
                player["ai_insight"] = ai_insight

        except Exception as e:
            logger.error(f"Error adding AI insights: {e}")

        return recommendations

    def _create_ai_context(
        self, player: Dict[str, Any], my_team: Dict[str, Any]
    ) -> str:
        """Create context string for AI analysis"""
        context = f"""
        Player Analysis Request:
        
        Player: {player["name"]} ({player["position"]})
        Team: {player["team"]}
        Stats: {player["stats"]}
        Fantasy Points per Game: {player["fantasy_points_per_game"]:.2f}
        Ownership: {player.get("ownership_percentage", 0)}%
        Injury Status: {player.get("injury_status", "Healthy")}
        
        My Team Context:
        Team Name: {my_team.get("team_name", "Unknown")}
        Current Record: {my_team.get("record", "Unknown")}
        Roster Size: {len(my_team.get("roster", []))}
        
        Analysis Metrics:
        Consistency: {player["analysis"]["consistency_rating"]:.1f}/10
        Upside: {player["analysis"]["upside_potential"]:.1f}/10
        Injury Risk: {player["analysis"]["injury_risk"]:.1f}/10
        Position Scarcity: {player["analysis"]["position_scarcity"]:.1f}/10
        Value Score: {player["analysis"]["value_score"]:.1f}
        
        Please provide a brief analysis of this player's fantasy value and whether they would be a good pickup for my team.
        """
        return context

    def _get_ai_analysis(self, context: str) -> str:
        """Get AI analysis using OpenAI"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a fantasy hockey expert providing player analysis and pickup recommendations. Provide a brief 2-3 sentence explanation of why this player would be a good pickup, focusing on recent performance, consistency, and fantasy value.",
                    },
                    {"role": "user", "content": context},
                ],
                max_tokens=200,
                temperature=0.7,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error getting AI analysis: {e}")
            return "AI analysis unavailable"

    def generate_report(
        self, recommendations: List[Dict[str, Any]], my_team: Dict[str, Any]
    ) -> str:
        """Generate a comprehensive analysis report"""
        report = f"""
# Fantasy Hockey Analysis Report
## Team: {my_team.get("team_name", "Unknown")}
## Record: {my_team.get("record", "Unknown")}
## Analysis Date: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}

## Top Pickup Recommendations

"""

        for i, player in enumerate(recommendations, 1):
            report += f"""
### {i}. {player["name"]} ({player["position"]}) - {player["team"]}
- **Fantasy Points/Game**: {player["fantasy_points_per_game"]:.2f}
- **Value Score**: {player["analysis"]["value_score"]:.1f}/10
- **Consistency**: {player["analysis"]["consistency_rating"]:.1f}/10
- **Upside**: {player["analysis"]["upside_potential"]:.1f}/10
- **Injury Risk**: {player["analysis"]["injury_risk"]:.1f}/10
- **Ownership**: {player.get("ownership_percentage", 0)}%

**AI Insight**: {player.get("ai_insight", "No AI analysis available")}

---
"""

        return report

    def save_analysis(
        self,
        recommendations: List[Dict[str, Any]],
        filename: str = "analysis_results.json",
    ):
        """Save analysis results to file"""
        try:
            filepath = f"output/{filename}"
            with open(filepath, "w") as f:
                json.dump(recommendations, f, indent=2)
            logger.info(f"Analysis saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving analysis: {e}")


def main():
    """Test the analyzer"""
    analyzer = FantasyHockeyAnalyzer()

    # Load test data
    try:
        with open("data/my_team.json", "r") as f:
            my_team = json.load(f)

        with open("data/free_agents.json", "r") as f:
            free_agents = json.load(f)

        # Run analysis
        recommendations = analyzer.analyze_player_pickups(my_team, free_agents)

        # Generate report
        report = analyzer.generate_report(recommendations, my_team)

        # Save results
        analyzer.save_analysis(recommendations)

        with open("reports/analysis_report.md", "w") as f:
            f.write(report)

        print(f"Analysis complete! Generated {len(recommendations)} recommendations.")

    except FileNotFoundError:
        print("Test data not found. Run espn_client.py first to collect data.")


if __name__ == "__main__":
    main()
