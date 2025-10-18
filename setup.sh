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
echo "✅ Setup Complete!"
echo "=========================================================="
echo ""
echo "Generated files:"
echo "  • unified_media_database.json (~442 MB)"
echo "  • embeddings.npy (~808 MB)"
echo "  • embeddings_index.json (~7.3 MB)"
echo ""
echo "Next steps:"
echo "  1. Add files to Git LFS (if not already tracked):"
echo "     git lfs track '*.npy' '*.json'"
echo "     git add .gitattributes"
echo ""
echo "  2. Commit the files:"
echo "     git add embeddings.npy embeddings_index.json unified_media_database.json"
echo "     git commit -m 'Add pre-computed embeddings and database'"
echo ""
echo "  3. Start the service:"
echo "     ./start_service.sh"
echo ""

