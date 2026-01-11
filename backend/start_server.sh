#!/bin/bash
# CBSE Study App - Backend Server Startup Script
# For Amazon Linux / Ubuntu / any Linux with Python 3.10+

set -e

echo "🚀 Starting CBSE Study App Backend..."

# Navigate to backend directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   Copy .env.example to .env and add your GEMINI_API_KEY"
    exit 1
fi

# Start the server
echo "✅ Starting Uvicorn server on http://0.0.0.0:8000"
echo "   Press Ctrl+C to stop"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
