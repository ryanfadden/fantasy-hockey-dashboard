#!/usr/bin/env python3
"""
MCP server for the Fantasy Hockey pipeline.

Exposes live ESPN league data and the statistical pickup analysis as MCP
tools over Streamable HTTP, so external AI assistants can query the team.

Auth: if MCP_AUTH_TOKEN is set, every request to the MCP endpoint must carry
it either as "Authorization: Bearer <token>" or as a "?key=<token>" query
parameter (for clients that cannot set custom headers).

Run locally:  python mcp_server.py   -> http://localhost:8000/mcp
On Railway:   deployed as its own service via railway-mcp.json.
"""

import copy
import json
import logging
import os
import secrets
import time
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs

from dotenv import load_dotenv

load_dotenv()

from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fantasy-hockey-mcp")

PORT = int(os.getenv("PORT", "8000"))

mcp = FastMCP(
    "fantasy-hockey",
    instructions=(
        "Live data and analysis for Ryan's ESPN fantasy leagues (hockey and "
        "football). Call list_leagues to see the configured leagues and each "
        "one's sport; every data tool takes an optional 'league' argument "
        "(name, partial name, or league id) and defaults to the first league. "
        "Stats come straight from ESPN at call time (cached ~10 minutes). "
        "Hockey fantasy points are computed with the scoring in "
        "get_scoring_config; football points come from ESPN already scored "
        "with each league's own settings."
    ),
    stateless_http=True,
    json_response=True,
    host="0.0.0.0",
    port=PORT,
)

# ---------------------------------------------------------------------------
# Cached ESPN access
# ---------------------------------------------------------------------------

CACHE_TTL_SECONDS = 600

_cache: Dict[str, Dict[str, Any]] = {}


def _cached(key: str, loader, refresh: bool = False):
    entry = _cache.get(key)
    if refresh or entry is None or time.time() - entry["ts"] > CACHE_TTL_SECONDS:
        _cache[key] = entry = {"ts": time.time(), "value": loader()}
    return entry["value"]


def _load_leagues():
    """League registry: LEAGUES_JSON env var (JSON array of objects with
    name, league_id, team_id and optional year/sport), falling back to the
    single league configured via LEAGUE_ID/TEAM_ID/YEAR. sport is "hockey"
    (default) or "football"."""
    default_year = int(os.getenv("YEAR", "2026"))
    raw = os.getenv("LEAGUES_JSON", "").strip()
    if raw:
        leagues = json.loads(raw)
    else:
        leagues = [
            {
                "name": "default",
                "league_id": os.getenv("LEAGUE_ID"),
                "team_id": os.getenv("TEAM_ID"),
            }
        ]
    for lg in leagues:
        lg.setdefault("year", default_year)
        lg["sport"] = str(lg.get("sport", "hockey")).lower()
        lg["league_id"] = str(lg["league_id"])
        lg["team_id"] = str(lg["team_id"])
    return leagues


LEAGUES = _load_leagues()


def _resolve_league(league: Optional[str]) -> Dict[str, Any]:
    """Match a league by (partial) name or league id; default: first league."""
    if not league:
        return LEAGUES[0]
    needle = league.strip().lower()
    for lg in LEAGUES:
        if needle == lg["league_id"] or needle == lg["name"].lower():
            return lg
    for lg in LEAGUES:
        if needle in lg["name"].lower():
            return lg
    raise ValueError(
        f"Unknown league {league!r}. Configured leagues: "
        + ", ".join(f"{lg['name']} (id {lg['league_id']})" for lg in LEAGUES)
    )


def _client(lg: Dict[str, Any]):
    def make():
        if lg["sport"] == "football":
            from espn_football_client import ESPNFootballClient

            return ESPNFootballClient(
                league_id=lg["league_id"], team_id=lg["team_id"], year=lg["year"]
            )
        from espn_client import ESPNFantasyClient

        return ESPNFantasyClient(
            league_id=lg["league_id"], team_id=lg["team_id"], year=lg["year"]
        )

    return _cached(f"client:{lg['league_id']}", make)


def _require_hockey(lg: Dict[str, Any], tool: str):
    if lg["sport"] != "hockey":
        raise ValueError(
            f"{tool} only works for hockey leagues; {lg['name']!r} is a "
            f"{lg['sport']} league. Use get_free_agents (sorted by fantasy "
            "points per game, scored with the league's own settings) instead."
        )


def _league_key(name: str, lg: Dict[str, Any]) -> str:
    return f"{name}:{lg['league_id']}"


