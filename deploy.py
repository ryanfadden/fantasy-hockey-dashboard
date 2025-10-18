"""
Netlify Deployment Script
Handles deployment of the dashboard to Netlify
"""

import os
import json
import subprocess
import logging
from datetime import datetime
from typing import Dict, Any
from utils import setup_logging, load_json_file

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


class NetlifyDeployer:
    """Handles Netlify deployment"""

    def __init__(self):
        """Initialize the deployer"""
        self.site_id = os.getenv("NETLIFY_SITE_ID")
        self.access_token = os.getenv("NETLIFY_ACCESS_TOKEN")

        if not self.site_id or not self.access_token:
            logger.warning("Netlify credentials not configured")

    def build_static_site(self) -> bool:
        """Build static files for deployment"""
        try:
            logger.info("Building static site...")

            # Create static directory structure
            os.makedirs("static", exist_ok=True)
            os.makedirs("static/css", exist_ok=True)
            os.makedirs("static/js", exist_ok=True)

            # Generate static HTML from latest analysis
            self._generate_static_html()

            # Copy dashboard assets
            self._copy_dashboard_assets()

            logger.info("Static site built successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to build static site: {e}")
            return False

    def _generate_static_html(self):
        """Generate static HTML from analysis results"""
        try:
            # Load latest analysis data
            summary_file = self._get_latest_file("output", "summary_")
            if not summary_file:
                logger.warning("No analysis data found for static generation")
                return

            summary_data = load_json_file(summary_file)
            if not summary_data:
                return

            # Generate HTML
            html_content = self._create_html_template(summary_data)

            # Save to static directory
            with open("static/index.html", "w") as f:
                f.write(html_content)

            logger.info("Static HTML generated")

        except Exception as e:
            logger.error(f"Failed to generate static HTML: {e}")

    def _create_html_template(self, data: Dict[str, Any]) -> str:
        """Create HTML template with analysis data"""
        recommendations = data.get("top_recommendations", [])
        team_name = data.get("team_name", "Unknown Team")
        timestamp = data.get("timestamp", "Unknown")

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fantasy Hockey Analysis - {team_name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f8f9fa;
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #2E86AB, #A23B72);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px;
        }}
        .recommendation {{
            background: #f8f9fa;
            border-left: 4px solid #2E86AB;
            padding: 20px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
        }}
        .recommendation h3 {{
            margin: 0 0 10px 0;
            color: #2E86AB;
        }}
        .stats {{
            display: flex;
            gap: 15px;
            margin: 10px 0;
        }}
        .stat {{
            background: #e3f2fd;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 0.9em;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #eee;
        }}
        .no-data {{
            text-align: center;
            padding: 40px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏒 Fantasy Hockey Analysis</h1>
            <p>Team: {team_name} | Updated: {timestamp}</p>
        </div>
        
        <div class="content">
            <h2>Top Pickup Recommendations</h2>
"""

        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                html += f"""
            <div class="recommendation">
                <h3>{i}. {rec["name"]} ({rec["position"]}) - {rec["team"]}</h3>
                <div class="stats">
                    <div class="stat">Value Score: {rec["value_score"]:.1f}/10</div>
                    <div class="stat">Fantasy Points/Game: {rec["fantasy_points_per_game"]:.2f}</div>
                </div>
            </div>
"""
        else:
            html += """
            <div class="no-data">
                <p>No recommendations available. Run the analysis pipeline to generate recommendations.</p>
            </div>
"""

        html += (
            """
        </div>
        
        <div class="footer">
            <p>Generated by Fantasy Hockey Analysis Pipeline</p>
            <p>Last updated: """
            + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            + """</p>
        </div>
    </div>
</body>
</html>
"""
        )

        return html

    def _copy_dashboard_assets(self):
        """Copy dashboard assets to static directory"""
        try:
            # Create basic CSS file
            css_content = """
/* Fantasy Hockey Dashboard Styles */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: #f8f9fa;
    margin: 0;
    padding: 0;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.header {
    text-align: center;
    margin-bottom: 30px;
}

.header h1 {
    color: #2E86AB;
    margin-bottom: 10px;
}

.card {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    padding: 20px;
    margin: 20px 0;
}

.recommendation {
    border-left: 4px solid #2E86AB;
    padding: 15px;
    margin: 10px 0;
    background: #f8f9fa;
}

.stat {
    display: inline-block;
    background: #e3f2fd;
    padding: 5px 10px;
    border-radius: 4px;
    margin: 5px 10px 5px 0;
    font-size: 0.9em;
}
"""

            with open("static/css/style.css", "w") as f:
                f.write(css_content)

            logger.info("Dashboard assets copied")

        except Exception as e:
            logger.error(f"Failed to copy dashboard assets: {e}")

    def _get_latest_file(self, directory: str, pattern: str) -> str:
        """Get the latest file matching a pattern"""
        try:
            files = [f for f in os.listdir(directory) if pattern in f]
            if not files:
                return ""

            files.sort(
                key=lambda x: os.path.getmtime(os.path.join(directory, x)), reverse=True
            )
            return os.path.join(directory, files[0])
        except Exception as e:
            logger.error(f"Error getting latest file: {e}")
            return ""

    def deploy(self) -> bool:
        """Deploy to Netlify"""
        if not self.site_id or not self.access_token:
            logger.error("Netlify credentials not configured")
            return False

        try:
            logger.info("Deploying to Netlify...")

            # Set environment variables
            env = os.environ.copy()
            env["NETLIFY_SITE_ID"] = self.site_id
            env["NETLIFY_ACCESS_TOKEN"] = self.access_token

            # Run netlify deploy command
            result = subprocess.run(
                [
                    "netlify",
                    "deploy",
                    "--prod",
                    "--dir=static",
                    f"--site={self.site_id}",
                ],
                env=env,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                logger.info("Successfully deployed to Netlify")
                logger.info(f"Deploy output: {result.stdout}")
                return True
            else:
                logger.error(f"Netlify deployment failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False

    def run_full_deployment(self) -> bool:
        """Run the complete deployment process"""
        logger.info("Starting full deployment process")

        # Build static site
        if not self.build_static_site():
            return False

        # Deploy to Netlify
        if not self.deploy():
            return False

        logger.info("Full deployment completed successfully")
        return True


def main():
    """Main entry point for deployment"""
    deployer = NetlifyDeployer()

    print("🚀 Fantasy Hockey Netlify Deployment")
    print("=" * 50)

    if deployer.run_full_deployment():
        print("✅ Deployment successful!")
    else:
        print("❌ Deployment failed!")


if __name__ == "__main__":
    main()


