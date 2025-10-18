"""
ESPN Fantasy Hockey API Client
Handles all interactions with ESPN's fantasy hockey API
"""

import json
import logging
from typing import List, Dict, Optional, Any
from espn_api.hockey import League
from config import ESPN_S2, ESPN_SWID, LEAGUE_ID, YEAR, TEAM_ID

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ESPNFantasyClient:
    """Client for interacting with ESPN Fantasy Hockey API"""

    def __init__(self):
        """Initialize the ESPN client with authentication"""
        self.league_id = LEAGUE_ID
        self.year = YEAR
        self.team_id = TEAM_ID

        # Initialize league connection
        try:
            if ESPN_S2 and ESPN_SWID:
                self.league = League(
                    league_id=self.league_id,
                    year=self.year,
                    espn_s2=ESPN_S2,
                    swid=ESPN_SWID,
                )
                logger.info("Connected to ESPN Fantasy Hockey with authentication")
            else:
                self.league = League(league_id=self.league_id, year=self.year)
                logger.info("Connected to ESPN Fantasy Hockey (public league)")

        except Exception as e:
            logger.error(f"Failed to connect to ESPN Fantasy Hockey: {e}")
            raise

    def get_my_team(self) -> Dict[str, Any]:
        """Get your team's roster and information"""
        try:
            # Find your team
            my_team = None
            for team in self.league.teams:
                if str(team.team_id) == str(self.team_id):
                    my_team = team
                    break

            if not my_team:
                logger.error(f"Team with ID {self.team_id} not found")
                return {}

            # Get roster data
            roster_data = []
            for player in my_team.roster:
                player_info = {
                    "id": player.playerId,
                    "name": player.name,
                    "position": player.position,
                    "team": player.proTeam,
                    "injury_status": getattr(player, "injuryStatus", ""),
                    "stats": self._get_player_stats(player),
                    "recent_performance": self._get_recent_performance(player),
                    "last_year_stats": self._get_last_year_stats(player),
                }
                roster_data.append(player_info)

            return {
                "team_name": my_team.team_name,
                "team_id": my_team.team_id,
                "roster": roster_data,
                "record": f"{my_team.wins}-{my_team.losses}-{my_team.ties}",
                "points": getattr(my_team, "points", 0),
            }

        except Exception as e:
            logger.error(f"Error getting team data: {e}")
            return {}

    def get_all_teams_data(self) -> List[Dict[str, Any]]:
        """Get roster data from all teams for comparison purposes"""
        try:
            all_teams_data = []

            for team in self.league.teams:
                team_data = {
                    "team_name": team.team_name,
                    "team_id": team.team_id,
                    "roster": [],
                }

                for player in team.roster:
                    player_info = {
                        "id": player.playerId,
                        "name": player.name,
                        "position": player.position,
                        "team": player.proTeam,
                        "injury_status": getattr(player, "injuryStatus", ""),
                        "stats": self._get_player_stats(player),
                        "recent_performance": self._get_recent_performance(player),
                    }
                    team_data["roster"].append(player_info)

                all_teams_data.append(team_data)

            return all_teams_data

        except Exception as e:
            logger.error(f"Error getting all teams data: {e}")
            return []

    def get_free_agents(self, position: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available free agents, optionally filtered by position"""
        try:
            # Get free agents with optimized limit
            free_agents = self.league.free_agents(size=500)

            if position:
                free_agents = [p for p in free_agents if p.position == position]

            agent_data = []
            for player in free_agents:
                player_info = {
                    "id": player.playerId,
                    "name": player.name,
                    "position": player.position,
                    "team": player.proTeam,
                    "injury_status": getattr(player, "injuryStatus", ""),
                    "stats": self._get_player_stats(player),
                    "recent_performance": self._get_recent_performance(player),
                    "last_year_stats": self._get_last_year_stats(player),
                    "ownership_percentage": getattr(player, "ownership", 0),
                    "projected_points": getattr(player, "projected_points", 0),
                }
                agent_data.append(player_info)

            return agent_data

        except Exception as e:
            logger.error(f"Error getting free agents: {e}")
            return []

    def get_league_standings(self) -> List[Dict[str, Any]]:
        """Get current league standings"""
        try:
            standings = []
            for team in self.league.teams:
                team_info = {
                    "team_name": team.team_name,
                    "team_id": team.team_id,
                    "record": f"{team.wins}-{team.losses}-{team.ties}",
                    "points": getattr(team, "points", 0),
                    "rank": getattr(team, "standing", 0),
                }
                standings.append(team_info)

            return sorted(standings, key=lambda x: x["rank"])

        except Exception as e:
            logger.error(f"Error getting league standings: {e}")
            return []

    def get_matchup_data(self) -> Dict[str, Any]:
        """Get current matchup information"""
        try:
            current_week = self.league.current_week
            matchup_data = {"current_week": current_week, "matchups": []}

            for matchup in self.league.scoreboard():
                matchup_info = {
                    "home_team": matchup.home_team.team_name,
                    "away_team": matchup.away_team.team_name,
                    "home_score": getattr(matchup, "home_score", 0),
                    "away_score": getattr(matchup, "away_score", 0),
                    "week": getattr(matchup, "matchup_period_id", 0),
                }
                matchup_data["matchups"].append(matchup_info)

            return matchup_data

        except Exception as e:
            logger.error(f"Error getting matchup data: {e}")
            return {}

    def _get_player_stats(self, player) -> Dict[str, Any]:
        """Extract player statistics"""
        try:
            stats = getattr(player, "stats", {})

            # ESPN API returns stats in nested format: 'Total 2026' -> 'total' -> actual stats
            total_stats = stats.get("Total 2026", {}).get("total", {})

            # For goalies, use GS (Games Started) instead of GP (Games Played)
            games_played = int(total_stats.get("GP", 0))
            if games_played == 0:  # If no GP, try GS for goalies
                games_played = int(total_stats.get("GS", 0))

            # Calculate fantasy points using the same method as historical data
            fantasy_points = self._calculate_fantasy_points_from_stats(total_stats)
            fantasy_points_per_game = fantasy_points / games_played if games_played > 0 else 0.0

            return {
                "games_played": games_played,
                "goals": int(total_stats.get("G", 0)),
                "assists": int(total_stats.get("A", 0)),
                "points": int(total_stats.get("G", 0) + total_stats.get("A", 0)),
                "plus_minus": int(total_stats.get("+/-", 0)),
                "powerplay_points": int(total_stats.get("PPP", 0)),
                "shorthanded_points": int(total_stats.get("SHP", 0)),
                "shots_on_goal": int(total_stats.get("SOG", 0)),
                "hits": int(total_stats.get("HIT", 0)),
                "blocks": int(total_stats.get("BLK", 0)),
                "faceoffs_won": int(total_stats.get("FOW", 0)),
                "penalty_minutes": int(total_stats.get("PIM", 0)),
                # Goaltender stats
                "wins": int(total_stats.get("W", 0)),
                "goals_against": int(total_stats.get("GA", 0)),
                "saves": int(total_stats.get("SV", 0)),
                "shutouts": int(total_stats.get("SO", 0)),
                "overtime_losses": int(total_stats.get("OTL", 0)),
                # Fantasy points
                "fantasy_points": fantasy_points,
                "fantasy_points_per_game": fantasy_points_per_game,
            }
        except Exception as e:
            logger.warning(f"Error getting stats for {player.name}: {e}")
            return {
                "games_played": 0,
                "goals": 0,
                "assists": 0,
                "points": 0,
                "plus_minus": 0,
                "powerplay_points": 0,
                "shorthanded_points": 0,
                "shots_on_goal": 0,
                "hits": 0,
                "blocks": 0,
                "faceoffs_won": 0,
                "penalty_minutes": 0,
                "wins": 0,
                "goals_against": 0,
                "saves": 0,
                "shutouts": 0,
                "overtime_losses": 0,
                "fantasy_points": 0,
                "fantasy_points_per_game": 0.0,
            }

    def _get_recent_performance(self, player) -> Dict[str, Any]:
        """Get recent performance metrics (last 7 games)"""
        try:
            stats = getattr(player, "stats", {})

            # Get last 7 games stats
            last_7_stats = stats.get("Last 7 2026", {}).get("total", {})
            last_7_points = int(last_7_stats.get("G", 0) + last_7_stats.get("A", 0))
            last_7_games = int(last_7_stats.get("GP", 1))  # Avoid division by zero

            return {
                "last_7_games_points": last_7_points,
                "last_7_games_avg": last_7_points / last_7_games
                if last_7_games > 0
                else 0.0,
                "trend": "up" if last_7_points > 0 else "stable",
            }
        except Exception as e:
            logger.warning(f"Error getting recent performance for {player.name}: {e}")
            return {
                "last_7_games_points": 0,
                "last_7_games_avg": 0.0,
                "trend": "stable",
            }

    def _get_last_year_stats(self, player) -> Dict[str, Any]:
        """Extract last year's performance data for comparison (optimized)"""
        try:
            stats = getattr(player, "stats", {})

            # Only check for 2025 data (last year) - simplified approach
            last_year_stats = stats.get("Total 2025", {}).get("total", {})

            if not last_year_stats:
                return {
                    "games_played": 0,
                    "fantasy_points_per_game": 0.0,
                    "years_analyzed": 0,
                }

            # Calculate fantasy points for last year
            last_year_fp = self._calculate_fantasy_points_from_stats(last_year_stats)

            # Get games played (use GS for goalies if GP is 0)
            last_year_gp = int(last_year_stats.get("GP", 0))
            if last_year_gp == 0:
                last_year_gp = int(last_year_stats.get("GS", 0))

            if last_year_gp == 0:
                return {
                    "games_played": 0,
                    "fantasy_points_per_game": 0.0,
                    "years_analyzed": 0,
                }

            last_year_fp_per_game = last_year_fp / last_year_gp

            return {
                "games_played": last_year_gp,
                "fantasy_points": last_year_fp,
                "fantasy_points_per_game": last_year_fp_per_game,
                "season": "2024-2025",
                "years_analyzed": 1,
            }
        except Exception as e:
            logger.warning(f"Error getting last year stats for {player.name}: {e}")
            return {
                "games_played": 0,
                "fantasy_points_per_game": 0.0,
                "years_analyzed": 0,
            }

    def _get_additional_historical_data(self, player) -> List[Dict[str, Any]]:
        """Try to get historical data from other league years"""
        additional_years = []

        # Try to get data from 2024 league
        try:
            from espn_api.hockey import League

            league_2024 = League(
                league_id=self.league_id, year=2024, espn_s2=ESPN_S2, swid=ESPN_SWID
            )
            team_2024 = league_2024.teams[0]

            # Find the same player in 2024
            for p in team_2024.roster:
                if p.playerId == player.playerId:
                    stats_2024 = getattr(p, "stats", {})
                    # Look for 2023 data in 2024 league
                    if "Total 2023" in stats_2024:
                        year_stats = stats_2024["Total 2023"].get("total", {})
                        if year_stats:
                            year_fp = self._calculate_fantasy_points_from_stats(
                                year_stats
                            )
                            year_gp = int(year_stats.get("GP", 0))
                            if year_gp == 0:
                                year_gp = int(year_stats.get("GS", 0))

                            if year_gp > 0:
                                year_fp_per_game = year_fp / year_gp
                                additional_years.append(
                                    {
                                        "year": "2023",
                                        "games_played": year_gp,
                                        "fantasy_points": year_fp,
                                        "fantasy_points_per_game": year_fp_per_game,
                                    }
                                )
                    break
        except Exception as e:
            logger.debug(f"Could not get 2024 league data: {e}")

        return additional_years

    def _calculate_fantasy_points_from_stats(self, stats: Dict[str, Any]) -> float:
        """Calculate fantasy points from raw stats"""
        from config import SCORING_CATEGORIES

        # Map ESPN stat names to our scoring categories
        stat_mapping = {
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

        total_points = 0.0
        for category, points_per_unit in SCORING_CATEGORIES.items():
            espn_stat = stat_mapping.get(category, category)
            value = stats.get(espn_stat, 0)
            total_points += value * points_per_unit
        return total_points

    def save_data_to_file(self, data: Dict[str, Any], filename: str):
        """Save data to JSON file"""
        try:
            filepath = f"data/{filename}"
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Data saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving data to file: {e}")


def main():
    """Test the ESPN client"""
    client = ESPNFantasyClient()

    # Test getting team data
    team_data = client.get_my_team()
    if team_data:
        print(f"Team: {team_data['team_name']}")
        print(f"Record: {team_data['record']}")
        print(f"Roster size: {len(team_data['roster'])}")

    # Test getting free agents
    free_agents = client.get_free_agents()
    print(f"Free agents available: {len(free_agents)}")

    # Save data
    client.save_data_to_file(team_data, "my_team.json")
    client.save_data_to_file(free_agents, "free_agents.json")


if __name__ == "__main__":
    main()