POSITION_ALIASES = {
    "c": "Center",
    "lw": "Left Wing",
    "rw": "Right Wing",
    "d": "Defense",
    "g": "Goalie",
}

FOOTBALL_POSITION_ALIASES = {
    "dst": "D/ST",
    "d/st": "D/ST",
    "def": "D/ST",
    "defense": "D/ST",
}


def _normalize_position(position: Optional[str], sport: str = "hockey") -> Optional[str]:
    if not position:
        return None
    needle = position.strip().lower()
    if sport == "football":
        # ESPN football positions are abbreviations: QB, RB, WR, TE, K, D/ST.
        return FOOTBALL_POSITION_ALIASES.get(needle, position.strip().upper())
    return POSITION_ALIASES.get(needle, position.strip().title())


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def list_leagues() -> Dict[str, Any]:
    """List the configured fantasy leagues (name, sport, league id, Ryan's
    team id, ESPN season year). Covers hockey and football leagues. Pass a
    league's name (or part of it) as the 'league' argument of the other
    tools; they default to the first league."""
    return {"default_league": LEAGUES[0]["name"], "leagues": LEAGUES}


@mcp.tool()
def get_my_team(league: Optional[str] = None, refresh: bool = False) -> Dict[str, Any]:
    """Get Ryan's current fantasy roster with season stats and injury status
    for every player, plus the team's record (hockey also includes last-7-
    games form and last season's numbers). 'league' picks the league by
    (partial) name or id (see list_leagues); default is the first league."""
    lg = _resolve_league(league)
    data = _cached(
        _league_key("my_team", lg), lambda: _client(lg).get_my_team(), refresh=refresh
    )
    return {"league": lg["name"], **data}


@mcp.tool()
def get_free_agents(
    position: Optional[str] = None,
    limit: int = 25,
    league: Optional[str] = None,
    refresh: bool = False,
) -> Dict[str, Any]:
    """Top available free agents, sorted by fantasy points per game.

    position: hockey — Center, Left Wing, Right Wing, Defense, Goalie
    (abbreviations C, LW, RW, D, G also work); football — QB, RB, WR, TE,
    K, D/ST. limit: max players returned (1-100). league: league (partial)
    name or id, default first league. refresh: bypass the 10-minute cache
    and refetch from ESPN.
    """
    lg = _resolve_league(league)
    agents = _cached(
        _league_key("free_agents", lg),
        lambda: _client(lg).get_free_agents(),
        refresh=refresh,
    )
    pos = _normalize_position(position, lg["sport"])
    if pos:
        agents = [a for a in agents if a.get("position") == pos]
    agents = sorted(
        agents,
        key=lambda a: a.get("stats", {}).get("fantasy_points_per_game", 0),
        reverse=True,
    )
    limit = max(1, min(int(limit), 100))
    return {
        "league": lg["name"],
        "position_filter": pos,
        "total_matching": len(agents),
        "players": agents[:limit],
    }


@mcp.tool()
def get_pickup_recommendations(
    max_results: int = 10,
    include_ai_insights: bool = False,
    league: Optional[str] = None,
    refresh: bool = False,
) -> Dict[str, Any]:
    """Run the statistical pickup analysis live: ranks available free agents
    by value score (fantasy points per game, consistency, upside, position
    scarcity, historical bonus) against the current roster. Hockey leagues
    only — for football use get_free_agents, whose points are already scored
    with the league's own settings. 'league' picks the league by (partial)
    name or id, default first league.

    include_ai_insights=True also adds the pipeline's own OpenAI-generated
    blurbs (much slower); leave it False and draw your own conclusions from
    the returned metrics.
    """
    from statistical_analyzer import FantasyHockeyAnalyzer

    lg = _resolve_league(league)
    _require_hockey(lg, "get_pickup_recommendations")
    team = _cached(
        _league_key("my_team", lg), lambda: _client(lg).get_my_team(), refresh=refresh
    )
    agents = _cached(
        _league_key("free_agents", lg),
        lambda: _client(lg).get_free_agents(),
        refresh=refresh,
    )

    analyzer = FantasyHockeyAnalyzer()
    if not include_ai_insights:
        analyzer.openai_client = None

    # The analyzer mutates the agent dicts, so work on a copy of the cache.
    recommendations = analyzer.analyze_player_pickups(team, copy.deepcopy(agents))
    max_results = max(1, min(int(max_results), 20))
    return {
        "league": lg["name"],
        "team": team.get("team_name"),
        "recommendations": recommendations[:max_results],
    }


