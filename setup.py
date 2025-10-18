"""
Setup script for Fantasy Hockey Pipeline
Helps users configure the system
"""

import os
import json
import getpass
from typing import Dict, Any


def create_env_file():
    """Create .env file from user input"""
    print("🔧 Fantasy Hockey Pipeline Setup")
    print("=" * 50)

    # Check if .env already exists
    if os.path.exists(".env"):
        overwrite = input("⚠️  .env file already exists. Overwrite? (y/N): ").lower()
        if overwrite != "y":
            print("Setup cancelled.")
            return

    print("\n📋 ESPN Fantasy Hockey Configuration")
    print("You'll need to get these values from your ESPN Fantasy Hockey league:")
    print("1. Log into ESPN Fantasy Hockey")
    print("2. Open browser dev tools (F12)")
    print("3. Go to Application/Storage > Cookies")
    print("4. Copy your espn_s2 and SWID values")
    print()

    # Get ESPN credentials
    league_id = input("Enter your League ID: ").strip()
    team_id = input("Enter your Team ID: ").strip()
    espn_s2 = getpass.getpass("Enter your ESPN_S2 cookie (hidden): ").strip()
    espn_swid = getpass.getpass("Enter your ESPN_SWID cookie (hidden): ").strip()

    print("\n🤖 OpenAI Configuration")
    print("Get your API key from: https://platform.openai.com/api-keys")
    openai_key = getpass.getpass("Enter your OpenAI API key (hidden): ").strip()

    print("\n🌐 Optional: Netlify Configuration")
    print("Skip these if you don't want to deploy to Netlify")
    print("You can always add Netlify later if you want the web dashboard")

    use_netlify = input("Do you want to configure Netlify now? (y/N): ").lower()

    if use_netlify == "y":
        netlify_site_id = input("Enter Netlify Site ID: ").strip()
        netlify_token = getpass.getpass("Enter Netlify Access Token (hidden): ").strip()
    else:
        netlify_site_id = ""
        netlify_token = ""
        print("✅ Skipping Netlify configuration")

    # Create .env content
    env_content = f"""# ESPN Fantasy Hockey Credentials
ESPN_S2={espn_s2}
ESPN_SWID={espn_swid}

# OpenAI API Key
OPENAI_API_KEY={openai_key}

# League Configuration
LEAGUE_ID={league_id}
YEAR=2025
TEAM_ID={team_id}

# Optional: Netlify Configuration
NETLIFY_SITE_ID={netlify_site_id}
NETLIFY_ACCESS_TOKEN={netlify_token}
"""

    # Write .env file
    with open(".env", "w") as f:
        f.write(env_content)

    print("\n✅ Configuration saved to .env file")
    print("⚠️  Keep your .env file secure and never commit it to version control!")


def create_gitignore():
    """Create .gitignore file"""
    gitignore_content = """# Environment variables
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/
*.log

# Data files (optional - remove if you want to track data)
data/
output/
reports/

# OS
.DS_Store
Thumbs.db

# Netlify
.netlify/
"""

    with open(".gitignore", "w") as f:
        f.write(gitignore_content)

    print("✅ Created .gitignore file")


def test_configuration():
    """Test the configuration"""
    print("\n🧪 Testing Configuration...")

    try:
        from config import LEAGUE_ID, TEAM_ID, OPENAI_API_KEY, ESPN_S2, ESPN_SWID

        print(f"✅ League ID: {LEAGUE_ID}")
        print(f"✅ Team ID: {TEAM_ID}")
        print(f"✅ OpenAI API Key: {'Set' if OPENAI_API_KEY else 'Not set'}")
        print(f"✅ ESPN S2: {'Set' if ESPN_S2 else 'Not set'}")
        print(f"✅ ESPN SWID: {'Set' if ESPN_SWID else 'Not set'}")

        return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing Dependencies...")

    try:
        import subprocess

        result = subprocess.run(
            ["pip", "install", "-r", "requirements.txt"], capture_output=True, text=True
        )

        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
            return True
        else:
            print(f"❌ Failed to install dependencies: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False


def create_sample_data():
    """Create sample data for testing"""
    print("\n📊 Creating Sample Data...")

    sample_team = {
        "team_name": "Sample Team",
        "team_id": "123456",
        "record": "5-3-1",
        "points": 1250.5,
        "roster": [
            {
                "id": "12345",
                "name": "Connor McDavid",
                "position": "C",
                "team": "EDM",
                "injury_status": "",
                "stats": {
                    "games_played": 8,
                    "goals": 4,
                    "assists": 8,
                    "points": 12,
                    "plus_minus": 5,
                    "powerplay_points": 3,
                    "shots_on_goal": 25,
                    "hits": 8,
                    "blocks": 2,
                },
            }
        ],
    }

    sample_agents = [
        {
            "id": "67890",
            "name": "Sample Player",
            "position": "LW",
            "team": "TOR",
            "injury_status": "",
            "stats": {
                "games_played": 7,
                "goals": 3,
                "assists": 5,
                "points": 8,
                "plus_minus": 2,
                "powerplay_points": 2,
                "shots_on_goal": 20,
                "hits": 12,
                "blocks": 4,
            },
            "ownership_percentage": 45,
            "projected_points": 65,
        }
    ]

    # Save sample data
    os.makedirs("data", exist_ok=True)

    with open("data/my_team.json", "w") as f:
        json.dump(sample_team, f, indent=2)

    with open("data/free_agents.json", "w") as f:
        json.dump(sample_agents, f, indent=2)

    print("✅ Sample data created")


def main():
    """Main setup function"""
    print("🏒 Fantasy Hockey Pipeline Setup")
    print("=" * 50)

    # Create .env file
    create_env_file()

    # Create .gitignore
    create_gitignore()

    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed at dependency installation")
        return

    # Test configuration
    if not test_configuration():
        print("❌ Setup failed at configuration test")
        return

    # Create sample data
    create_sample_data()

    print("\n🎉 Setup Complete!")
    print("=" * 50)
    print("Next steps:")
    print("1. Run 'python main.py' to test the pipeline")
    print("2. Run 'python dashboard.py' to start the web interface")
    print("3. Run 'python scheduler.py' for scheduled analysis")
    print("4. Check the README.md for more information")
    print("\nHappy fantasy hockey managing! 🏒")


if __name__ == "__main__":
    main()
