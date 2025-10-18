# Fantasy Hockey Automation Pipeline

An automated pipeline to help optimize your ESPN Fantasy Hockey team with AI-powered player recommendations.

## Features

- **Automated Data Collection**: Pulls your team roster and available free agents from ESPN
- **AI Analysis**: Uses OpenAI to analyze player performance and suggest pickups
- **Advanced Analytics**: Multiple analysis approaches including statistical modeling
- **Web Dashboard**: Beautiful interface to view recommendations
- **Automated Scheduling**: Runs analysis on a schedule via GitHub Actions
- **Netlify Deployment**: Easy deployment of the web interface

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Get ESPN Authentication**:
   - Log into ESPN Fantasy Hockey
   - Open browser dev tools (F12)
   - Go to Application/Storage > Cookies
   - Copy your `espn_s2` and `SWID` values

3. **Set Environment Variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Configure League Settings**:
   - Update `config.py` with your league ID and team info

## Usage

### Manual Analysis
```bash
python main.py
```

### Web Dashboard
```bash
python dashboard.py
```

### Automated Analysis
The system runs automatically via GitHub Actions every Monday at 12 PM UTC.

## Project Structure

```
├── main.py                 # Main analysis script
├── dashboard.py            # Web dashboard
├── espn_client.py         # ESPN API wrapper
├── analyzer.py            # AI analysis engine
├── config.py              # Configuration settings
├── utils.py               # Utility functions
├── .github/workflows/     # GitHub Actions
└── static/                # Web assets
```

## Analysis Features

1. **Player Performance Analysis**
   - Recent form trends
   - Statistical comparisons
   - Injury/lineup analysis

2. **AI Recommendations**
   - OpenAI-powered insights
   - Context-aware suggestions
   - Risk assessment

3. **Advanced Metrics**
   - Fantasy points per game
   - Consistency ratings
   - Upside potential

## Deployment

The web dashboard automatically deploys to Netlify when you push to the main branch.

