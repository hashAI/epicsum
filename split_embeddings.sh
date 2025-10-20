#!/bin/bash

# Split large files into chunks under 100MB for Git

echo "=================================================="
echo "Splitting Large Files into Git-Friendly Chunks"
echo "=================================================="
echo ""

CHUNK_SIZE="95M"  # 95MB per chunk (safely under 100MB limit)

# Create chunks directory
mkdir -p embeddings_chunks

# Split embeddings.npy (808 MB -> ~9 chunks)
if [ -f "embeddings.npy" ]; then
    echo "Splitting embeddings.npy..."
    split -b $CHUNK_SIZE embeddings.npy embeddings_chunks/embeddings.npy.part_
    echo "✓ Created $(ls embeddings_chunks/embeddings.npy.part_* | wc -l) chunks"
    
    # Create checksum
    shasum -a 256 embeddings.npy > embeddings_chunks/embeddings.npy.sha256
    echo "✓ Created checksum"
else
    echo "⚠️  embeddings.npy not found"
fi
echo ""

# Split unified_media_database.json (442 MB -> ~5 chunks)
if [ -f "unified_media_database.json" ]; then
    echo "Splitting unified_media_database.json..."
    split -b $CHUNK_SIZE unified_media_database.json embeddings_chunks/database.json.part_
    echo "✓ Created $(ls embeddings_chunks/database.json.part_* | wc -l) chunks"
    
    # Create checksum
    shasum -a 256 unified_media_database.json > embeddings_chunks/database.json.sha256
    echo "✓ Created checksum"
else
    echo "⚠️  unified_media_database.json not found"
fi
echo ""

# Note: embeddings_index.json (7.3 MB) stays at root level
# It's small enough to commit directly to git (no chunking needed)
echo "✓ embeddings_index.json (7.3 MB) - committed directly to git (no chunking needed)"
echo ""

# Show results
echo "=================================================="
echo "✓ Splitting Complete!"
echo "=================================================="
echo ""
echo "Chunk directory: embeddings_chunks/"
ls -lh embeddings_chunks/ | tail -n +2
echo ""
echo "Next steps:"
echo "  1. git add embeddings_chunks/ embeddings_index.json"
echo "  2. git commit -m 'Add embeddings in chunks'"
echo ""
echo "Note: embeddings_index.json is committed at root (not chunked)"
echo ""

