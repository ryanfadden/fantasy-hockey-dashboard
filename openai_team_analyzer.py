"""
OpenAI-powered team analysis for fantasy hockey recommendations
"""

import os
from typing import Dict, List, Any
from openai import OpenAI


class OpenAITeamAnalyzer:
    """Handles OpenAI-powered analysis of fantasy hockey team rosters"""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def analyze_team_roster(
        self,
        team_roster: List[Dict[str, Any]],
        comparison_data: Dict[str, Dict[str, float]],
        top_free_agents: List[Dict[str, Any]] = None,
    ) -> Dict[str, Dict[str, str]]:
        """Get lightweight swap analysis for all team players"""
        try:
            recommendations = {}

            for player in team_roster:
                player_name = player.get("name", "Unknown")
                position = player.get("position", "Unknown")

                # Calculate FP/G from stats if not present
                player_fp_per_game = player.get("fantasy_points_per_game", 0)
                if player_fp_per_game == 0:
                    player_fp_per_game = self._calculate_fantasy_points_per_game(
                        player.get("stats", {})
                    )

                # Find potential swap targets from recommendations
                swap_targets = self._find_swap_targets(player, top_free_agents)

                if swap_targets:
                    # Calculate swap score
                    swap_score = self._calculate_swap_score(player, swap_targets[0])
                    best_target = swap_targets[0]

                    # Calculate actual FP/G improvement (without bonuses)
                    actual_fp_improvement = (
                        best_target.get("fantasy_points_per_game", 0)
                        - player_fp_per_game
                    )

                    # Determine recommendation
                    if swap_score >= 15:
                        recommendation = "Must Swap"
                        rationale = f"Strong upgrade available: {best_target['name']} (+{actual_fp_improvement:.1f} FP/G improvement)"
                    elif swap_score >= 5:
                        recommendation = "Consider Swap"
                        rationale = f"Moderate upgrade: {best_target['name']} (+{actual_fp_improvement:.1f} FP/G improvement)"
                    else:
                        recommendation = "Keep"
                        rationale = self._generate_low_score_rationale(
                            player, best_target, swap_score
                        )
                else:
                    recommendation = "Keep"
                    rationale = self._generate_detailed_keep_rationale(
                        player, top_free_agents
                    )

                recommendations[player_name] = {
                    "recommendation": recommendation,
                    "rationale": rationale,
                }

            return recommendations

        except Exception as e:
            print(f"Error in lightweight swap analysis: {e}")
            import traceback

            traceback.print_exc()
            return {}

    def _build_comprehensive_player_context(
        self,
        player: Dict[str, Any],
        comparison_data: Dict[str, Dict[str, float]],
        top_free_agents: List[Dict[str, Any]] = None,
    ) -> str:
        """Build comprehensive context for swap analysis"""
        from dashboard import (
            calculate_fantasy_points_per_game,
            get_performance_comparison,
            get_historical_bonus,
        )

        stats = player.get("stats", {})
        current_fp_per_game = calculate_fantasy_points_per_game(stats)
        games_played = stats.get("games_played", 0)
        name = player.get("name", "Unknown")
        position = player.get("position", "Unknown")
        team = player.get("team", "Unknown")

        # Get comparisons
        league_performance = get_performance_comparison(player, comparison_data)
        last_year_stats = player.get("last_year_stats", {})
        last_year_fp_per_game = last_year_stats.get("fantasy_points_per_game", 0)
        historical_bonus = get_historical_bonus(name)

        # Convert league performance to percentile
        league_percentile = self._convert_performance_to_percentile(league_performance)

        # Get additional context
        age_context = self._get_age_context(name)
        team_context = self._get_team_context(team)
        schedule_context = self._get_schedule_context(team)
        injury_context = self._get_injury_context(player)
        contract_context = self._get_contract_context(name)
        recent_trend = self._get_recent_trend_context(player)

        # Find potential swap targets
        swap_targets = (
            self._find_potential_swap_targets(player, top_free_agents)
            if top_free_agents
            else "No free agent data available"
        )

        player_context = f"""
{name} ({position}) - SWAP ANALYSIS:
- Current Performance: {current_fp_per_game:.2f} FP/G ({games_played} games) - {league_percentile}
- Historical Context: {self._get_historical_status(historical_bonus)} ({last_year_fp_per_game:.2f} FP/G last year)
- Team Situation: {team} {team_context}
- Schedule Context: {schedule_context}
- Injury Status: {injury_context}
- Contract Status: {contract_context}
- Recent Trend: {recent_trend}
- Age Context: {age_context}
- Current Stats: {stats.get("goals", 0)}G {stats.get("assists", 0)}A, {stats.get("plus_minus", 0)}+/-, {stats.get("shots_on_goal", 0)} SOG, {stats.get("hits", 0)} hits, {stats.get("blocks", 0)} blocks
- Potential Swap Targets: {swap_targets}
"""
        return player_context

    def _build_player_context(
        self, player: Dict[str, Any], comparison_data: Dict[str, Dict[str, float]]
    ) -> str:
        """Build detailed context for a single player"""
        from dashboard import (
            calculate_fantasy_points_per_game,
            get_performance_comparison,
            get_historical_bonus,
        )

        stats = player.get("stats", {})
        current_fp_per_game = calculate_fantasy_points_per_game(stats)
        games_played = stats.get("games_played", 0)

        # Get comparisons
        league_performance = get_performance_comparison(player, comparison_data)
        last_year_stats = player.get("last_year_stats", {})
        last_year_fp_per_game = last_year_stats.get("fantasy_points_per_game", 0)
        historical_bonus = get_historical_bonus(player.get("name", ""))

        # Convert league performance to percentile
        league_percentile = self._convert_performance_to_percentile(league_performance)

        # Get additional context
        age_context = self._get_age_context(player.get("name", ""))
        team_context = self._get_team_context(player.get("team", ""))

        player_context = f"""
{player.get("name", "Unknown")} ({player.get("position", "Unknown")}):
- Current FP/G: {current_fp_per_game:.2f} ({games_played} games played)
- League Performance: {league_percentile}
- Last Year FP/G: {last_year_fp_per_game:.2f}
- Historical Status: {self._get_historical_status(historical_bonus)}
- Injury Status: {player.get("injury_status", "ACTIVE")}
- Team: {player.get("team", "Unknown")} {team_context}
- Age Context: {age_context}
- Current Stats: {stats.get("goals", 0)}G {stats.get("assists", 0)}A, {stats.get("plus_minus", 0)}+/-, {stats.get("shots_on_goal", 0)} SOG
- Situation Analysis: {self._get_situation_analysis(player, current_fp_per_game, games_played)}
"""
        return player_context

    def _convert_performance_to_percentile(self, league_performance: str) -> str:
        """Convert league performance to percentile description"""
        if league_performance == "Better":
            return "Top 25% of league (75th percentile+)"
        elif league_performance == "Average":
            return "Middle 50% of league (25th-75th percentile)"
        else:
            return "Bottom 25% of league (below 25th percentile)"

    def _get_historical_status(self, historical_bonus: float) -> str:
        """Get descriptive historical status"""
        if historical_bonus >= 0.3:
            return "Elite player (5+ All-Star appearances)"
        elif historical_bonus >= 0.2:
            return "Proven veteran (3+ All-Star appearances)"
        elif historical_bonus >= 0.1:
            return "Established player (1-2 All-Star appearances)"
        else:
            return "Rookie/Unproven player"

    def _get_age_context(self, player_name: str) -> str:
        """Get age context for known players"""
        # Known player ages (could be expanded)
        player_ages = {
            "Macklin Celebrini": "19 years old (2024 1st overall pick)",
            "Steven Stamkos": "34 years old (veteran)",
            "Erik Karlsson": "34 years old (veteran)",
            "Nazem Kadri": "33 years old (veteran)",
            "Matt Coronato": "21 years old (young prospect)",
            "Jackson LaCombe": "23 years old (young player)",
            "Matvei Michkov": "20 years old (top prospect)",
        }
        return player_ages.get(player_name, "Age unknown")

    def _get_team_context(self, team: str) -> str:
        """Get team context"""
        team_contexts = {
            "San Jose Sharks": "(rebuilding team)",
            "Nashville Predators": "(competitive team)",
            "Pittsburgh Penguins": "(aging core)",
            "Calgary Flames": "(competitive team)",
            "Philadelphia Flyers": "(rebuilding team)",
            "Anaheim Ducks": "(young team)",
        }
        return team_contexts.get(team, "")

    def _get_situation_analysis(
        self, player: Dict[str, Any], current_fp_per_game: float, games_played: int
    ) -> str:
        """Analyze the player's situation beyond just stats"""
        name = player.get("name", "")
        position = player.get("position", "")
        team = player.get("team", "")

        # No hardcoded factors - let AI analyze based on actual data

        # Generic situation analysis based on available data
        if games_played < 5:
            if current_fp_per_game < 1.5:
                return "Early season struggles, small sample size but concerning performance"
            elif current_fp_per_game < 2.5:
                return "Early season, small sample size, monitor for improvement"
            else:
                return "Early season, solid start, established role"
        else:
            if current_fp_per_game < 1.5:
                return "Concerning performance through multiple games, limited upside"
            elif current_fp_per_game < 2.5:
                return "Below-average performance, monitor for improvement or decline"
            else:
                return "Solid performance, established role and opportunity"

    def _get_league_context(
        self,
        team_roster: List[Dict[str, Any]],
        comparison_data: Dict[str, Dict[str, float]],
    ) -> str:
        """Get league-wide context for better decision making"""
        from dashboard import calculate_fantasy_points_per_game
        import json
        import glob
        import os

        # Calculate team average FP/G
        team_fp_values = []
        for player in team_roster:
            stats = player.get("stats", {})
            fp_per_game = calculate_fantasy_points_per_game(stats)
            team_fp_values.append(fp_per_game)

        team_avg = sum(team_fp_values) / len(team_fp_values) if team_fp_values else 0

        # Get free agent data for comparison
        free_agent_context = self._get_free_agent_context()

        return f"""
LEAGUE CONTEXT:
- Your team average FP/G: {team_avg:.2f}
- Roster spots: 17 total (2G, 4D, 6F starters + 5 bench)
{free_agent_context}
"""

    def _get_free_agent_context(self) -> str:
        """Get free agent performance data for comparison"""
        try:
            from dashboard import calculate_fantasy_points_per_game
            import json
            import glob
            import os

            # Find the latest free agents file
            free_agent_files = glob.glob("data/free_agents_*.json")
            if not free_agent_files:
                return "- Free agent data not available"

            # Get the most recent file
            latest_file = max(free_agent_files, key=os.path.getmtime)

            with open(latest_file, "r") as f:
                free_agents_data = json.load(f)

            if not free_agents_data:
                return "- Free agent data not available"

            # Calculate FP/G for all free agents
            free_agent_fp_values = []
            top_free_agents = []

            for agent in free_agents_data:
                stats = agent.get("stats", {})
                fp_per_game = calculate_fantasy_points_per_game(stats)
                games_played = stats.get("games_played", 0)

                if games_played >= 3:  # Only include players with decent sample size
                    free_agent_fp_values.append(fp_per_game)

                    # Track top performers for examples
                    if fp_per_game >= 3.0:
                        top_free_agents.append(
                            {
                                "name": agent.get("name", "Unknown"),
                                "position": agent.get("position", "Unknown"),
                                "fp_per_game": fp_per_game,
                                "games": games_played,
                            }
                        )

            if not free_agent_fp_values:
                return "- No free agents with sufficient sample size"

            # Sort top free agents by FP/G
            top_free_agents.sort(key=lambda x: x["fp_per_game"], reverse=True)

            # Calculate averages
            avg_free_agent_fp = sum(free_agent_fp_values) / len(free_agent_fp_values)
            max_free_agent_fp = max(free_agent_fp_values)

            # Build context string
            context_parts = [
                f"- Free agent average FP/G: {avg_free_agent_fp:.2f}",
                f"- Best available free agent: {max_free_agent_fp:.2f} FP/G",
                f"- Total free agents analyzed: {len(free_agent_fp_values)}",
            ]

            # Add top 3 free agents as examples
            if top_free_agents:
                context_parts.append("- Top available free agents:")
                for i, agent in enumerate(top_free_agents[:3], 1):
                    context_parts.append(
                        f"  {i}. {agent['name']} ({agent['position']}): {agent['fp_per_game']:.2f} FP/G ({agent['games']} games)"
                    )

            return "\n".join(context_parts)

        except Exception as e:
            print(f"Error getting free agent context: {e}")
            return "- Free agent data unavailable"

    def _get_analysis_instructions(self) -> str:
        return """
You are analyzing a fantasy hockey roster where roster spots are LIMITED. Be DECISIVE and STRATEGIC.

RECOMMENDATION CRITERIA (focus on context, not just stats):
- Must Keep: Elite track record + current opportunity OR proven veterans with clear path to improvement
- Hold: Solid situation + reasonable upside OR veterans with track record worth patience
- Watch: Unclear situation OR rookies/prospects with potential but small sample
- Drop: Poor situation + no clear improvement path OR veterans clearly declining

STRICT GUIDELINES:
- Only 2-3 "Must Keep" players maximum per roster
- Focus on SITUATION and OPPORTUNITY, not just current stats
- Consider roster construction: You can only start 2 goalies, 4 defensemen, 6 forwards
- Early season (3-5 games) - prioritize potential and situation over current stats
- Veterans with elite history deserve patience unless situation is clearly bad
- BE DECISIVE: If a player is underperforming AND has poor situation, recommend "Drop"
- Don't be afraid to recommend "Drop" for veterans who are clearly declining

DECISION FACTORS (in order of importance):
1. Team situation and opportunity (rebuilding vs competitive, role changes, line changes)
2. Player development stage and trajectory (rookie improving vs veteran declining)
3. Sample size reliability (5+ games vs 3-4 games) 
4. Historical track record and age context
5. Position scarcity and roster needs
6. Current FP/G as supporting evidence, not primary factor

DROP CANDIDATES (be decisive):
- Veterans with <2.0 FP/G AND poor situation (aging, reduced role, team struggles)
- Players with <1.5 FP/G through 5+ games AND no clear improvement path
- Roster cloggers who are blocking better free agents
- Players significantly underperforming vs available free agents

SITUATIONAL ANALYSIS EXAMPLES (use as guidance, not hardcoded):
- "Rookie on rebuilding team, potential for increased ice time as season progresses"
- "Veteran on new team, may need adjustment period to new system"
- "Aging player, monitor for potential role changes or decline"
- "Elite player with slow start, likely temporary based on track record"
- "Young player on competitive team, fighting for ice time"
- "Top prospect, high upside but raw and needs development"

For each player, provide: "Player Name: Recommendation - few sentence rationale"
Use exactly these recommendations: Drop, Watch, Hold, Must Keep
Be decisive - avoid generic language like "strong performance" or "good pickup".
"""

    def _parse_response(self, response_text: str) -> Dict[str, Dict[str, str]]:
        """Parse OpenAI response into structured recommendations"""
        recommendations = {}

        for line in response_text.split("\n"):
            if ":" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    player_name = parts[0].strip()
                    recommendation_part = parts[1].strip()

                    # Extract recommendation and rationale
                    if " - " in recommendation_part:
                        rec_parts = recommendation_part.split(" - ", 1)
                        recommendation = rec_parts[0].strip()
                        rationale = rec_parts[1].strip()
                    else:
                        recommendation = recommendation_part
                        rationale = "Analysis provided"

                    if recommendation in ["Drop", "Watch", "Hold", "Must Keep"]:
                        recommendations[player_name] = {
                            "recommendation": recommendation,
                            "rationale": rationale,
                        }

        return recommendations

    def _get_schedule_context(self, team: str) -> str:
        """Get schedule context for team"""
        # This could be enhanced with actual schedule data
        schedule_contexts = {
            "San Jose Sharks": "Heavy road schedule coming up, tough matchups",
            "Nashville Predators": "Favorable home stretch, good matchups",
            "Pittsburgh Penguins": "Back-to-back games this week, rest advantage",
            "Calgary Flames": "Light schedule this week, practice time",
            "Philadelphia Flyers": "Heavy schedule, multiple games in short period",
            "Anaheim Ducks": "Road trip coming up, travel fatigue factor",
        }
        return schedule_contexts.get(team, "Standard schedule")

    def _get_injury_context(self, player: Dict[str, Any]) -> str:
        """Get detailed injury context"""
        injury_status = player.get("injury_status", "ACTIVE").lower()
        if "out" in injury_status:
            return "OUT - Long-term injury, significant timeline"
        elif "doubtful" in injury_status:
            return "DOUBTFUL - Likely to miss multiple games"
        elif "questionable" in injury_status:
            return "QUESTIONABLE - Game-time decision"
        elif "probable" in injury_status:
            return "PROBABLE - Minor issue, should play"
        else:
            return "HEALTHY - No injury concerns"

    def _get_contract_context(self, player_name: str) -> str:
        """Get contract context for known players"""
        contract_contexts = {
            "Macklin Celebrini": "Entry-level contract, rookie",
            "Steven Stamkos": "UFA after this season, contract year motivation",
            "Erik Karlsson": "Long-term contract, team cornerstone",
            "Nazem Kadri": "Multi-year contract, stable situation",
            "Matt Coronato": "Entry-level contract, developing player",
            "Jackson LaCombe": "Entry-level contract, young defenseman",
            "Matvei Michkov": "Entry-level contract, top prospect",
        }
        return contract_contexts.get(player_name, "Contract status unknown")

    def _get_recent_trend_context(self, player: Dict[str, Any]) -> str:
        """Analyze recent performance trend"""
        recent_performance = player.get("recent_performance", {})
        if not recent_performance:
            return "No recent trend data available"

        # This would need to be enhanced with actual recent game data
        return "Recent performance data not available in current format"

    def _find_potential_swap_targets(
        self, player: Dict[str, Any], top_free_agents: List[Dict[str, Any]]
    ) -> str:
        """Find potential swap targets from free agents"""
        if not top_free_agents:
            return "No free agent data available"

        player_position = player.get("position", "Unknown")
        player_fp_per_game = player.get("fantasy_points_per_game", 0)

        # Find same position players with better FP/G
        potential_targets = []
        for agent in top_free_agents[:10]:  # Top 10 free agents
            if agent.get("position") == player_position:
                agent_fp_per_game = agent.get("fantasy_points_per_game", 0)
                if agent_fp_per_game > player_fp_per_game:
                    potential_targets.append(
                        f"{agent.get('name', 'Unknown')} ({agent_fp_per_game:.2f} FP/G)"
                    )

        if potential_targets:
            return f"Consider: {', '.join(potential_targets[:3])}"  # Top 3 targets
        else:
            return "No clear upgrade targets at this position"

    def _get_swap_analysis_instructions(self) -> str:
        return """
You are analyzing potential roster swaps in a fantasy hockey league. For each player, determine if they should be swapped with a better free agent.

SWAP ANALYSIS CRITERIA:
- Keep: Player is performing well or has strong upside potential
- Consider Swap: Player is underperforming and better options are available
- Must Swap: Player is clearly underperforming with multiple better alternatives

ANALYSIS FACTORS (in order of importance):
1. Current performance vs league average and free agent alternatives
2. Historical track record and proven ability
3. Team situation and opportunity (line changes, role changes, team performance)
4. Schedule context (upcoming matchups, rest advantages)
5. Injury status and health concerns
6. Contract situation and motivation factors
7. Age and development trajectory
8. Position scarcity and roster construction needs

SWAP RECOMMENDATIONS:
- Keep: "Keep - [reasoning]"
- Consider Swap: "Consider Swap - [specific player to target] - [reasoning]"
- Must Swap: "Must Swap - [specific player to target] - [reasoning]"

For each player, provide: "Player Name: Recommendation - detailed reasoning"
Be specific about which free agent to target and why the swap makes sense.
Focus on actionable advice with concrete alternatives.
"""

    def _parse_swap_response(self, response_text: str) -> Dict[str, Dict[str, str]]:
        """Parse OpenAI swap analysis response"""
        recommendations = {}

        for line in response_text.split("\n"):
            if ":" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    player_name = parts[0].strip()
                    recommendation_part = parts[1].strip()

                    # Extract recommendation and rationale
                    if " - " in recommendation_part:
                        rec_parts = recommendation_part.split(" - ", 1)
                        recommendation = rec_parts[0].strip()
                        rationale = rec_parts[1].strip()
                    else:
                        recommendation = recommendation_part
                        rationale = "Analysis provided"

                    if recommendation in ["Keep", "Consider Swap", "Must Swap"]:
                        recommendations[player_name] = {
                            "recommendation": recommendation,
                            "rationale": rationale,
                        }

        return recommendations

    def _find_swap_targets(
        self, player: Dict[str, Any], top_free_agents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find potential swap targets matching position"""
        if not top_free_agents:
            return []

        player_position = player.get("position", "Unknown")
        # Calculate FP/G from stats if not present
        player_fp_per_game = player.get("fantasy_points_per_game", 0)
        if player_fp_per_game == 0:
            player_fp_per_game = self._calculate_fantasy_points_per_game(
                player.get("stats", {})
            )

        # Position matching rules
        position_matches = {
            "Goalie": ["Goalie"],
            "Defense": ["Defense"],
            "Center": ["Center"],
            "Left Wing": ["Left Wing"],
            "Right Wing": ["Right Wing"],
        }

        matching_positions = position_matches.get(player_position, [])

        # Find same position players with better FP/G
        potential_targets = []
        for agent in top_free_agents:
            if agent.get("position") in matching_positions:
                agent_fp_per_game = agent.get("fantasy_points_per_game", 0)
                if agent_fp_per_game > player_fp_per_game:
                    potential_targets.append(agent)

        # Sort by FP/G improvement (highest first)
        potential_targets.sort(
            key=lambda x: x.get("fantasy_points_per_game", 0) - player_fp_per_game,
            reverse=True,
        )

        return potential_targets[:3]  # Top 3 targets

    def _calculate_swap_score(
        self, current_player: Dict[str, Any], target_player: Dict[str, Any]
    ) -> float:
        """Calculate swap score based on FP/G improvement and other factors"""
        current_fp_per_game = current_player.get("fantasy_points_per_game", 0)
        if current_fp_per_game == 0:
            current_fp_per_game = self._calculate_fantasy_points_per_game(
                current_player.get("stats", {})
            )

        target_fp_per_game = target_player.get("fantasy_points_per_game", 0)

        # Base score is FP/G improvement
        fp_improvement = target_fp_per_game - current_fp_per_game

        # Add small bonuses for other factors
        bonus = 0

        # Sample size bonus (more games = more reliable)
        target_games = target_player.get("stats", {}).get("games_played", 0)
        if target_games >= 5:
            bonus += 2
        elif target_games >= 3:
            bonus += 1

        # Historical track record bonus
        from dashboard import get_historical_bonus

        target_historical = get_historical_bonus(target_player.get("name", ""))
        if target_historical > 0.3:
            bonus += 3
        elif target_historical > 0.2:
            bonus += 2
        elif target_historical > 0.1:
            bonus += 1

        # Injury status bonus
        target_injury = target_player.get("injury_status", "ACTIVE").lower()
        if "out" in target_injury:
            bonus -= 5
        elif "doubtful" in target_injury:
            bonus -= 2
        elif "questionable" in target_injury:
            bonus -= 1

        return fp_improvement + bonus

    def _calculate_fantasy_points_per_game(self, stats: Dict[str, Any]) -> float:
        """Calculate fantasy points per game using league scoring"""
        from config import SCORING_CATEGORIES

        total_points = 0.0
        for category, points_per_unit in SCORING_CATEGORIES.items():
            value = stats.get(category, 0)
            total_points += value * points_per_unit

        games_played = max(stats.get("games_played", 1), 1)
        return total_points / games_played

    def _generate_detailed_keep_rationale(
        self, player: Dict[str, Any], top_free_agents: List[Dict[str, Any]]
    ) -> str:
        """Generate detailed rationale for why to keep a player when no swap targets exist"""
        player_name = player.get("name", "Unknown")
        player_position = player.get("position", "Unknown")
        player_fp_per_game = player.get("fantasy_points_per_game", 0)
        if player_fp_per_game == 0:
            player_fp_per_game = self._calculate_fantasy_points_per_game(
                player.get("stats", {})
            )

        # Analyze available options at this position
        position_analysis = self._analyze_position_depth(
            player_position, top_free_agents
        )

        # Get player's performance context
        performance_context = self._get_performance_context(player)

        # Build comprehensive rationale
        rationale_parts = []

        # Position scarcity analysis
        if position_analysis["total_available"] == 0:
            rationale_parts.append(f"No {player_position}s available in free agency")
        elif position_analysis["total_available"] <= 3:
            rationale_parts.append(
                f"Very limited {player_position} options available ({position_analysis['total_available']} total)"
            )
        else:
            rationale_parts.append(
                f"Analyzed {position_analysis['total_available']} available {player_position}s"
            )

        # Performance comparison
        if position_analysis["better_players"] == 0:
            rationale_parts.append("No players with better FP/G found")
        else:
            rationale_parts.append(
                f"Found {position_analysis['better_players']} players with higher FP/G"
            )

        # Specific analysis of why no swap
        if position_analysis["best_available"]:
            best_available = position_analysis["best_available"]
            fp_diff = (
                best_available.get("fantasy_points_per_game", 0) - player_fp_per_game
            )

            if fp_diff <= 0:
                rationale_parts.append(
                    f"Best available ({best_available['name']}) has {best_available.get('fantasy_points_per_game', 0):.1f} FP/G vs your {player_fp_per_game:.1f}"
                )
            else:
                rationale_parts.append(
                    f"Best available ({best_available['name']}) only +{fp_diff:.1f} FP/G improvement"
                )

        # Add performance context
        if performance_context:
            rationale_parts.append(performance_context)

        # Add historical context if applicable
        from dashboard import get_historical_bonus

        historical_bonus = get_historical_bonus(player_name)
        if historical_bonus > 0.1:
            rationale_parts.append(
                f"Strong historical track record ({historical_bonus:.1f} bonus)"
            )

        # Add injury context
        injury_status = player.get("injury_status", "ACTIVE")
        if injury_status != "ACTIVE":
            rationale_parts.append(f"Currently {injury_status.lower()}")

        return " | ".join(rationale_parts)

    def _analyze_position_depth(
        self, position: str, top_free_agents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze available players at a specific position"""
        if not top_free_agents:
            return {"total_available": 0, "better_players": 0, "best_available": None}

        # Position matching rules
        position_matches = {
            "Goalie": ["Goalie"],
            "Defense": ["Defense"],
            "Center": ["Center"],
            "Left Wing": ["Left Wing"],
            "Right Wing": ["Right Wing"],
        }

        matching_positions = position_matches.get(position, [])
        position_players = [
            p for p in top_free_agents if p.get("position") in matching_positions
        ]

        # Sort by FP/G
        position_players.sort(
            key=lambda x: x.get("fantasy_points_per_game", 0), reverse=True
        )

        return {
            "total_available": len(position_players),
            "better_players": len(
                [p for p in position_players if p.get("fantasy_points_per_game", 0) > 0]
            ),
            "best_available": position_players[0] if position_players else None,
        }

    def _get_performance_context(self, player: Dict[str, Any]) -> str:
        """Get performance context for a player"""
        fp_per_game = player.get("fantasy_points_per_game", 0)
        games_played = player.get("stats", {}).get("games_played", 0)

        context_parts = []

        # Sample size context
        if games_played >= 10:
            context_parts.append("Strong sample size")
        elif games_played >= 5:
            context_parts.append("Decent sample size")
        elif games_played >= 3:
            context_parts.append("Limited sample size")
        else:
            context_parts.append("Very small sample")

        # Performance level context
        if fp_per_game >= 5.0:
            context_parts.append("Elite performance")
        elif fp_per_game >= 3.0:
            context_parts.append("Strong performance")
        elif fp_per_game >= 2.0:
            context_parts.append("Solid performance")
        elif fp_per_game >= 1.0:
            context_parts.append("Average performance")
        else:
            context_parts.append("Below average performance")

        return " • ".join(context_parts)

    def _generate_low_score_rationale(
        self, player: Dict[str, Any], target: Dict[str, Any], swap_score: float
    ) -> str:
        """Generate detailed rationale for low swap scores"""
        player_name = player.get("name", "Unknown")
        player_fp_per_game = player.get("fantasy_points_per_game", 0)
        if player_fp_per_game == 0:
            player_fp_per_game = self._calculate_fantasy_points_per_game(
                player.get("stats", {})
            )

        target_name = target.get("name", "Unknown")
        target_fp_per_game = target.get("fantasy_points_per_game", 0)

        rationale_parts = []

        # FP/G comparison
        fp_improvement = target_fp_per_game - player_fp_per_game
        if fp_improvement <= 0:
            rationale_parts.append(
                f"Best option ({target_name}) has {target_fp_per_game:.1f} FP/G vs your {player_fp_per_game:.1f}"
            )
        else:
            rationale_parts.append(
                f"Best option ({target_name}) only +{fp_improvement:.1f} FP/G improvement"
            )

        # Sample size analysis
        player_games = player.get("stats", {}).get("games_played", 0)
        target_games = target.get("stats", {}).get("games_played", 0)

        if player_games >= 5 and target_games < 3:
            rationale_parts.append("Your player has more reliable sample size")
        elif target_games >= 5 and player_games < 3:
            rationale_parts.append("Target has more reliable sample size")

        # Historical track record comparison
        from dashboard import get_historical_bonus

        player_historical = get_historical_bonus(player_name)
        target_historical = get_historical_bonus(target_name)

        if player_historical > target_historical + 0.1:
            rationale_parts.append("Your player has stronger historical track record")
        elif target_historical > player_historical + 0.1:
            rationale_parts.append("Target has stronger historical track record")

        # Injury status comparison
        player_injury = player.get("injury_status", "ACTIVE")
        target_injury = target.get("injury_status", "ACTIVE")

        if player_injury == "ACTIVE" and target_injury != "ACTIVE":
            rationale_parts.append("Your player is healthy, target is not")
        elif target_injury == "ACTIVE" and player_injury != "ACTIVE":
            rationale_parts.append("Target is healthy, your player is not")

        # Overall assessment
        if swap_score < 0:
            rationale_parts.append("Swap would be a downgrade")
        elif swap_score < 2:
            rationale_parts.append("Minimal improvement, not worth the risk")
        else:
            rationale_parts.append("Small improvement, consider holding")

        return " | ".join(rationale_parts)


def get_openai_recommendation(
    team_roster: List[Dict[str, Any]],
    comparison_data: Dict[str, Dict[str, float]],
    top_free_agents: List[Dict[str, Any]] = None,
) -> Dict[str, Dict[str, str]]:
    """Convenience function for backward compatibility"""
    analyzer = OpenAITeamAnalyzer()
    return analyzer.analyze_team_roster(team_roster, comparison_data, top_free_agents)
