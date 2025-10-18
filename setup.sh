#!/bin/bash

# EpicSum Media Service - One-Time Setup Script
# Run this once to generate database and embeddings

echo "=========================================================="
echo "     EpicSum Media Service - Initial Setup"
echo "=========================================================="
echo ""
echo "This script will:"
echo "  1. Generate unified database (~2-3 minutes)"
echo "  2. Generate embeddings (~15-20 minutes)"
echo ""
echo "⚠️  This only needs to be run ONCE"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled."
    exit 1
fi

echo ""
echo "=================================================="
echo "Step 1: Generating Unified Database"
echo "=================================================="
echo ""

if [ -f "unified_media_database.json" ]; then
    echo "⚠️  Database already exists!"
    read -p "Regenerate? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping database generation..."
    else
        python3 create_unified_database.py
    fi
else
    python3 create_unified_database.py
fi

echo ""
echo "=================================================="
echo "Step 2: Generating Embeddings"
echo "=================================================="
echo ""

if [ -f "embeddings.npy" ]; then
    echo "⚠️  Embeddings already exist!"
    read -p "Regenerate? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping embeddings generation..."
    else
        python3 generate_embeddings.py
    fi
else
    python3 generate_embeddings.py
fi

echo ""
echo "=========================================================="
echo "Step 3: Creating Chunks for Git"
echo "=========================================================="
echo ""

if [ -f "embeddings.npy" ] && [ -f "unified_media_database.json" ]; then
    echo "Creating chunks under 100MB for Git..."
    ./split_embeddings.sh
    echo ""
fi

echo "=========================================================="
echo "✅ Setup Complete!"
echo "=========================================================="
echo ""
echo "Generated files:"
echo "  • unified_media_database.json (~215 MB)"
echo "  • embeddings.npy (~808 MB)"
echo "  • embeddings_index.json (~7.3 MB)"
echo "  • embeddings_chunks/ (15 files, all <100MB)"
echo ""
echo "Next steps:"
echo "  1. Commit chunks to git:"
echo "     git add embeddings_chunks/"
echo "     git commit -m 'Update embeddings chunks'"
echo "     git push origin main"
echo ""
echo "  2. Start the service:"
echo "     ./start_service.sh"
echo ""

