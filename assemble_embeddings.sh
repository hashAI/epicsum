#!/bin/bash

# Reassemble large files from chunks

echo "=================================================="
echo "Reassembling Large Files from Chunks"
echo "=================================================="
echo ""

# Check if chunks directory exists
if [ ! -d "embeddings_chunks" ]; then
    echo "❌ Error: embeddings_chunks/ directory not found"
    echo ""
    echo "Please run setup.sh to generate files, or ensure chunks are present."
    exit 1
fi

# Reassemble embeddings.npy
if [ ! -f "embeddings.npy" ]; then
    if ls embeddings_chunks/embeddings.npy.part_* 1> /dev/null 2>&1; then
        echo "Reassembling embeddings.npy..."
        cat embeddings_chunks/embeddings.npy.part_* > embeddings.npy
        
        # Verify checksum if available
        if [ -f "embeddings_chunks/embeddings.npy.sha256" ]; then
            echo "Verifying checksum..."
            if shasum -a 256 -c embeddings_chunks/embeddings.npy.sha256; then
                echo "✓ Checksum verified"
            else
                echo "⚠️  Checksum mismatch - file may be corrupted"
            fi
        fi
        
        echo "✓ embeddings.npy assembled ($(du -h embeddings.npy | cut -f1))"
    else
        echo "⚠️  No embeddings.npy chunks found"
    fi
else
    echo "✓ embeddings.npy already exists"
fi
echo ""

# Reassemble unified_media_database.json
if [ ! -f "unified_media_database.json" ]; then
    if ls embeddings_chunks/database.json.part_* 1> /dev/null 2>&1; then
        echo "Reassembling unified_media_database.json..."
        cat embeddings_chunks/database.json.part_* > unified_media_database.json
        
        # Verify checksum if available
        if [ -f "embeddings_chunks/database.json.sha256" ]; then
            echo "Verifying checksum..."
            if shasum -a 256 -c embeddings_chunks/database.json.sha256; then
                echo "✓ Checksum verified"
            else
                echo "⚠️  Checksum mismatch - file may be corrupted"
            fi
        fi
        
        echo "✓ unified_media_database.json assembled ($(du -h unified_media_database.json | cut -f1))"
    else
        echo "⚠️  No database.json chunks found"
    fi
else
    echo "✓ unified_media_database.json already exists"
fi
echo ""

# Check embeddings_index.json (should already exist at root)
if [ -f "embeddings_index.json" ]; then
    echo "✓ embeddings_index.json found at root ($(du -h embeddings_index.json | cut -f1))"
else
    echo "⚠️  embeddings_index.json not found!"
    echo "    This file should be committed directly to git at root level."
    echo "    If missing, run: ./setup.sh"
fi
echo ""

echo "=================================================="
echo "✓ Assembly Complete!"
echo "=================================================="
echo ""

