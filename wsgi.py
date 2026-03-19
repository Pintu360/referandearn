# wsgi.py
from flask import Flask, jsonify
import os
import time
import psycopg2
from datetime import datetime

app = Flask(__name__)
start_time = time.time()

@app.route('/')
def home():
    return jsonify({
        "name": "Solana Tracker Bot",
        "status": "running",
        "version": "1.0.0",
        "uptime": f"{int(time.time() - start_time)} seconds",
        "docs": "/health"
    })

@app.route('/health')
def health():
    """Health check endpoint for Render"""
    try:
        # Test database connection
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            conn = psycopg2.connect(database_url)
            conn.close()
            db_status = "connected"
        else:
            db_status = "not configured"
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": int(time.time() - start_time),
            "database": db_status,
            "telegram_bot": os.getenv("TELEGRAM_BOT_TOKEN") is not None
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@app.route('/healthz')
def healthz():
    """Simple health check for load balancers"""
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)