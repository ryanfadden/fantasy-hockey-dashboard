"""
Fantasy Hockey Dashboard
Web interface for viewing analysis results and recommendations
"""

import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import os
import glob
from datetime import datetime
from typing import List, Dict, Any
from utils import get_latest_data_file, format_timestamp
from config import DASHBOARD_CONFIG

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Fantasy Hockey Analysis Dashboard"

# Define the layout
app.layout = html.Div(
    [
        html.Div(
            [
                html.H1(
                    "🏒 Fantasy Hockey Analysis Dashboard",
                    style={
                        "textAlign": "center",
                        "color": "#2E86AB",
                        "marginBottom": "30px",
                    },
                ),
                # Status indicator
                html.Div(
                    id="status-indicator",
                    style={"textAlign": "center", "marginBottom": "20px"},
                ),
                # Refresh button
                html.Div(
                    [
                        html.Button(
                            "🔄 Refresh Data",
                            id="refresh-button",
                            n_clicks=0,
                            style={
                                "backgroundColor": "#2E86AB",
                                "color": "white",
                                "border": "none",
                                "padding": "10px 20px",
                                "borderRadius": "5px",
                                "cursor": "pointer",
                            },
                        )
                    ],
                    style={"textAlign": "center", "marginBottom": "30px"},
                ),
            ]
        ),
        # Main content tabs
        dcc.Tabs(
            id="main-tabs",
            value="recommendations",
            children=[
                dcc.Tab(label="📊 Recommendations", value="recommendations"),
                dcc.Tab(label="👥 My Team", value="my-team"),
                dcc.Tab(label="🔄 Swap Analysis", value="swap-analysis"),
                dcc.Tab(label="📈 Analytics", value="analytics"),
            ],
        ),
        html.Div(id="tab-content", style={"marginTop": "20px"}),
        # Hidden div to store data
        html.Div(id="data-store", style={"display": "none"}),
        # Auto-refresh interval
        dcc.Interval(
            id="interval-component",
            interval=5 * 60 * 1000,  # Update every 5 minutes
            n_intervals=0,
        ),
    ]
)


def calculate_fantasy_points_per_game(stats: Dict[str, Any]) -> float:
    """Calculate fantasy points per game using league scoring"""
    from config import SCORING_CATEGORIES

    total_points = 0.0
    for category, points_per_unit in SCORING_CATEGORIES.items():
        value = stats.get(category, 0)
        total_points += value * points_per_unit

    games_played = max(stats.get("games_played", 1), 1)
    return total_points / games_played


