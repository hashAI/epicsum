#!/usr/bin/env python3
"""
Script to generate embeddings for all media items in the database.
This enables fast semantic search using FAISS.
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
import time


def load_database(db_path: str = "unified_media_database.json"):
    """Load the unified media database."""
    print(f"Loading database from {db_path}...")
    with open(db_path, 'r', encoding='utf-8') as f:
        database = json.load(f)
    print(f"✓ Loaded {len(database)} media items")
    return database


def create_searchable_text(item: dict) -> str:
    """
    Create searchable text from a media item.
    Combines title, description, and metadata into a single string.
    """
    parts = []
    
    # Add title
    if item.get('title'):
        parts.append(item['title'])
    
    # Add description
    if item.get('description'):
        parts.append(item['description'])
    
    # Add category metadata for images
    if item.get('meta'):
        if item['meta'].get('category'):
            parts.append(item['meta']['category'])
        if item['meta'].get('sub_category'):
            parts.append(item['meta']['sub_category'])
    
    return ' '.join(parts)


def generate_embeddings(
    database: list,
    model_name: str = 'all-MiniLM-L6-v2',
    batch_size: int = 512,
    output_embeddings: str = 'embeddings.npy',
    output_index: str = 'embeddings_index.json'
):
    """
    Generate embeddings for all media items.
    
    Args:
        database: List of media items
        model_name: Sentence transformer model to use
        batch_size: Batch size for encoding
        output_embeddings: Output file for embeddings (numpy array)
        output_index: Output file for index mapping
    """
    print(f"\n{'=' * 60}")
    print(f"Generating Embeddings")
    print(f"{'=' * 60}")
    print(f"Model: {model_name}")
    print(f"Items: {len(database)}")
    print(f"Batch size: {batch_size}")
    
    # Load the model
    print(f"\nLoading model '{model_name}'...")
    start_time = time.time()
    model = SentenceTransformer(model_name)
    print(f"✓ Model loaded in {time.time() - start_time:.2f}s")
    
    # Create searchable text for all items
    print("\nCreating searchable text for all items...")
    texts = [create_searchable_text(item) for item in database]
    print(f"✓ Created {len(texts)} text entries")
    
    # Generate embeddings
    print(f"\nGenerating embeddings (batch_size={batch_size})...")
    start_time = time.time()
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True  # L2 normalize for cosine similarity
    )
    elapsed_time = time.time() - start_time
    print(f"✓ Generated embeddings in {elapsed_time:.2f}s")
    print(f"  - Speed: {len(texts) / elapsed_time:.0f} items/second")
    print(f"  - Shape: {embeddings.shape}")
    print(f"  - Dtype: {embeddings.dtype}")
    
    # Save embeddings
    print(f"\nSaving embeddings to {output_embeddings}...")
    np.save(output_embeddings, embeddings)
    file_size_mb = Path(output_embeddings).stat().st_size / (1024 * 1024)
    print(f"✓ Saved embeddings ({file_size_mb:.1f} MB)")
    
    # Create index mapping (for reference)
    index_data = {
        'total_items': len(database),
        'embedding_dim': embeddings.shape[1],
        'model_name': model_name,
        'content_type_index': {}
    }
    
    # Create content type index for faster filtering
    for idx, item in enumerate(database):
        content_type = item['content_type']
        if content_type not in index_data['content_type_index']:
            index_data['content_type_index'][content_type] = []
        index_data['content_type_index'][content_type].append(idx)
    
    print(f"Saving index to {output_index}...")
    with open(output_index, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2)
    print(f"✓ Saved index mapping")
    
    print(f"\n{'=' * 60}")
    print(f"Summary:")
    print(f"  - Total embeddings: {len(embeddings)}")
    print(f"  - Images: {len(index_data['content_type_index'].get('image', []))}")
    print(f"  - Videos: {len(index_data['content_type_index'].get('video', []))}")
    print(f"  - Embeddings file: {output_embeddings} ({file_size_mb:.1f} MB)")
    print(f"  - Index file: {output_index}")
    print(f"{'=' * 60}")
    
    return embeddings, index_data


if __name__ == "__main__":
    # Configuration
    DATABASE_FILE = "unified_media_database.json"
    EMBEDDINGS_OUTPUT = "embeddings.npy"
    INDEX_OUTPUT = "embeddings_index.json"
    MODEL_NAME = "all-MiniLM-L6-v2"  # Fast and efficient model (80MB)
    BATCH_SIZE = 512
    
    # Load database
    database = load_database(DATABASE_FILE)
    
    # Generate embeddings
    generate_embeddings(
        database=database,
        model_name=MODEL_NAME,
        batch_size=BATCH_SIZE,
        output_embeddings=EMBEDDINGS_OUTPUT,
        output_index=INDEX_OUTPUT
    )
    
    print("\n✓ Done! You can now use the embeddings with the media service.")

