"""
ESPN Fantasy Football API client.

Mirrors the method shapes of espn_client.ESPNFantasyClient (get_my_team,
get_all_teams_data, get_free_agents, get_league_standings, get_matchup_data)
so the MCP server can serve football leagues through the same tools.

Unlike hockey, ESPN scores football players with each league's own scoring
settings, so the fantasy_points fields here are league-accurate as returned.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from espn_api.football import League

load_dotenv()

ESPN_S2 = os.getenv("ESPN_S2")
ESPN_SWID = os.getenv("ESPN_SWID")

logger = logging.getLogger(__name__)


class ESPNFootballClient:
    """Client for interacting with an ESPN Fantasy Football league."""

    def __init__(self, league_id, team_id, year):
        self.league_id = int(league_id)
        self.team_id = int(team_id)
        self.year = int(year)

        if ESPN_S2 and ESPN_SWID:
            self.league = League(
                league_id=self.league_id,
                year=self.year,
                espn_s2=ESPN_S2,
                swid=ESPN_SWID,
            )
        else:
            self.league = League(league_id=self.league_id, year=self.year)
        logger.info(
            f"Connected to ESPN Fantasy Football league {self.league_id} ({self.year})"
        )

    @property
    def league_name(self) -> str:
        return getattr(getattr(self.league, "settings", None), "name", "") or ""

    # ------------------------------------------------------------------
    # Public API (same shapes as the hockey client)
    # ------------------------------------------------------------------

    def get_my_team(self) -> Dict[str, Any]:
        my_team = self._find_team(self.team_id)
        if my_team is None:
            logger.error(f"Team with ID {self.team_id} not found")
            return {}
        return {
            "team_name": my_team.team_name,
            "team_id": my_team.team_id,
            "record": self._record(my_team),
            "points_for": round(getattr(my_team, "points_for", 0) or 0, 1),
            "points_against": round(getattr(my_team, "points_against", 0) or 0, 1),
            "roster": [self._player_info(p) for p in my_team.roster],
        }

    def get_all_teams_data(self) -> List[Dict[str, Any]]:
        return [
            {
                "team_name": team.team_name,
                "team_id": team.team_id,
                "roster": [self._player_info(p) for p in team.roster],
            }
            for team in self.league.teams
        ]

    def get_free_agents(self, position: Optional[str] = None) -> List[Dict[str, Any]]:
        agents = self.league.free_agents(size=500)
        if position:
            agents = [p for p in agents if getattr(p, "position", "") == position]
        return [self._player_info(p) for p in agents]

    def get_league_standings(self) -> List[Dict[str, Any]]:
        try:
            ordered = self.league.standings()
        except Exception:
            ordered = sorted(
                self.league.teams, key=lambda t: getattr(t, "standing", 0)
            )
        return [
            {
                "rank": index + 1,
                "team_name": team.team_name,
                "team_id": team.team_id,
                "record": self._record(team),
                "points_for": round(getattr(team, "points_for", 0) or 0, 1),
                "points_against": round(getattr(team, "points_against", 0) or 0, 1),
            }
            for index, team in enumerate(ordered)
        ]

    def get_matchup_data(self) -> Dict[str, Any]:
        matchups = []
        for matchup in self.league.scoreboard():
            matchups.append(
                {
                    "home_team": self._team_name(matchup, "home_team"),
                    "away_team": self._team_name(matchup, "away_team"),
                    "home_score": getattr(matchup, "home_score", 0),
                    "away_score": getattr(matchup, "away_score", 0),
                }
            )
        return {"current_week": self.league.current_week, "matchups": matchups}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _find_team(self, team_id):
        for team in self.league.teams:
            if str(team.team_id) == str(team_id):
                return team
        return None

    @staticmethod
    def _record(team) -> str:
        return f"{team.wins}-{team.losses}-{team.ties}"

    @staticmethod
    def _team_name(matchup, side: str) -> str:
        team = getattr(matchup, side, None)
        return getattr(team, "team_name", "BYE") if team else "BYE"

    def _player_info(self, player) -> Dict[str, Any]:
        stats = getattr(player, "stats", {}) or {}
        season = stats.get(0, {}) or {}
        breakdown = {
            key: round(value, 1)
            for key, value in (season.get("breakdown") or {}).items()
            if isinstance(value, (int, float)) and abs(value) >= 0.5
        }

        total_points = getattr(player, "total_points", 0) or 0
        avg_points = getattr(player, "avg_points", 0) or 0
        if not avg_points and total_points:
            weeks_played = sum(
                1
                for week, entry in stats.items()
                if week != 0 and (entry or {}).get("points")
            )
            if weeks_played:
                avg_points = total_points / weeks_played

        return {
            "id": player.playerId,
            "name": player.name,
            "position": getattr(player, "position", ""),
            "team": getattr(player, "proTeam", ""),
            "injury_status": getattr(player, "injuryStatus", ""),
            "stats": {
                # Scored with this league's own scoring settings by ESPN.
                "fantasy_points": round(total_points, 1),
                "fantasy_points_per_game": round(avg_points, 2),
                "projected_total_points": round(
                    getattr(player, "projected_total_points", 0) or 0, 1
                ),
                "projected_avg_points": round(
                    getattr(player, "projected_avg_points", 0) or 0, 2
                ),
                "percent_owned": round(getattr(player, "percent_owned", 0) or 0, 1),
                "season_breakdown": breakdown,
            },
        }
