# Fantasy Hockey Pipeline - GitHub Secrets Setup

## Required Secrets

Add these secrets to your GitHub repository:

### ESPN Fantasy Hockey
- `ESPN_S2`: Your ESPN S2 cookie value
- `ESPN_SWID`: Your ESPN SWID cookie value  
- `LEAGUE_ID`: Your fantasy league ID
- `TEAM_ID`: Your team ID

### OpenAI
- `OPENAI_API_KEY`: Your OpenAI API key

### Optional: Netlify Deployment
- `NETLIFY_SITE_ID`: Your Netlify site ID
- `NETLIFY_ACCESS_TOKEN`: Your Netlify access token

## How to Add Secrets

1. Go to your GitHub repository
2. Click Settings > Secrets and variables > Actions
3. Click "New repository secret"
4. Add each secret with the exact name listed above

## Getting Your Values

### ESPN Credentials
1. Log into ESPN Fantasy Hockey
2. Open browser dev tools (F12)
3. Go to Application/Storage > Cookies
4. Copy the values for `espn_s2` and `SWID`

### League/Team IDs
1. Go to your fantasy league page
2. Look at the URL: `https://fantasy.espn.com/hockey/league?leagueId=123456`
3. The number after `leagueId=` is your League ID
4. Go to your team page to find your Team ID

### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key (starts with `sk-`)

### Netlify (Optional)
1. Go to https://app.netlify.com/
2. Create a new site or use existing
3. Get Site ID from site settings
4. Generate access token in user settings


