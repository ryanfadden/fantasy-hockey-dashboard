"""
Fantasy Hockey Pipeline - Quick Start Guide

This guide will help you get your ESPN Fantasy Hockey automation pipeline up and running.

## Prerequisites

- Python 3.7 or higher
- ESPN Fantasy Hockey account
- OpenAI API key (optional but recommended)
- Netlify account (optional, for web deployment)

## Quick Setup

1. **Run the setup script:**
   ```bash
   python setup.py
   ```
   This will guide you through configuring your ESPN credentials and API keys.

2. **Test the pipeline:**
   ```bash
   python main.py
   ```

3. **Start the web dashboard:**
   ```bash
   python dashboard.py
   ```
   Open http://localhost:8050 in your browser.

## Getting ESPN Credentials

1. Log into ESPN Fantasy Hockey
2. Open browser developer tools (F12)
3. Go to Application/Storage > Cookies
4. Find and copy these values:
   - `espn_s2` (long string)
   - `SWID` (UUID format)

## Getting Your League/Team IDs

1. Go to your ESPN Fantasy Hockey league
2. Look at the URL: `https://fantasy.espn.com/hockey/league?leagueId=123456`
3. The number after `leagueId=` is your League ID
4. Go to your team page and look for Team ID in the URL or page source

## OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key (starts with `sk-`)

## Usage

### Manual Analysis
```bash
python main.py
```

### Web Dashboard
```bash
python dashboard.py
```

### Scheduled Analysis
```bash
python scheduler.py
```

### Deploy to Netlify
```bash
python deploy.py
```

## GitHub Actions Setup

1. Go to your GitHub repository
2. Go to Settings > Secrets and variables > Actions
3. Add these secrets:
   - `ESPN_S2`: Your ESPN S2 cookie
   - `ESPN_SWID`: Your ESPN SWID cookie
   - `LEAGUE_ID`: Your league ID
   - `TEAM_ID`: Your team ID
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `NETLIFY_SITE_ID`: Your Netlify site ID (optional)
   - `NETLIFY_ACCESS_TOKEN`: Your Netlify token (optional)

## Troubleshooting

### Common Issues

1. **"Failed to connect to ESPN Fantasy Hockey"**
   - Check your League ID and Team ID
   - Verify your ESPN cookies are correct
   - Make sure your league is public or you have proper authentication

2. **"No recommendations available"**
   - Check if you have free agents in your league
   - Verify your scoring categories in config.py match your league

3. **"OpenAI API error"**
   - Check your API key is correct
   - Verify you have credits in your OpenAI account

### Getting Help

- Check the logs in the `logs/` directory
- Run `python utils.py` to check system status
- Review the configuration in `config.py`

## Customization

### Scoring Categories
Edit `config.py` to match your league's scoring:
```python
SCORING_CATEGORIES = {
    'goals': 3,
    'assists': 2,
    'plus_minus': 1,
    # Add your league's categories
}
```

### Analysis Settings
Adjust analysis parameters in `config.py`:
```python
ANALYSIS_SETTINGS = {
    'min_games_played': 5,
    'max_recommendations': 10,
    # Modify as needed
}
```

## File Structure

```
├── main.py              # Main analysis pipeline
├── dashboard.py         # Web dashboard
├── espn_client.py      # ESPN API client
├── analyzer.py         # Analysis engine
├── scheduler.py        # Scheduled analysis
├── deploy.py           # Netlify deployment
├── setup.py            # Setup script
├── config.py           # Configuration
├── utils.py            # Utility functions
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (create this)
├── data/               # Raw data storage
├── output/             # Analysis results
├── reports/            # Generated reports
├── static/             # Web assets
└── .github/workflows/  # GitHub Actions
```

## Next Steps

1. **Customize the analysis** - Modify the scoring and analysis logic
2. **Add more data sources** - Integrate additional hockey statistics
3. **Enhance the dashboard** - Add more visualizations and features
4. **Set up notifications** - Add email/Slack notifications for recommendations
5. **Expand analysis** - Add injury reports, lineup analysis, etc.

Happy fantasy hockey managing! 🏒


