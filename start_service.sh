#!/bin/bash

# EpicSum Media Service Startup Script

echo "=================================================="
echo "     EpicSum Media Service Startup"
echo "=================================================="
echo ""

# Check if database exists
if [ ! -f "unified_media_database.json" ]; then
    echo "⚠️  Database not found. Creating unified database..."
    python3 create_unified_database.py
    echo ""
fi

# Kill any existing process on port 8082
echo "🔍 Checking for existing processes on port 8082..."
lsof -ti:8082 | xargs kill -9 2>/dev/null && echo "✓ Killed existing process" || echo "✓ No existing process found"
echo ""

# Start the service
echo "🚀 Starting EpicSum Media Service on port 8082..."
echo ""
python3 media_service.py