def get_player_comparison_data() -> Dict[str, Dict[str, float]]:
    """Get comparison data for all OTHER rostered players by position (excluding my team)"""
    try:
        # Load all team data to get rostered players
        team_files = glob.glob("data/all_teams_data_*.json")
        if not team_files:
            return {}

        latest_all_teams_file = max(team_files, key=os.path.getctime)

        with open(latest_all_teams_file, "r") as f:
            all_teams_data = json.load(f)

        # Get my team ID from the latest team data
        my_team_file = get_latest_data_file("data", "team_data_")
        my_team_id = None
        if my_team_file:
            with open(my_team_file, "r") as f:
                my_team_data = json.load(f)
                my_team_id = my_team_data.get("team_id")

        # Get all rostered players from OTHER teams only
        other_rostered_players = []

        for team_data in all_teams_data:
            # Skip my own team
            if team_data.get("team_id") == my_team_id:
                continue

            if "roster" in team_data:
                other_rostered_players.extend(team_data["roster"])

        # Group by position and calculate averages
        position_stats = {}
        for player in other_rostered_players:
            position = player.get("position", "Unknown")
            stats = player.get("stats", {})
            fp_per_game = calculate_fantasy_points_per_game(stats)

            if position not in position_stats:
                position_stats[position] = []
            position_stats[position].append(fp_per_game)

        # Calculate averages and percentiles for each position
        comparison_data = {}
        for position, fp_values in position_stats.items():
            if fp_values:
                fp_values.sort()
                avg_fp = sum(fp_values) / len(fp_values)
                median_fp = fp_values[len(fp_values) // 2]
                p75_fp = fp_values[int(len(fp_values) * 0.75)]
                p25_fp = fp_values[int(len(fp_values) * 0.25)]

                comparison_data[position] = {
                    "average": avg_fp,
                    "median": median_fp,
                    "p75": p75_fp,
                    "p25": p25_fp,
                    "count": len(fp_values),
                }

        return comparison_data

    except Exception as e:
        print(f"Error getting comparison data: {e}")
        return {}


def get_performance_comparison(
    player: Dict[str, Any], comparison_data: Dict[str, Dict[str, float]]
) -> str:
    """Compare player performance to league average"""
    try:
        position = player.get("position", "Unknown")
        stats = player.get("stats", {})
        player_fp = calculate_fantasy_points_per_game(stats)

        if position not in comparison_data:
            return "Unknown"

        pos_data = comparison_data[position]

        # Compare to percentiles
        if player_fp >= pos_data["p75"]:
            return "Better"
        elif player_fp >= pos_data["p25"]:
            return "Average"
        else:
            return "Worse"

    except Exception as e:
        print(f"Error comparing performance: {e}")
        return "Unknown"


def load_latest_data() -> Dict[str, Any]:
    """Load the latest analysis data"""
    try:
        summary_data = {}  # Initialize empty dict

        # Try to load latest summary
        summary_file = get_latest_data_file("output", "summary_")
        if summary_file:
            with open(summary_file, "r") as f:
                summary_data = json.load(f)

        # Also load team data
        team_file = get_latest_data_file("data", "team_data_")
        if team_file:
            with open(team_file, "r") as f:
                team_data = json.load(f)
                summary_data["team_roster"] = team_data.get("roster", [])

        # Load full recommendations with AI insights
        rec_file = get_latest_data_file("output", "recommendations_")
        if rec_file:
            with open(rec_file, "r") as f:
                recommendations = json.load(f)
                summary_data["full_recommendations"] = recommendations

        return summary_data

    except Exception as e:
        print(f"Error loading data: {e}")
        # Fallback to latest recommendations
        try:
            rec_file = get_latest_data_file("output", "recommendations_")
            if rec_file:
                with open(rec_file, "r") as f:
                    recommendations = json.load(f)
                    return {
                        "recommendations": recommendations,
                        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                    }
        except Exception as e2:
            print(f"Error loading fallback data: {e2}")

        return {}


@app.callback(
    [Output("data-store", "children"), Output("status-indicator", "children")],
    [Input("refresh-button", "n_clicks"), Input("interval-component", "n_intervals")],
)
def update_data(n_clicks, n_intervals):
    """Update data when refresh button is clicked or interval triggers"""
    data = load_latest_data()

    if data:
        status = html.Div(
            [
                html.Span("🟢 Data Updated: ", style={"color": "green"}),
                html.Span(format_timestamp(data.get("timestamp", "Unknown"))),
            ]
        )
    else:
        status = html.Div(
            [
                html.Span("🔴 No Data Available", style={"color": "red"}),
                html.Br(),
                html.Span(
                    "Run the analysis pipeline first",
                    style={"fontSize": "12px", "color": "gray"},
                ),
            ]
        )

    return json.dumps(data), status


@app.callback(
    Output("tab-content", "children"),
    [Input("main-tabs", "value"), Input("data-store", "children")],
)
def render_tab_content(active_tab, data_json):
    """Render content based on selected tab"""
    print(f"DEBUG: Tab content callback - active_tab: '{active_tab}'")

    try:
        data = json.loads(data_json) if data_json else {}
    except:
        data = {}

    if active_tab == "recommendations":
        print("DEBUG: Rendering recommendations tab")
        return render_recommendations_tab(data)
    elif active_tab == "my-team":
        print("DEBUG: Rendering my-team tab")
        return render_my_team_tab(data)
    elif active_tab == "swap-analysis":
        print("DEBUG: Rendering swap-analysis tab")
        return render_swap_analysis_tab(data)
    elif active_tab == "analytics":
        print("DEBUG: Rendering analytics tab")
        return render_analytics_tab(data)
    else:
        print(f"DEBUG: Unknown tab: '{active_tab}'")
        return html.Div("Select a tab to view content")


@app.callback(
    [
        Output("swap-analysis-Matt-Coronato", "children", allow_duplicate=True),
        Output("swap-analysis-Matvei-Michkov", "children", allow_duplicate=True),
    ],
    [Input("data-store", "children")],
    prevent_initial_call="initial_duplicate",  # Allow callback to run on initial load with duplicates
)
def update_swap_analysis(data_json):
    """Update swap analysis with OpenAI insights"""
    print("DEBUG: Swap analysis callback triggered")

    try:
        data = json.loads(data_json) if data_json else {}
        roster = data.get("team_roster", [])

        # Find swap candidates and extract their targets
        analyses = {}

        for player in roster:
            player_name = player.get("name", "")

            # Check both possible field names for recommendations
            recommendation = ""
            rationale = ""
            if "openai_rec" in player:
                recommendation = player["openai_rec"].get("recommendation", "")
                rationale = player["openai_rec"].get("rationale", "")
            else:
                recommendation = player.get("recommendation", "")
                rationale = player.get("rationale", "")

            if "Consider Swap" in recommendation and "Moderate upgrade:" in rationale:
                # Extract target player from rationale
                import re

                match = re.search(
                    r"Moderate upgrade: ([^(]+) \(\+(\d+\.?\d*) FP/G improvement\)",
                    rationale,
                )
                if match:
                    target_player = match.group(1).strip()
                    print(f"DEBUG: Found swap {player_name} → {target_player}")

                    # Get detailed analysis for this swap
                    print(
                        f"DEBUG: Calling get_detailed_swap_analysis for {player_name} → {target_player}"
                    )
                    analysis = get_detailed_swap_analysis(player, target_player)
                    print(f"DEBUG: Analysis result: {analysis[:100]}...")

                    analyses[player_name] = analysis

        # Return analyses for the specific hardcoded outputs (for now)
        coronato_analysis = analyses.get("Matt Coronato", "No analysis available")
        michkov_analysis = analyses.get("Matvei Michkov", "No analysis available")

        print(
            f"DEBUG: Returning analyses - Coronato: {len(coronato_analysis)}, Michkov: {len(michkov_analysis)}"
        )
        return coronato_analysis, michkov_analysis

    except Exception as e:
        error_msg = f"Error generating analysis: {str(e)}"
        print(f"DEBUG: Swap analysis error: {error_msg}")
        return error_msg, error_msg


def get_detailed_swap_analysis(
    current_player: Dict[str, Any], target_player: str
) -> str:
    """Get detailed OpenAI analysis for a potential swap"""
    try:
        print(
            f"DEBUG: Starting analysis for {current_player.get('name')} → {target_player}"
        )
        from openai import OpenAI
        import os

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "Analysis unavailable: No OpenAI API key found"

        print(f"DEBUG: API key found, creating client")
        client = OpenAI(api_key=api_key)

        # Build context about the league scoring
        scoring_context = """
        LEAGUE SCORING SYSTEM:

        Skater Scoring:
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
        - Overtime Losses (OTL): 1 point
        """

        # Build player context
        player_context = f"""
        CURRENT PLAYER: {current_player.get("name", "Unknown")}
        - Position: {current_player.get("position", "Unknown")}
        - Team: {current_player.get("team", "Unknown")}
        - Current FP/G: {current_player.get("fantasy_points_per_game", 0):.2f}
        - Games Played: {current_player.get("stats", {}).get("games_played", 0)}
        - Goals: {current_player.get("stats", {}).get("goals", 0)}
        - Assists: {current_player.get("stats", {}).get("assists", 0)}
        - Power Play Points: {current_player.get("stats", {}).get("powerplay_points", 0)}
        - Short Handed Points: {current_player.get("stats", {}).get("shorthanded_points", 0)}
        - Shots on Goal: {current_player.get("stats", {}).get("shots_on_goal", 0)}
        - Hits: {current_player.get("stats", {}).get("hits", 0)}
        - Blocked Shots: {current_player.get("stats", {}).get("blocks", 0)}
        
        POTENTIAL TARGET: {target_player}
        """

        prompt = f"""Perform a comprehensive fantasy hockey analysis comparing {current_player.get("name", "Unknown")} and {target_player}.

{scoring_context}

I am considering dropping **{current_player.get("name", "Unknown")}** for **{target_player}**.

{player_context}

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

Be specific about fantasy point calculations using our exact scoring system."""

        print(f"DEBUG: Making API call with prompt length: {len(prompt)}")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a fantasy hockey expert. Provide comprehensive analysis comparing players using the provided scoring system. Give specific fantasy point calculations and clear recommendations.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
        )

        print(
            f"DEBUG: API call successful, response length: {len(response.choices[0].message.content)}"
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"Analysis unavailable: {str(e)}"


def get_ranking_explanation(
    player: Dict[str, Any], rank: int, all_recommendations: list
) -> str:
    """Generate explanation showing top 3 contributing factors to value score"""
    name = player.get("name", "")
    position = player.get("position", "")
    fp_per_game = player.get("fantasy_points_per_game", 0)
    analysis = player.get("analysis", {})

    # Calculate individual score contributions
    weights = {
        "fantasy_points_per_game": 0.5,
        "consistency_rating": 0.25,
        "upside_potential": 0.2,
        "position_scarcity": 0.05,
    }

    contributions = []

    # FP/G contribution
    fp_contrib = fp_per_game * weights["fantasy_points_per_game"]
    contributions.append(("FP/G", fp_contrib, f"{fp_per_game:.1f} FP/G"))

    # Consistency contribution
    consistency = analysis.get("consistency_rating", 0)
    consistency_contrib = consistency * weights["consistency_rating"]
    contributions.append(
        ("Consistency", consistency_contrib, f"{consistency:.1f}/10 consistency")
    )

    # Upside contribution
    upside = analysis.get("upside_potential", 0)
    upside_contrib = upside * weights["upside_potential"]
    contributions.append(("Upside", upside_contrib, f"{upside:.1f}/10 upside"))

    # Position scarcity contribution
    position_scarcity = analysis.get("position_scarcity", 0)
    position_contrib = position_scarcity * weights["position_scarcity"]
    contributions.append(
        ("Position", position_contrib, f"{position_scarcity:.1f}/10 scarcity")
    )

    # Sort by contribution value (descending)
    contributions.sort(key=lambda x: x[1], reverse=True)

    # Get ALL factors (not just top 3)
    all_factors = []

    # Add all contributing factors
    for factor_name, contrib_value, description in contributions:
        if contrib_value > 0:
            all_factors.append(description)

    # Add historical bonus if applicable
    historical_bonus = get_historical_bonus(name)
    if historical_bonus > 0:
        all_factors.append(f"+{historical_bonus:.1f} historical bonus")

    # Add position adjustment info
    if position == "Goalie":
        all_factors.append("40% goalie penalty applied")
    elif position in ["Center", "Left Wing", "Right Wing"]:
        all_factors.append("10% forward boost applied")
    elif position == "Defense":
        all_factors.append("5% defense boost applied")

    return " • ".join(all_factors)  # Show ALL factors


def _load_top_free_agents() -> List[Dict[str, Any]]:
    """Load top recommendations for swap analysis"""
    try:
        import json
        import glob
        import os

        # Find the latest recommendations file
        recommendation_files = glob.glob("output/recommendations_*.json")
        if not recommendation_files:
            return []

        # Get the most recent file
        latest_file = max(recommendation_files, key=os.path.getmtime)

        with open(latest_file, "r") as f:
            recommendations_data = json.load(f)

        if not recommendations_data:
            return []

        # Return the recommendations (they're already sorted by value score)
        return recommendations_data

    except Exception as e:
        print(f"Error loading recommendations: {e}")
        return []


def get_team_player_ranking_explanation(
    player: Dict[str, Any], comparison_data: Dict[str, Dict[str, float]]
) -> str:
    """Generate detailed weight system breakdown for My Team players"""
    try:
        stats = player.get("stats", {})
        position = player.get("position", "Unknown")

        # Get current performance metrics
        current_fp_per_game = calculate_fantasy_points_per_game(stats)
        games_played = stats.get("games_played", 0)

        # Get last year comparison
        last_year_stats = player.get("last_year_stats", {})
        last_year_fp_per_game = last_year_stats.get("fantasy_points_per_game", 0)

        # Get league comparison
        league_performance = get_performance_comparison(player, comparison_data)

        # Get historical bonus
        historical_bonus = get_historical_bonus(player.get("name", ""))

        # Build detailed breakdown
        factors = []

        # FP/G (current performance)
        factors.append(f"{current_fp_per_game:.1f} FP/G")

        # Upside potential (based on last year vs current)
        if last_year_fp_per_game > 0:
            upside_ratio = (
                last_year_fp_per_game / current_fp_per_game
                if current_fp_per_game > 0
                else 0
            )
            if upside_ratio >= 1.5:
                upside_score = 9.0
            elif upside_ratio >= 1.2:
                upside_score = 7.0
            elif upside_ratio >= 0.9:
                upside_score = 5.0
            else:
                upside_score = 3.0
        else:
            upside_score = 6.0  # Neutral for rookies
        factors.append(f"{upside_score:.1f}/10 upside")

        # Consistency (based on sample size and performance stability)
        if games_played >= 5:
            consistency_score = 8.0
        elif games_played >= 3:
            consistency_score = 6.0
        else:
            consistency_score = 4.0
        factors.append(f"{consistency_score:.1f}/10 consistency")

        # Position scarcity (based on position)
        if position == "Goalie":
            scarcity_score = 8.0
        elif position in ["Center", "Defense"]:
            scarcity_score = 6.0
        else:
            scarcity_score = 5.0
        factors.append(f"{scarcity_score:.1f}/10 scarcity")

        # Injury risk (only show if actually injured)
        injury_status = player.get("injury_status", "ACTIVE").lower()
        if "out" in injury_status:
            injury_score = 1.0
            factors.append(f"{injury_score:.1f}/10 injury risk (OUT)")
        elif "doubtful" in injury_status:
            injury_score = 3.0
            factors.append(f"{injury_score:.1f}/10 injury risk (DOUBTFUL)")
        elif "questionable" in injury_status:
            injury_score = 5.0
            factors.append(f"{injury_score:.1f}/10 injury risk (QUESTIONABLE)")
        # Don't show injury risk for healthy players - it's not useful

        # Historical bonus (All-Star appearances)
        historical_bonus = get_historical_bonus(player.get("name", ""))
        if historical_bonus > 0:
            factors.append(f"{historical_bonus:.1f} historical bonus")

        # Position boost applied
        if position == "Goalie":
            factors.append("40% goalie penalty applied")
        elif position == "Defense":
            factors.append("15% defense boost applied")
        elif position in ["Center", "Left Wing", "Right Wing"]:
            factors.append("No position boost applied")

        return " • ".join(factors)

    except Exception as e:
        return "Analysis unavailable"


def get_player_recommendation(
    player: Dict[str, Any], comparison_data: Dict[str, Dict[str, float]]
) -> str:
    """Generate actionable recommendation for a player based on all available data"""
    try:
        stats = player.get("stats", {})
        position = player.get("position", "Unknown")
        injury_status = player.get("injury_status", "ACTIVE")

        # Get current performance metrics
        current_fp_per_game = calculate_fantasy_points_per_game(stats)
        games_played = stats.get("games_played", 0)

        # Get last year comparison
        last_year_stats = player.get("last_year_stats", {})
        last_year_fp_per_game = last_year_stats.get("fantasy_points_per_game", 0)

        # Get league comparison
        league_performance = get_performance_comparison(player, comparison_data)

        # Get historical bonus (All-Star appearances)
        historical_bonus = get_historical_bonus(player.get("name", ""))

        # Recommendation logic based on multiple factors
        recommendation_score = 0

        # Factor 1: Current performance vs league (40% weight)
        if league_performance == "Better":
            recommendation_score += 40
        elif league_performance == "Average":
            recommendation_score += 20
        else:  # Worse
            recommendation_score += 0

        # Factor 2: Games played (20% weight) - need sufficient sample size
        if games_played >= 5:
            recommendation_score += 20
        elif games_played >= 3:
            recommendation_score += 10
        else:
            recommendation_score += 0

        # Factor 3: Historical performance (20% weight)
        if last_year_fp_per_game > 0:
            if (
                current_fp_per_game >= last_year_fp_per_game * 0.9
            ):  # Within 10% of last year
                recommendation_score += 20
            elif (
                current_fp_per_game >= last_year_fp_per_game * 0.7
            ):  # Within 30% of last year
                recommendation_score += 10
            else:
                recommendation_score += 0
        else:
            recommendation_score += 10  # No historical data, neutral

        # Factor 4: Historical bonus (20% weight)
        if historical_bonus >= 0.3:  # Elite players
            recommendation_score += 20
        elif historical_bonus >= 0.2:  # High tier
            recommendation_score += 15
        elif historical_bonus >= 0.1:  # Medium tier
            recommendation_score += 10
        else:
            recommendation_score += 0

        # Factor 5: Injury status penalty
        if "out" in injury_status.lower():
            recommendation_score -= 30
        elif "doubtful" in injury_status.lower():
            recommendation_score -= 20
        elif "questionable" in injury_status.lower():
            recommendation_score -= 10

        # Convert score to recommendation
        if recommendation_score >= 80:
            return "Must Keep"
        elif recommendation_score >= 60:
            return "Hold"
        elif recommendation_score >= 40:
            return "Watch"
        else:
            return "Drop"

    except Exception as e:
        print(
            f"Error generating recommendation for {player.get('name', 'Unknown')}: {e}"
        )
        return "Watch"  # Default to watch if error


def get_historical_bonus(name: str) -> float:
    """Get historical bonus based on All-Star Game appearances"""
    try:
        import json
        import os

        # Load from external file
        file_path = "data/all_star_appearances.json"
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                data = json.load(f)
                all_star_players = data.get("all_star_appearances", {})
        else:
            # Fallback to hardcoded data if file doesn't exist
            all_star_players = {
                "Sidney Crosby": 5,
                "Alex Ovechkin": 8,
                "Patrick Kane": 6,
                "Evgeni Malkin": 4,
                "Steven Stamkos": 6,
                "John Tavares": 6,
                "Claude Giroux": 3,
                "Erik Karlsson": 6,
                "Victor Hedman": 4,
                "Drew Doughty": 2,
                "Marc-Andre Fleury": 4,
                "Carey Price": 7,
                "Henrik Lundqvist": 3,
                "Brad Marchand": 3,
                "David Pastrnak": 2,
                "Artemi Panarin": 2,
                "Nikita Kucherov": 3,
                "Nathan MacKinnon": 3,
                "Connor McDavid": 6,
                "Leon Draisaitl": 3,
                "Auston Matthews": 4,
                "Mitch Marner": 1,
                "William Nylander": 1,
                "John Carlson": 1,
                "Roman Josi": 2,
                "Cale Makar": 2,
                "Adam Fox": 1,
                "Andrei Vasilevskiy": 2,
                "Connor Hellebuyck": 2,
                "Igor Shesterkin": 1,
                "Anze Kopitar": 2,
                "Brent Burns": 2,
                "Shea Weber": 2,
                "Duncan Keith": 2,
                "Tuukka Rask": 1,
                "Sergei Bobrovsky": 2,
                "Pekka Rinne": 1,
                "Roberto Luongo": 1,
                "Ryan O'Reilly": 1,
                "Patrice Bergeron": 1,
                "Jonathan Toews": 1,
                "Ryan Getzlaf": 1,
                "Corey Perry": 1,
                "Marc Staal": 1,
                "Cam Talbot": 1,
                "Kris Letang": 1,
                "Devon Toews": 0,
                "Zach Benson": 0,
                "Leo Carlsson": 0,
                "Dawson Mercer": 0,
                "Arturs Silovs": 0,
                "Travis Konecny": 2,
                "Mika Zibanejad": 2,
                "Johnny Gaudreau": 2,
                "Matthew Tkachuk": 2,
                "Brady Tkachuk": 1,
                "Sebastian Aho": 2,
                "Miro Heiskanen": 1,
                "Quinn Hughes": 1,
                "Jake Guentzel": 1,
                "Mark Scheifele": 1,
                "Gabriel Landeskog": 1,
                "Tyler Seguin": 1,
                "Jamie Benn": 1,
                "Taylor Hall": 1,
                "Phil Kessel": 1,
                "Jeff Skinner": 1,
                "Tyler Toffoli": 1,
                "Brock Boeser": 1,
                "Elias Pettersson": 1,
                "Bo Horvat": 1,
                "Mathew Barzal": 1,
                "Anders Lee": 1,
                "Josh Bailey": 1,
                "Ryan Nugent-Hopkins": 1,
            }

        appearances = all_star_players.get(name, 0)

        # Calculate bonus based on appearances
        if appearances >= 5:
            return 0.4  # Elite tier
        elif appearances >= 3:
            return 0.35  # High tier
        elif appearances >= 2:
            return 0.3  # Medium tier
        elif appearances >= 1:
            return 0.2  # Low tier
        else:
            return 0.0  # No bonus

    except Exception as e:
        print(f"Error getting historical bonus for {name}: {e}")
        return 0.0


def render_recommendations_tab(data: Dict[str, Any]) -> html.Div:
    """Render recommendations tab"""
    # Use full recommendations with AI insights if available, otherwise fall back to summary
    recommendations = data.get(
        "full_recommendations", data.get("top_recommendations", [])
    )

    if not recommendations:
        return html.Div(
            [
                html.H3("No Recommendations Available"),
                html.P("Run the analysis pipeline to generate recommendations."),
            ]
        )

    cards = []
    for i, rec in enumerate(recommendations, 1):
        # Get AI insight if available
        ai_insight = rec.get("ai_insight", "Analysis not available")

        # Handle different data structures (summary vs full recommendations)
        value_score = rec.get(
            "value_score", rec.get("analysis", {}).get("value_score", 0)
        )
        fp_per_game = rec.get(
            "fantasy_points_per_game", rec.get("fantasy_points_per_game", 0)
        )

        # Get last year comparison data
        last_year_stats = rec.get("last_year_stats", {})
        last_year_fp_per_game = last_year_stats.get("fantasy_points_per_game", 0)
        last_year_games = last_year_stats.get("games_played", 0)

        # Calculate performance vs last year
        if last_year_fp_per_game > 0:
            performance_ratio = fp_per_game / last_year_fp_per_game
            if performance_ratio >= 1.2:
                last_year_status = "BETTER than last year"
                status_color = "#28a745"  # Green
            elif performance_ratio >= 0.8:
                last_year_status = "AVERAGE vs last year"
                status_color = "#ffc107"  # Yellow
            else:
                last_year_status = "WORSE than last year"
                status_color = "#dc3545"  # Red
        else:
            last_year_status = "No last year data"
            status_color = "#6c757d"  # Gray
            performance_ratio = 0

        # Generate ranking explanation
        ranking_explanation = get_ranking_explanation(rec, i, recommendations)

        card = html.Div(
            [
                html.H4(
                    f"{i}. {rec['name']}", style={"color": "#2E86AB", "margin": "0"}
                ),
                html.P(
                    f"Position: {rec['position']} | Team: {rec['team']}",
                    style={"margin": "5px 0", "color": "gray"},
                ),
                html.Div(
                    [
                        html.Span(
                            f"Value Score: {value_score:.1f}/10",
                            style={
                                "backgroundColor": "#E8F4FD",
                                "padding": "5px 10px",
                                "borderRadius": "3px",
                                "marginRight": "10px",
                            },
                        ),
                        html.Span(
                            f"FP/G: {fp_per_game:.2f}",
                            style={
                                "backgroundColor": "#E8F4FD",
                                "padding": "5px 10px",
                                "borderRadius": "3px",
                                "marginRight": "10px",
                            },
                        ),
                        html.Span(
                            f"Last Year: {last_year_fp_per_game:.2f}",
                            style={
                                "backgroundColor": "#F8F9FA",
                                "padding": "5px 10px",
                                "borderRadius": "3px",
                                "marginRight": "10px",
                            },
                        ),
                        html.Span(
                            last_year_status,
                            style={
                                "backgroundColor": status_color,
                                "color": "white",
                                "padding": "5px 10px",
                                "borderRadius": "3px",
                                "fontSize": "12px",
                                "fontWeight": "bold",
                            },
                        ),
                    ],
                    style={"margin": "10px 0"},
                ),
                # Add ranking explanation
                html.Div(
                    [
                        html.H5(
                            "Why This Ranking:",
                            style={"margin": "10px 0 5px 0", "color": "#2E86AB"},
                        ),
                        html.P(
                            ranking_explanation,
                            style={
                                "backgroundColor": "#FFF3CD",
                                "padding": "10px",
                                "borderRadius": "5px",
                                "borderLeft": "4px solid #FFC107",
                                "margin": "0",
                                "fontSize": "14px",
                                "lineHeight": "1.4",
                                "fontStyle": "italic",
                            },
                        ),
                    ],
                    style={"margin": "10px 0"},
                ),
                # Add AI insight
                html.Div(
                    [
                        html.H5(
                            "Analysis:",
                            style={"margin": "10px 0 5px 0", "color": "#2E86AB"},
                        ),
                        html.P(
                            ai_insight,
                            style={
                                "backgroundColor": "#F8F9FA",
                                "padding": "10px",
                                "borderRadius": "5px",
                                "borderLeft": "4px solid #2E86AB",
                                "margin": "0",
                                "fontSize": "14px",
                                "lineHeight": "1.4",
                            },
                        ),
                    ],
                    style={"margin": "10px 0"},
                ),
            ],
            style={
                "backgroundColor": "white",
                "padding": "20px",
                "margin": "10px 0",
                "borderRadius": "8px",
                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
            },
        )
        cards.append(card)

    return html.Div(
        [html.H3(f"Top {len(recommendations)} Pickup Recommendations"), html.Div(cards)]
    )


def render_my_team_tab(data: Dict[str, Any]) -> html.Div:
    """Render my team tab"""
    team_name = data.get("team_name", "Unknown Team")
    team_record = data.get("team_record", "Unknown Record")
    roster = data.get("team_roster", [])

    roster_content = []
    if roster:
        # Get comparison data for performance analysis
        comparison_data = get_player_comparison_data()

        # Create roster table
        roster_rows = [
            html.Tr(
                [
                    html.Th(
                        "Player",
                        style={
                            "textAlign": "left",
                            "padding": "8px",
                            "backgroundColor": "#f8f9fa",
                            "fontWeight": "bold",
                            "border": "1px solid #ddd",
                        },
                    ),
                    html.Th(
                        "Position",
                        style={
                            "textAlign": "center",
                            "padding": "8px",
                            "backgroundColor": "#f8f9fa",
                            "fontWeight": "bold",
                            "border": "1px solid #ddd",
                        },
                    ),
                    html.Th(
                        "Team",
                        style={
                            "textAlign": "left",
                            "padding": "8px",
                            "backgroundColor": "#f8f9fa",
                            "fontWeight": "bold",
                            "border": "1px solid #ddd",
                        },
                    ),
                    html.Th(
                        "Games",
                        style={
                            "textAlign": "center",
                            "padding": "8px",
                            "backgroundColor": "#f8f9fa",
                            "fontWeight": "bold",
                            "border": "1px solid #ddd",
                        },
                    ),
                    html.Th(
                        "Points",
                        style={
                            "textAlign": "center",
                            "padding": "8px",
                            "backgroundColor": "#f8f9fa",
                            "fontWeight": "bold",
                            "border": "1px solid #ddd",
                        },
                    ),
                    html.Th(
                        "vs League",
                        style={
                            "textAlign": "center",
                            "padding": "8px",
                            "backgroundColor": "#f8f9fa",
                            "fontWeight": "bold",
                            "border": "1px solid #ddd",
                            "cursor": "help",
                        },
                        title="Compares each player's FP/G against other rostered players in your league (excluding your own team):\n🟢 Better - Top 25% (75th percentile and above)\n🟡 Average - Middle 50% (25th-75th percentile)\n🔴 Worse - Bottom 25% (below 25th percentile)",
                    ),
                    html.Th(
                        "FP/G",
                        style={
                            "textAlign": "center",
                            "padding": "8px",
                            "backgroundColor": "#f8f9fa",
                            "fontWeight": "bold",
                            "border": "1px solid #ddd",
                        },
                    ),
                    html.Th(
                        "Last Year",
                        style={
                            "textAlign": "center",
                            "padding": "8px",
                            "backgroundColor": "#f8f9fa",
                            "fontWeight": "bold",
                            "border": "1px solid #ddd",
                        },
                    ),
                    html.Th(
                        "Swap Analysis",
                        style={
                            "textAlign": "center",
                            "padding": "8px",
                            "backgroundColor": "#f8f9fa",
                            "fontWeight": "bold",
                            "border": "1px solid #ddd",
                            "cursor": "help",
                        },
                        title="AI-powered swap analysis comparing your players to available free agents:\n🟢 Keep - Player performing well or has strong upside\n🟡 Consider Swap - Better options available, consider specific targets\n🔴 Must Swap - Clear upgrade available, specific recommendations provided",
                    ),
                    html.Th(
                        "Value Breakdown",
                        style={
                            "textAlign": "left",
                            "padding": "8px",
                            "backgroundColor": "#f8f9fa",
                            "fontWeight": "bold",
                            "border": "1px solid #ddd",
                            "cursor": "help",
                        },
                        title="Detailed scoring breakdown: FP/G, upside, consistency, scarcity, injury risk, and position adjustments",
                    ),
                ]
            )
        ]

        # Get OpenAI recommendations for all players
        from openai_team_analyzer import get_openai_recommendation

        # Load top free agents for comparison
        top_free_agents = _load_top_free_agents()

        openai_recommendations = get_openai_recommendation(
            roster, comparison_data, top_free_agents
        )

        # Debug: Print what we got from OpenAI
        print(f"OpenAI recommendations received: {len(openai_recommendations)} players")
        for player_name, rec in openai_recommendations.items():
            print(f"  {player_name}: {rec}")

        # Calculate performance for all players and sort them
        players_with_performance = []
        for player in roster:
            stats = player.get("stats", {})
            fp_per_game = calculate_fantasy_points_per_game(stats)
            performance = get_performance_comparison(player, comparison_data)

            # Add performance score for sorting (Better=3, Average=2, Worse=1, Unknown=0)
            perf_score = {"Better": 3, "Average": 2, "Worse": 1}.get(performance, 0)

            players_with_performance.append(
                {
                    "player": player,
                    "stats": stats,
                    "fp_per_game": fp_per_game,
                    "performance": performance,
                    "perf_score": perf_score,
                    "openai_rec": openai_recommendations.get(
                        player.get("name", ""),
                        {
                            "recommendation": "Keep",
                            "rationale": "Analysis in progress...",
                        },
                    ),
                }
            )

        # Sort by performance (Better first), then by FP/G (highest first)
        players_with_performance.sort(
            key=lambda x: (x["perf_score"], x["fp_per_game"]), reverse=True
        )

        # Create table rows from sorted players
        for player_data in players_with_performance:
            player = player_data["player"]
            stats = player_data["stats"]
            fp_per_game = player_data["fp_per_game"]
            performance = player_data["performance"]

            # Get last year comparison data
            last_year_stats = player.get("last_year_stats", {})
            last_year_fp_per_game = last_year_stats.get("fantasy_points_per_game", 0)
            last_year_games = last_year_stats.get("games_played", 0)

            # Calculate performance vs last year
            if last_year_fp_per_game > 0:
                performance_ratio = fp_per_game / last_year_fp_per_game
                if performance_ratio >= 1.2:
                    last_year_status = "BETTER"
                    last_year_color = "#28a745"  # Green
                elif performance_ratio >= 0.8:
                    last_year_status = "AVERAGE"
                    last_year_color = "#ffc107"  # Yellow
                else:
                    last_year_status = "WORSE"
                    last_year_color = "#dc3545"  # Red
            else:
                last_year_status = "N/A"
                last_year_color = "#6c757d"  # Gray

            # Color code performance
            perf_color = {
                "Better": "#28a745",  # Green
                "Average": "#ffc107",  # Yellow
                "Worse": "#dc3545",  # Red
            }.get(performance, "#6c757d")  # Gray for unknown

            roster_rows.append(
                html.Tr(
                    [
                        html.Td(
                            player.get("name", "Unknown"),
                            style={
                                "textAlign": "left",
                                "padding": "8px",
                                "border": "1px solid #ddd",
                            },
                        ),
                        html.Td(
                            player.get("position", "N/A"),
                            style={
                                "textAlign": "center",
                                "padding": "8px",
                                "border": "1px solid #ddd",
                            },
                        ),
                        html.Td(
                            player.get("team", "N/A"),
                            style={
                                "textAlign": "left",
                                "padding": "8px",
                                "border": "1px solid #ddd",
                            },
                        ),
                        html.Td(
                            stats.get("games_played", 0),
                            style={
                                "textAlign": "center",
                                "padding": "8px",
                                "border": "1px solid #ddd",
                            },
                        ),
                        html.Td(
                            f"{stats.get('goals', 0)}G {stats.get('assists', 0)}A",
                            style={
                                "textAlign": "center",
                                "padding": "8px",
                                "border": "1px solid #ddd",
                            },
                        ),
                        html.Td(
                            performance,
                            style={
                                "color": perf_color,
                                "fontWeight": "bold",
                                "textAlign": "center",
                                "padding": "8px",
                                "border": "1px solid #ddd",
                            },
                        ),
                        html.Td(
                            f"{fp_per_game:.2f}",
                            style={
                                "textAlign": "center",
                                "padding": "8px",
                                "border": "1px solid #ddd",
                            },
                        ),
                        html.Td(
                            f"{last_year_fp_per_game:.2f}",
                            style={
                                "textAlign": "center",
                                "padding": "8px",
                                "border": "1px solid #ddd",
                            },
                        ),
                        html.Td(
                            [
                                html.Div(
                                    player_data["openai_rec"]["recommendation"],
                                    style={
                                        "fontWeight": "bold",
                                        "color": {
                                            "Keep": "#28a745",  # Green
                                            "Consider Swap": "#ffc107",  # Yellow
                                            "Must Swap": "#dc3545",  # Red
                                        }.get(
                                            player_data["openai_rec"]["recommendation"],
                                            "#6c757d",
                                        ),
                                    },
                                ),
                                html.Div(
                                    player_data["openai_rec"]["rationale"],
                                    style={
                                        "fontSize": "11px",
                                        "fontStyle": "italic",
                                        "color": "#666",
                                        "marginTop": "2px",
                                    },
                                ),
                            ],
                            style={
                                "textAlign": "center",
                                "padding": "8px",
                                "border": "1px solid #ddd",
                            },
                        ),
                        html.Td(
                            get_team_player_ranking_explanation(
                                player, comparison_data
                            ),
                            style={
                                "textAlign": "left",
                                "padding": "8px",
                                "border": "1px solid #ddd",
                                "fontSize": "12px",
                                "fontStyle": "italic",
                            },
                        ),
                    ]
                )
            )

        roster_content = [
            html.H4("Roster"),
            html.P(
                "Performance comparison vs other drafted players in your league (excluding your own team). Sorted by performance (Better → Average → Worse), then by FP/G."
            ),
            html.Table(
                roster_rows,
                style={
                    "width": "100%",
                    "borderCollapse": "collapse",
                    "border": "1px solid #ddd",
                    "fontFamily": "Arial, sans-serif",
                    "fontSize": "14px",
                },
            ),
        ]
    else:
        roster_content = [
            html.H4("Roster"),
            html.P("No roster data available. Run the analysis to load team data."),
        ]

    return html.Div(
        [
            html.H3(f"Team: {team_name}"),
            html.P(f"Record: {team_record}"),
            html.P(
                f"Last Updated: {format_timestamp(data.get('timestamp', 'Unknown'))}"
            ),
            html.Div(
                roster_content,
                style={
                    "backgroundColor": "white",
                    "padding": "20px",
                    "margin": "10px 0",
                    "borderRadius": "8px",
                    "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                },
            ),
        ]
    )


def render_swap_analysis_tab(data: Dict[str, Any]) -> html.Div:
    """Render swap analysis tab with detailed OpenAI analysis"""
    roster = data.get("team_roster", [])


    if not roster:
        return html.Div(
            [
                html.H3("No Team Data Available"),
                html.P("Team data will be displayed here when available."),
            ]
        )

    # Use the same logic as My Team tab to get recommendations
    from openai_team_analyzer import get_openai_recommendation

    # Get comparison data
    comparison_data = get_player_comparison_data()

    # Load top free agents for comparison
    top_free_agents = _load_top_free_agents()

    # Generate recommendations for all players (same as My Team tab)
    openai_recommendations = get_openai_recommendation(
        roster, comparison_data, top_free_agents
    )

    # Add recommendations to roster data
    roster_with_recommendations = []
    for player in roster:
        player_name = player.get("name", "")
        player["openai_rec"] = openai_recommendations.get(
            player_name,
            {"recommendation": "Keep", "rationale": "Analysis in progress..."},
        )
        roster_with_recommendations.append(player)

    # Find players with "Consider Swap" recommendations
    swap_candidates = []
    for player in roster_with_recommendations:
        # Check both possible field names for recommendations
        recommendation = ""
        if "openai_rec" in player:
            recommendation = player["openai_rec"].get("recommendation", "")
        else:
            recommendation = player.get("recommendation", "")

        print(
            f"DEBUG: {player.get('name', 'Unknown')} recommendation: '{recommendation}'"
        )
        if "Consider Swap" in recommendation:
            swap_candidates.append(player)

    print(f"DEBUG: Found {len(swap_candidates)} swap candidates")

    if not swap_candidates:
        return html.Div(
            [
                html.H3("🔄 Swap Analysis"),
                html.P(
                    "No swap candidates found. All players are recommended to keep."
                ),
                html.P("Check back after the next analysis run for potential swaps."),
                html.P(
                    f"DEBUG: Checked {len(roster)} players for swap recommendations."
                ),
            ]
        )

    # Create swap analysis cards
    swap_cards = []
    for player in swap_candidates:
        player_name = player.get("name", "Unknown")
        position = player.get("position", "Unknown")
        team = player.get("team", "Unknown")
        current_fp = player.get("fantasy_points_per_game", 0)

        # Extract swap target from recommendation
        recommendation = ""
        rationale = ""
        if "openai_rec" in player:
            recommendation = player["openai_rec"].get("recommendation", "")
            rationale = player["openai_rec"].get("rationale", "")
        else:
            recommendation = player.get("recommendation", "")
            rationale = player.get("rationale", "")

        swap_target = "Unknown Player"
        fp_improvement = 0

        # Parse the rationale to extract target player and FP improvement
        if "Consider Swap" in recommendation and "Moderate upgrade:" in rationale:
            import re

            # Extract target player name from "Moderate upgrade: PlayerName (+X.X FP/G improvement)"
            match = re.search(
                r"Moderate upgrade: ([^(]+) \(\+(\d+\.?\d*) FP/G improvement\)",
                rationale,
            )
            if match:
                swap_target = match.group(1).strip()
                fp_improvement = float(match.group(2))
                print(
                    f"DEBUG: Extracted swap target '{swap_target}' with {fp_improvement} FP/G improvement"
                )
            else:
                print(f"DEBUG: Could not parse rationale: '{rationale}'")

        # Create swap analysis card
        card = html.Div(
            [
                html.H4(
                    f"🔄 {player_name} → {swap_target}",
                    style={"color": "#2E86AB", "marginBottom": "15px"},
                ),
                html.Div(
                    [
                        html.P(f"Position: {position} | Team: {team}"),
                        html.P(f"Current FP/G: {current_fp:.2f}"),
                        html.P(f"Potential Target: {swap_target}"),
                        html.P(f"Potential Improvement: +{fp_improvement:.1f} FP/G"),
                    ],
                    style={"marginBottom": "15px"},
                ),
                html.Div(
                    [
                        html.H5("🤖 AI Analysis:", style={"color": "#2E86AB"}),
                        html.Div(
                            id=f"swap-analysis-{player_name.replace(' ', '-')}",
                            children=[
                                html.P(
                                    "Loading detailed analysis...",
                                    style={"fontStyle": "italic", "color": "#666"},
                                )
                            ],
                            style={
                                "backgroundColor": "#F8F9FA",
                                "padding": "15px",
                                "borderRadius": "5px",
                                "borderLeft": "4px solid #2E86AB",
                                "margin": "10px 0",
                            },
                        ),
                    ]
                ),
            ],
            style={
                "backgroundColor": "white",
                "padding": "20px",
                "margin": "15px 0",
                "borderRadius": "8px",
                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                "border": "2px solid #E3F2FD",
            },
        )
        swap_cards.append(card)

    return html.Div(
        [
            html.H3("🔄 Detailed Swap Analysis"),
            html.P(
                "AI-powered analysis of potential player swaps with internet access for latest news and insights."
            ),
            html.Div(swap_cards),
        ]
    )


def render_standings_tab(data: Dict[str, Any]) -> html.Div:
    """Render league standings tab"""
    standings = data.get("league_standings", [])

    if not standings:
        return html.Div(
            [
                html.H3("No Standings Data Available"),
                html.P("Standings data will be displayed here when available."),
            ]
        )

    # Create standings table
    table_rows = [
        html.Tr(
            [html.Th("Rank"), html.Th("Team"), html.Th("Record"), html.Th("Points")]
        )
    ]

    for team in standings:
        table_rows.append(
            html.Tr(
                [
                    html.Td(team.get("rank", "N/A")),
                    html.Td(team.get("team_name", "Unknown")),
                    html.Td(team.get("record", "N/A")),
                    html.Td(team.get("points", "N/A")),
                ]
            )
        )

    return html.Div(
        [
            html.H3("League Standings"),
            html.Table(
                table_rows,
                style={
                    "width": "100%",
                    "borderCollapse": "collapse",
                    "backgroundColor": "white",
                    "borderRadius": "8px",
                    "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                },
            ),
        ]
    )


def render_analytics_tab(data: Dict[str, Any]) -> html.Div:
    """Render analytics tab with charts"""
    recommendations = data.get("top_recommendations", [])

    if not recommendations:
        return html.Div(
            [
                html.H3("No Analytics Data Available"),
                html.P(
                    "Analytics will be displayed here when recommendations are available."
                ),
            ]
        )

    # Create value score chart
    df = pd.DataFrame(recommendations)

    fig_value = px.bar(
        df,
        x="name",
        y="value_score",
        title="Player Value Scores",
        color="value_score",
        color_continuous_scale="Blues",
    )
    fig_value.update_layout(xaxis_tickangle=-45)

    # Create fantasy points chart
    fig_points = px.bar(
        df,
        x="name",
        y="fantasy_points_per_game",
        title="Fantasy Points per Game",
        color="fantasy_points_per_game",
        color_continuous_scale="Greens",
    )
    fig_points.update_layout(xaxis_tickangle=-45)

    return html.Div(
        [
            html.H3("Analytics Dashboard"),
            dcc.Graph(figure=fig_value),
            dcc.Graph(figure=fig_points),
        ]
    )


# Add CSS styling
app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f8f9fa;
                margin: 0;
                padding: 20px;
            }
            .dash-tabs {
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .dash-tab {
                background-color: #f8f9fa;
                border: none;
                padding: 15px 25px;
            }
            .dash-tab--selected {
                background-color: #2E86AB;
                color: white;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""


def render_general_analysis_tab(data: Dict[str, Any]) -> html.Div:
    """Render general analysis and insights tab"""
    try:
        # Get team data
        team_data = data.get("team_roster", [])
        recommendations = data.get(
            "full_recommendations", data.get("top_recommendations", [])
        )
        standings = data.get("league_standings", [])

        insights = []

        # Team Performance Analysis
        if team_data:
            total_fp = sum(
                calculate_fantasy_points_per_game(player.get("stats", {}))
                for player in team_data
            )
            avg_fp_per_player = total_fp / len(team_data) if team_data else 0

            insights.append(
                {
                    "title": "Team Performance Overview",
                    "content": f"Your team averages {avg_fp_per_player:.2f} fantasy points per player. With {len(team_data)} rostered players, you're generating solid fantasy production across your lineup.",
                }
            )

        # Recommendation Quality Analysis
        if recommendations:
            high_value_picks = [
                r
                for r in recommendations
                if r.get("analysis", {}).get("value_score", 0) > 2.0
            ]
            goalie_picks = [r for r in recommendations if r.get("position") == "G"]
            skater_picks = [r for r in recommendations if r.get("position") != "G"]

            insights.append(
                {
                    "title": "Pickup Opportunities",
                    "content": f"Found {len(high_value_picks)} high-value pickups (value score > 2.0). {len(goalie_picks)} goalies and {len(skater_picks)} skaters available. Focus on goalies for immediate impact - they typically score higher FP/G.",
                }
            )

        # League Standing Analysis
        if standings:
            my_team_rank = None
            for team in standings:
                if team.get("team_name") == data.get("team_name"):
                    my_team_rank = team.get("rank", "Unknown")
                    break

            if my_team_rank:
                insights.append(
                    {
                        "title": "League Position",
                        "content": f"You're currently ranked #{my_team_rank} in your league. Consider aggressive pickups to climb the standings - the waiver wire offers several high-upside players.",
                    }
                )

        # General Strategy Insights
        insights.extend(
            [
                {
                    "title": "Strategy Recommendations",
                    "content": "1) Prioritize goalies - they score the most fantasy points. 2) Look for players with recent hot streaks. 3) Consider position scarcity - centers and goalies are harder to find. 4) Monitor injury reports for potential pickups.",
                },
                {
                    "title": "Waiver Wire Tips",
                    "content": "The best free agents often have low ownership percentages but high recent performance. Players like Leo Carlsson (3.62 FP/G) offer great value. Don't sleep on young players with upside potential.",
                },
            ]
        )

        # Create insight cards
        insight_cards = []
        for insight in insights:
            card = html.Div(
                [
                    html.H4(
                        insight["title"],
                        style={"color": "#2E86AB", "margin": "0 0 10px 0"},
                    ),
                    html.P(
                        insight["content"], style={"margin": "0", "lineHeight": "1.5"}
                    ),
                ],
                style={
                    "backgroundColor": "white",
                    "padding": "20px",
                    "margin": "15px 0",
                    "borderRadius": "8px",
                    "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                    "borderLeft": "4px solid #2E86AB",
                },
            )
            insight_cards.append(card)

        return html.Div(
            [
                html.H3("General Analysis & Insights"),
                html.P(
                    "Strategic analysis and recommendations based on your league data."
                ),
                html.Div(insight_cards),
            ]
        )

    except Exception as e:
        return html.Div(
            [
                html.H3("General Analysis"),
                html.P(f"Error loading analysis: {str(e)}"),
            ]
        )


def main():
    """Run the dashboard"""
    print("Starting Fantasy Hockey Dashboard...")

    # Get port from environment variable (for Render deployment)
    port = int(os.environ.get("PORT", DASHBOARD_CONFIG["port"]))

    print(f"Dashboard will be available at: http://localhost:{port}")

    app.run_server(
        host=DASHBOARD_CONFIG["host"],
        port=port,
        debug=False,  # Set to False for production
    )


if __name__ == "__main__":
    main()
