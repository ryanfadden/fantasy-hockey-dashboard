# Deploy Fantasy Hockey Dashboard to Render

This guide will help you deploy your Fantasy Hockey Dashboard to Render so you can access it online.

## Steps to Deploy

1. **Go to Render.com** and sign up/login
2. **Connect your GitHub account** to Render
3. **Create a new Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository: `ryanfadden/fantasy-hockey-dashboard`
   - Choose the repository

4. **Configure the service**:
   - **Name**: `fantasy-hockey-dashboard`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python dashboard.py`
   - **Plan**: Free

5. **Set Environment Variables**:
   - Go to the "Environment" tab
   - Add these variables:
     - `ESPN_S2`: Your ESPN S2 token
     - `ESPN_SWID`: Your ESPN SWID
     - `OPENAI_API_KEY`: Your OpenAI API key
     - `LEAGUE_ID`: Your league ID
     - `TEAM_ID`: Your team ID
     - `YEAR`: 2026 (or current year)

6. **Deploy**:
   - Click "Create Web Service"
   - Wait for the build to complete (5-10 minutes)
   - Your dashboard will be available at the provided URL!

## What You'll Get

Once deployed, you'll have:
- ✅ **My Team Tab**: Your roster with swap analysis
- ✅ **Recommendations Tab**: Top free agents
- ✅ **League Standings**: Current standings
- ✅ **Real-time Data**: Updates from ESPN
- ✅ **AI Analysis**: OpenAI-powered insights

## Troubleshooting

- If the build fails, check that all dependencies are in `requirements.txt`
- If the app crashes, check the logs in Render dashboard
- Make sure all environment variables are set correctly

## Cost

Render's free tier includes:
- 750 hours/month of usage
- Automatic sleep after 15 minutes of inactivity
- Free SSL certificate
- Custom domain support

Perfect for personal projects!
