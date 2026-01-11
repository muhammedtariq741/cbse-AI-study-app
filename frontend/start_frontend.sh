#!/bin/bash
# CBSE Study App - Frontend Server Startup Script
# For Amazon Linux / Ubuntu / any Linux with Node.js 18+

set -e

echo "🚀 Starting CBSE Study App Frontend..."

# Navigate to frontend directory
cd "$(dirname "$0")"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Build for production (optional - uncomment for production)
# echo "🔨 Building for production..."
# npm run build

# Start the server
echo "✅ Starting Next.js dev server on http://0.0.0.0:3000"
echo "   Press Ctrl+C to stop"
echo ""

# For development
npm run dev -- -H 0.0.0.0

# For production (uncomment these and comment above)
# npm run build
# npm start -- -H 0.0.0.0
