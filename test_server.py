#!/usr/bin/env python3
"""
Simple test server for Railway deployment
"""
import os
from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Fantasy Hockey Dashboard - Test</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .status { background: #e8f5e8; border: 1px solid #4caf50; padding: 15px; border-radius: 5px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏒 Fantasy Hockey Dashboard</h1>
            <div class="status">
                <h3>✅ Railway Deployment Successful!</h3>
                <p>Your Fantasy Hockey Dashboard is now running on Railway.</p>
                <p>Environment: {}</p>
                <p>Port: {}</p>
            </div>
            <p>Next step: Set up your environment variables in Railway dashboard.</p>
        </div>
    </body>
    </html>
    '''.format(os.environ.get('RAILWAY_ENVIRONMENT', 'production'), os.environ.get('PORT', '8080'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
