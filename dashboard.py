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
                dcc.Tab(label="🏆 League Standings", value="standings"),
                dcc.Tab(label="📈 Analytics", value="analytics"),
                dcc.Tab(label="💡 General Analysis", value="general-analysis"),
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

        # Fallback to latest recommendations
        rec_file = get_latest_data_file("output", "recommendations_")
        if rec_file:
            with open(rec_file, "r") as f:
                recommendations = json.load(f)
                return {
                    "recommendations": recommendations,
                    "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                }

        return {}
    except Exception as e:
        print(f"Error loading data: {e}")
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
    try:
        data = json.loads(data_json) if data_json else {}
    except:
        data = {}

    if active_tab == "recommendations":
        return render_recommendations_tab(data)
    elif active_tab == "my-team":
        return render_my_team_tab(data)
    elif active_tab == "standings":
        return render_standings_tab(data)
    elif active_tab == "analytics":
        return render_analytics_tab(data)
    elif active_tab == "general-analysis":
        return render_general_analysis_tab(data)
    else:
        return html.Div("Select a tab to view content")


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
        "fantasy_points_per_game": 0.4,
        "consistency_rating": 0.25,
        "upside_potential": 0.25,
        "position_scarcity": 0.1,
        "injury_risk": 0.1,
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

    # Injury risk contribution
    injury_risk = analysis.get("injury_risk", 0)
    injury_contrib = injury_risk * weights["injury_risk"]
    contributions.append(
        ("Health", injury_contrib, f"{injury_risk:.1f}/10 injury risk")
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
            factors.append("No forward boost applied")

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
    print(
        f"Dashboard will be available at: http://localhost:{DASHBOARD_CONFIG['port']}"
    )

    app.run_server(
        host=DASHBOARD_CONFIG["host"],
        port=DASHBOARD_CONFIG["port"],
        debug=DASHBOARD_CONFIG["debug"],
    )


if __name__ == "__main__":
    main()
