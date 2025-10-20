#!/bin/bash

# EpicSum Media Service - Start Script
# Just starts the service (no setup/generation)

echo "=================================================="
echo "     EpicSum Media Service"
echo "=================================================="
echo ""

# Auto-assemble chunks if needed
if [ ! -f "embeddings.npy" ] || [ ! -f "unified_media_database.json" ] || [ ! -f "embeddings_index.json" ]; then
    if [ -d "embeddings_chunks" ]; then
        echo "📦 Assembling files from chunks..."
        ./assemble_embeddings.sh
        echo ""
    else
        echo "❌ Error: Required files not found and no chunks available"
        echo ""
        echo "Please run setup first:"
        echo "  ./setup.sh"
        echo ""
        exit 1
    fi
fi

echo "✓ Database ready (unified_media_database.json)"
echo "✓ Embeddings ready (embeddings.npy)"
echo "✓ Index ready (embeddings_index.json)"
echo ""

# Kill any existing process on port 8082
echo "🔍 Checking for existing processes on port 8082..."
lsof -ti:8082 | xargs kill -9 2>/dev/null && echo "✓ Killed existing process" || echo "✓ No existing process found"
echo ""

# Start the service
echo "🚀 Starting EpicSum Media Service on port 8082..."
echo "   Loading embeddings and FAISS index (~30-40 seconds)..."
echo ""
python media_service.py
