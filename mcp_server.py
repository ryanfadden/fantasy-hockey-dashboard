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
        "Live data and analysis for Ryan's ESPN Fantasy Hockey league. "
        "Stats come straight from ESPN at call time (cached ~10 minutes). "
        "Fantasy points use the league's scoring settings; call "
        "get_scoring_config to see them."
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


def _client():
    def make():
        from espn_client import ESPNFantasyClient

        return ESPNFantasyClient()

    return _cached("client", make)


POSITION_ALIASES = {
    "c": "Center",
    "lw": "Left Wing",
    "rw": "Right Wing",
    "d": "Defense",
    "g": "Goalie",
}


def _normalize_position(position: Optional[str]) -> Optional[str]:
    if not position:
        return None
    return POSITION_ALIASES.get(position.strip().lower(), position.strip().title())


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def get_my_team(refresh: bool = False) -> Dict[str, Any]:
    """Get Ryan's current fantasy roster with season stats, recent (last 7
    games) performance, last season's numbers, and injury status for every
    player, plus the team's record."""
    return _cached("my_team", lambda: _client().get_my_team(), refresh=refresh)


@mcp.tool()
def get_free_agents(
    position: Optional[str] = None, limit: int = 25, refresh: bool = False
) -> Dict[str, Any]:
    """Top available free agents, sorted by fantasy points per game.

    position: filter by Center, Left Wing, Right Wing, Defense or Goalie
    (abbreviations C, LW, RW, D, G also work). limit: max players returned
    (1-100). refresh: bypass the 10-minute cache and refetch from ESPN.
    """
    agents = _cached(
        "free_agents", lambda: _client().get_free_agents(), refresh=refresh
    )
    pos = _normalize_position(position)
    if pos:
        agents = [a for a in agents if a.get("position") == pos]
    agents = sorted(
        agents,
        key=lambda a: a.get("stats", {}).get("fantasy_points_per_game", 0),
        reverse=True,
    )
    limit = max(1, min(int(limit), 100))
    return {
        "position_filter": pos,
        "total_matching": len(agents),
        "players": agents[:limit],
    }


@mcp.tool()
def get_pickup_recommendations(
    max_results: int = 10, include_ai_insights: bool = False, refresh: bool = False
) -> Dict[str, Any]:
    """Run the statistical pickup analysis live: ranks available free agents
    by value score (fantasy points per game, consistency, upside, position
    scarcity, historical bonus) against the current roster.

    include_ai_insights=True also adds the pipeline's own OpenAI-generated
    blurbs (much slower); leave it False and draw your own conclusions from
    the returned metrics.
    """
    from statistical_analyzer import FantasyHockeyAnalyzer

    team = _cached("my_team", lambda: _client().get_my_team(), refresh=refresh)
    agents = _cached(
        "free_agents", lambda: _client().get_free_agents(), refresh=refresh
    )

    analyzer = FantasyHockeyAnalyzer()
    if not include_ai_insights:
        analyzer.openai_client = None

    # The analyzer mutates the agent dicts, so work on a copy of the cache.
    recommendations = analyzer.analyze_player_pickups(team, copy.deepcopy(agents))
    max_results = max(1, min(int(max_results), 20))
    return {
        "team": team.get("team_name"),
        "recommendations": recommendations[:max_results],
    }


@mcp.tool()
def get_league_standings() -> List[Dict[str, Any]]:
    """Current league standings: rank, record and points for every team."""
    return _cached("standings", lambda: _client().get_league_standings())


@mcp.tool()
def get_current_matchups() -> Dict[str, Any]:
    """This week's head-to-head matchups with live scores."""
    return _cached("matchups", lambda: _client().get_matchup_data())


@mcp.tool()
def find_player(name: str) -> Dict[str, Any]:
    """Look up players in the league by name (partial, case-insensitive).
    Returns stats plus whether each match is rostered (and by which fantasy
    team) or a free agent."""
    needle = name.strip().lower()
    matches: List[Dict[str, Any]] = []

    for team in _cached("all_teams", lambda: _client().get_all_teams_data()):
        for player in team.get("roster", []):
            if needle in player.get("name", "").lower():
                matches.append(
                    {
                        **player,
                        "status": "rostered",
                        "fantasy_team": team.get("team_name"),
                    }
                )

    for player in _cached("free_agents", lambda: _client().get_free_agents()):
        if needle in player.get("name", "").lower():
            matches.append({**player, "status": "free_agent"})

    return {"query": name, "matches": matches[:10]}


@mcp.tool()
def get_scoring_config() -> Dict[str, Any]:
    """The league's fantasy scoring weights (points per goal, assist, etc.)
    and the thresholds/weights the recommendation engine uses."""
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