@mcp.tool()
def get_league_standings(league: Optional[str] = None) -> Dict[str, Any]:
    """Current league standings: rank, record and points for every team.
    'league' picks the league by (partial) name or id, default first league."""
    lg = _resolve_league(league)
    standings = _cached(
        _league_key("standings", lg), lambda: _client(lg).get_league_standings()
    )
    return {"league": lg["name"], "standings": standings}


@mcp.tool()
def get_current_matchups(league: Optional[str] = None) -> Dict[str, Any]:
    """This week's head-to-head matchups with live scores. 'league' picks
    the league by (partial) name or id, default first league."""
    lg = _resolve_league(league)
    matchups = _cached(
        _league_key("matchups", lg), lambda: _client(lg).get_matchup_data()
    )
    return {"league": lg["name"], **matchups}


@mcp.tool()
def find_player(name: str, league: Optional[str] = None) -> Dict[str, Any]:
    """Look up players in a league by name (partial, case-insensitive).
    Returns stats plus whether each match is rostered (and by which fantasy
    team) or a free agent. 'league' picks the league by (partial) name or
    id, default first league."""
    lg = _resolve_league(league)
    needle = name.strip().lower()
    matches: List[Dict[str, Any]] = []

    for team in _cached(
        _league_key("all_teams", lg), lambda: _client(lg).get_all_teams_data()
    ):
        for player in team.get("roster", []):
            if needle in player.get("name", "").lower():
                matches.append(
                    {
                        **player,
                        "status": "rostered",
                        "fantasy_team": team.get("team_name"),
                    }
                )

    for player in _cached(
        _league_key("free_agents", lg), lambda: _client(lg).get_free_agents()
    ):
        if needle in player.get("name", "").lower():
            matches.append({**player, "status": "free_agent"})

    return {"league": lg["name"], "query": name, "matches": matches[:10]}


@mcp.tool()
def get_scoring_config() -> Dict[str, Any]:
    """The HOCKEY fantasy scoring weights (points per goal, assist, etc.)
    and the thresholds/weights the recommendation engine uses. Computed
    hockey fantasy_points fields use this one scoring table for every
    hockey league, so for a hockey league with different scoring settings,
    prefer the raw stats. Football leagues don't use this table at all —
    their points come from ESPN scored with each league's own settings."""
    from analysis_config import (
        RECOMMENDATION_THRESHOLDS,
        SCORING_CATEGORIES,
        VALUE_SCORING,
    )

    return {
        "scoring_categories": SCORING_CATEGORIES,
        "value_scoring": VALUE_SCORING,
        "recommendation_thresholds": RECOMMENDATION_THRESHOLDS,
    }


# ---------------------------------------------------------------------------
# Auth + server
# ---------------------------------------------------------------------------


async def _plain_response(send, status: int, body: bytes):
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", b"application/json")],
        }
    )
    await send({"type": "http.response.body", "body": body})


class TokenAuthMiddleware:
    """Require MCP_AUTH_TOKEN (Bearer header or ?key= query param) on every
    HTTP request except /health. If the env var is unset, the server is open."""

    def __init__(self, app, token: Optional[str]):
        self.app = app
        self.token = token

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        if scope.get("path", "").rstrip("/") == "/health":
            await _plain_response(send, 200, b'{"status":"ok"}')
            return
        if self.token and not self._authorized(scope):
            await _plain_response(send, 401, b'{"error":"unauthorized"}')
            return
        await self.app(scope, receive, send)

    def _authorized(self, scope) -> bool:
        for key, value in scope.get("headers", []):
            if key == b"authorization":
                header = value.decode()
                if header.lower().startswith("bearer ") and secrets.compare_digest(
                    header[7:].strip(), self.token
                ):
                    return True
        query = parse_qs(scope.get("query_string", b"").decode())
        return any(
            secrets.compare_digest(candidate, self.token)
            for candidate in query.get("key", [])
        )


def main():
    token = os.getenv("MCP_AUTH_TOKEN")
    if not token:
        logger.warning(
            "MCP_AUTH_TOKEN is not set - the MCP endpoint is UNAUTHENTICATED"
        )

    import uvicorn

    app = TokenAuthMiddleware(mcp.streamable_http_app(), token)
    logger.info(f"Fantasy Hockey MCP server listening on port {PORT} at /mcp")
    uvicorn.run(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
