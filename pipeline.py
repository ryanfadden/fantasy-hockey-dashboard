"""
Main Fantasy Hockey Pipeline
Orchestrates data collection, analysis, and reporting
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any
from espn_client import ESPNFantasyClient
from statistical_analyzer import FantasyHockeyAnalyzer
from utils import setup_logging, send_notification

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


class FantasyHockeyPipeline:
    """Main pipeline for fantasy hockey analysis"""

    def __init__(self):
        """Initialize the pipeline components"""
        self.espn_client = ESPNFantasyClient()
        self.analyzer = FantasyHockeyAnalyzer()
        self.run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def run_full_analysis(self) -> Dict[str, Any]:
        """Run the complete analysis pipeline"""
        logger.info("Starting Fantasy Hockey Pipeline Analysis")

        try:
            # Step 1: Collect data from ESPN
            logger.info("Step 1: Collecting data from ESPN")
            team_data = self.espn_client.get_my_team()
            free_agents = self.espn_client.get_free_agents()
            standings = self.espn_client.get_league_standings()
            matchup_data = self.espn_client.get_matchup_data()
            all_teams_data = self.espn_client.get_all_teams_data()

            if not team_data or not free_agents:
                logger.error("Failed to collect data from ESPN")
                return {"error": "Data collection failed"}

            # Step 2: Analyze players (before saving to preserve calculated data)
            logger.info("Step 2: Analyzing players and generating recommendations")
            recommendations = self.analyzer.analyze_player_pickups(
                team_data, free_agents
            )

            # Step 3: Save raw data (after analysis to preserve calculated fantasy points)
            logger.info("Step 3: Saving raw data")
            self._save_raw_data(
                team_data, free_agents, standings, matchup_data, all_teams_data
            )

            # Step 4: Generate reports
            logger.info("Step 4: Generating analysis reports")
            report = self.analyzer.generate_report(recommendations, team_data)

            # Step 5: Save results
            logger.info("Step 5: Saving analysis results")
            self._save_results(recommendations, report, team_data, standings)

            # Step 6: Send notifications (optional)
            logger.info("Step 6: Sending notifications")
            self._send_notifications(recommendations, team_data)

            logger.info("Pipeline analysis completed successfully!")

            return {
                "status": "success",
                "timestamp": self.run_timestamp,
                "team_name": team_data.get("team_name", "Unknown"),
                "recommendations_count": len(recommendations),
                "top_recommendation": recommendations[0]["name"]
                if recommendations
                else None,
            }

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return {"error": str(e), "status": "failed"}

    def _save_raw_data(
        self,
        team_data: Dict[str, Any],
        free_agents: list,
        standings: list,
        matchup_data: Dict[str, Any],
        all_teams_data: list,
    ):
        """Save raw data from ESPN"""
        timestamp = self.run_timestamp

        # Save individual files
        self.espn_client.save_data_to_file(team_data, f"team_data_{timestamp}.json")
        self.espn_client.save_data_to_file(free_agents, f"free_agents_{timestamp}.json")
        self.espn_client.save_data_to_file(standings, f"standings_{timestamp}.json")
        self.espn_client.save_data_to_file(
            matchup_data, f"matchup_data_{timestamp}.json"
        )
        self.espn_client.save_data_to_file(
            all_teams_data, f"all_teams_data_{timestamp}.json"
        )

        # Save combined data
        combined_data = {
            "timestamp": timestamp,
            "team_data": team_data,
            "free_agents": free_agents,
            "standings": standings,
            "matchup_data": matchup_data,
        }

        self.espn_client.save_data_to_file(
            combined_data, f"combined_data_{timestamp}.json"
        )

    def _save_results(
        self,
        recommendations: list,
        report: str,
        team_data: Dict[str, Any],
        standings: list,
    ):
        """Save analysis results"""
        timestamp = self.run_timestamp

        # Save recommendations
        self.analyzer.save_analysis(
            recommendations, f"recommendations_{timestamp}.json"
        )

        # Save markdown report
        report_file = f"reports/analysis_report_{timestamp}.md"
        with open(report_file, "w") as f:
            f.write(report)

        # Save summary
        summary = {
            "timestamp": timestamp,
            "team_name": team_data.get("team_name", "Unknown"),
            "team_record": team_data.get("record", "Unknown"),
            "recommendations_count": len(recommendations),
            "top_recommendations": [
                {
                    "name": rec["name"],
                    "position": rec["position"],
                    "team": rec["team"],
                    "value_score": rec["analysis"]["value_score"],
                    "fantasy_points_per_game": rec["fantasy_points_per_game"],
                }
                for rec in recommendations[:5]
            ],
            "league_standings": standings[:5],  # Top 5 teams
        }

        with open(f"output/summary_{timestamp}.json", "w") as f:
            json.dump(summary, f, indent=2)

    def _send_notifications(self, recommendations: list, team_data: Dict[str, Any]):
        """Send notifications about analysis results"""
        try:
            if recommendations:
                top_rec = recommendations[0]
                message = f"""
Fantasy Hockey Analysis Complete!

Team: {team_data.get("team_name", "Unknown")}
Top Recommendation: {top_rec["name"]} ({top_rec["position"]})
Value Score: {top_rec["analysis"]["value_score"]:.1f}/10
Fantasy Points/Game: {top_rec["fantasy_points_per_game"]:.2f}

Total Recommendations: {len(recommendations)}
                """

                send_notification("Fantasy Hockey Analysis", message)

        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")

    def run_quick_check(self) -> Dict[str, Any]:
        """Run a quick check for immediate insights"""
        logger.info("Running quick fantasy hockey check")

        try:
            # Get current team and free agents
            team_data = self.espn_client.get_my_team()
            free_agents = self.espn_client.get_free_agents()

            if not team_data or not free_agents:
                return {"error": "Quick check failed - no data available"}

            # Quick analysis (top 5 free agents)
            top_agents = free_agents[:5]
            quick_recommendations = self.analyzer.analyze_player_pickups(
                team_data, top_agents
            )

            return {
                "status": "success",
                "team_name": team_data.get("team_name", "Unknown"),
                "quick_recommendations": [
                    {
                        "name": rec["name"],
                        "position": rec["position"],
                        "value_score": rec["analysis"]["value_score"],
                        "fantasy_points_per_game": rec["fantasy_points_per_game"],
                    }
                    for rec in quick_recommendations[:3]
                ],
            }

        except Exception as e:
            logger.error(f"Quick check failed: {e}")
            return {"error": str(e)}


def main():
    """Main entry point for the pipeline"""
    pipeline = FantasyHockeyPipeline()

    # Run full analysis
    result = pipeline.run_full_analysis()

    if result.get("status") == "success":
        print("Analysis completed successfully!")
        print(f"Team: {result['team_name']}")
        print(f"Recommendations: {result['recommendations_count']}")
        if result["top_recommendation"]:
            print(f"Top Pick: {result['top_recommendation']}")
    else:
        print(f"Analysis failed: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
