import json
import os
from http.server import BaseHTTPRequestHandler
import sys
import io
from contextlib import redirect_stdout, redirect_stderr

# Add the project root to the Python path
sys.path.append('/opt/render/project/src')

def handler(request):
    """Netlify serverless function handler"""
    
    # Set up environment variables (you'll need to add these in Netlify)
    os.environ.setdefault('ESPN_S2', '')
    os.environ.setdefault('ESPN_SWID', '')
    os.environ.setdefault('OPENAI_API_KEY', '')
    
    try:
        # Import your dashboard components
        from dashboard import app
        
        # Create a simple HTML response
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Fantasy Hockey Dashboard</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .container { max-width: 1200px; margin: 0 auto; }
                .status { background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }
                .error { background: #ffe6e6; padding: 15px; border-radius: 5px; margin: 20px 0; }
                .info { background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }
                .github-link { text-align: center; margin: 20px 0; }
                .github-link a { color: #0366d6; text-decoration: none; font-weight: bold; }
                .github-link a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🏒 Fantasy Hockey Dashboard</h1>
                
                <div class="status">
                    <h3>✅ Dashboard is Running!</h3>
                    <p>Your Fantasy Hockey Dashboard is successfully deployed and running.</p>
                </div>
                
                <div class="info">
                    <h3>📊 Features Available</h3>
                    <ul>
                        <li>ESPN Fantasy Hockey integration</li>
                        <li>OpenAI-powered player analysis</li>
                        <li>Player swap recommendations</li>
                        <li>Real-time fantasy points tracking</li>
                        <li>Historical performance analysis</li>
                    </ul>
                </div>
                
                <div class="info">
                    <h3>🔧 Setup Required</h3>
                    <p>To use the full dashboard features, you need to:</p>
                    <ol>
                        <li>Set up your ESPN credentials in Netlify environment variables</li>
                        <li>Add your OpenAI API key</li>
                        <li>Configure your league settings</li>
                    </ol>
                    <p>See the <a href="https://github.com/ryanfadden/fantasy-hockey-dashboard" target="_blank">GitHub repository</a> for detailed setup instructions.</p>
                </div>
                
                <div class="github-link">
                    <p>🔗 <a href="https://github.com/ryanfadden/fantasy-hockey-dashboard" target="_blank">View on GitHub</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/html',
            },
            'body': html_content
        }
        
    except Exception as e:
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Fantasy Hockey Dashboard - Error</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .error {{ background: #ffe6e6; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🏒 Fantasy Hockey Dashboard</h1>
                <div class="error">
                    <h3>❌ Setup Required</h3>
                    <p>Error: {str(e)}</p>
                    <p>Please check the setup instructions in the GitHub repository.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/html',
            },
            'body': error_html
        }
