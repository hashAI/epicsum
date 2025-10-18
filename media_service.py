#!/usr/bin/env python3
"""
FastAPI service for serving images and videos based on search descriptions.
Optimized with FAISS vector search for ultra-fast semantic matching.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
import faiss
from sentence_transformers import SentenceTransformer
import uvicorn
import time


app = FastAPI(
    title="EpicSum Media Service",
    description="API for retrieving images and videos based on descriptions",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
MEDIA_DATABASE: List[Dict[str, Any]] = []
EMBEDDINGS: np.ndarray = None
FAISS_INDEX: faiss.Index = None
SENTENCE_MODEL: SentenceTransformer = None
INDEX_DATA: Dict[str, Any] = {}


def load_database(db_path: str = "unified_media_database.json"):
    """Load the unified media database."""
    global MEDIA_DATABASE
    try:
        print(f"Loading database from {db_path}...")
        start_time = time.time()
        with open(db_path, 'r', encoding='utf-8') as f:
            MEDIA_DATABASE = json.load(f)
        elapsed = time.time() - start_time
        print(f"✓ Loaded {len(MEDIA_DATABASE)} media items in {elapsed:.2f}s")
        
        # Count by type
        images = sum(1 for item in MEDIA_DATABASE if item['content_type'] == 'image')
        videos = sum(1 for item in MEDIA_DATABASE if item['content_type'] == 'video')
        print(f"  - Images: {images}")
        print(f"  - Videos: {videos}")
    except Exception as e:
        print(f"Error loading database: {e}")
        MEDIA_DATABASE = []


def load_embeddings_and_index(
    embeddings_path: str = "embeddings.npy",
    index_path: str = "embeddings_index.json"
):
    """Load pre-computed embeddings and create FAISS index."""
    global EMBEDDINGS, FAISS_INDEX, INDEX_DATA
    
    try:
        # Load embeddings
        print(f"\nLoading embeddings from {embeddings_path}...")
        start_time = time.time()
        EMBEDDINGS = np.load(embeddings_path)
        elapsed = time.time() - start_time
        print(f"✓ Loaded embeddings in {elapsed:.2f}s")
        print(f"  - Shape: {EMBEDDINGS.shape}")
        print(f"  - Size: {EMBEDDINGS.nbytes / (1024**2):.1f} MB")
        
        # Load index data
        print(f"Loading index data from {index_path}...")
        with open(index_path, 'r') as f:
            INDEX_DATA = json.load(f)
        print(f"✓ Loaded index data")
        
        # Create FAISS index
        print(f"\nCreating FAISS index...")
        start_time = time.time()
        embedding_dim = EMBEDDINGS.shape[1]
        
        # Use IndexFlatIP for inner product (cosine similarity with normalized vectors)
        FAISS_INDEX = faiss.IndexFlatIP(embedding_dim)
        FAISS_INDEX.add(EMBEDDINGS)
        
        elapsed = time.time() - start_time
        print(f"✓ Created FAISS index in {elapsed:.2f}s")
        print(f"  - Total vectors: {FAISS_INDEX.ntotal}")
        print(f"  - Dimension: {embedding_dim}")
        
    except Exception as e:
        print(f"Error loading embeddings: {e}")
        raise


def load_sentence_model(model_name: str = "all-MiniLM-L6-v2"):
    """Load the sentence transformer model."""
    global SENTENCE_MODEL
    
    try:
        print(f"\nLoading sentence model '{model_name}'...")
        start_time = time.time()
        SENTENCE_MODEL = SentenceTransformer(model_name)
        elapsed = time.time() - start_time
        print(f"✓ Loaded model in {elapsed:.2f}s")
    except Exception as e:
        print(f"Error loading model: {e}")
        raise


def search_media_fast(
    query: str,
    content_type: str,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Fast semantic search using FAISS and pre-computed embeddings.
    
    Args:
        query: Search query string
        content_type: Type of content ('image' or 'video')
        limit: Maximum number of results to return
        
    Returns:
        List of matching media items sorted by relevance
    """
    if not MEDIA_DATABASE or FAISS_INDEX is None or SENTENCE_MODEL is None:
        return []
    
    # Get indices for the specified content type
    content_indices = INDEX_DATA.get('content_type_index', {}).get(content_type, [])
    if not content_indices:
        return []
    
    # Encode the query
    query_embedding = SENTENCE_MODEL.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True
    )
    
    # Search using FAISS (much faster than linear search)
    # We search for more results to account for content type filtering
    k = min(len(content_indices) * 2, len(MEDIA_DATABASE))
    distances, indices = FAISS_INDEX.search(query_embedding, k)
    
    # Filter results by content type and get top matches
    results = []
    for idx, distance in zip(indices[0], distances[0]):
        if int(idx) in content_indices:
            results.append(MEDIA_DATABASE[int(idx)])
            if len(results) >= limit:
                break
    
    # If we didn't get enough results, fall back to all items of that type
    if not results:
        results = [MEDIA_DATABASE[i] for i in content_indices[:limit]]
    
    return results


@app.on_event("startup")
async def startup_event():
    """Load database, embeddings, and model on startup."""
    print("=" * 60)
    print("EpicSum Media Service - Starting Up")
    print("=" * 60)
    
    load_database()
    load_embeddings_and_index()
    load_sentence_model()
    
    print("\n" + "=" * 60)
    print("✓ Service ready!")
    print("=" * 60)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "EpicSum Media Service",
        "version": "2.0.0",
        "optimization": "FAISS + Sentence Transformers",
        "endpoints": {
            "images": "/epicsum/media/image/{description}",
            "videos": "/epicsum/media/video/{description}",
            "with_index": "/epicsum/media/image/{description}___<index>"
        },
        "database_stats": {
            "total_items": len(MEDIA_DATABASE),
            "images": sum(1 for item in MEDIA_DATABASE if item['content_type'] == 'image'),
            "videos": sum(1 for item in MEDIA_DATABASE if item['content_type'] == 'video'),
            "embeddings_loaded": EMBEDDINGS is not None,
            "faiss_index_ready": FAISS_INDEX is not None
        }
    }


@app.get("/epicsum/media/image/{description:path}")
async def get_image(description: str, redirect: bool = Query(True)):
    """
    Get image(s) based on description using fast semantic search.
    
    Format: /epicsum/media/image/tshirt-having-collar
    With index: /epicsum/media/image/tshirt-having-collar___2
    With redirect: /epicsum/media/image/tshirt-having-collar?redirect=true
    
    Args:
        description: Image description (can include ___<index> at the end)
        redirect: If true, redirects to the actual image link instead of returning JSON
        
    Returns:
        Matching image details or redirect to image URL
    """
    # Parse description and optional index
    index = 0
    if '___' in description:
        parts = description.split('___')
        description = parts[0]
        try:
            index = int(parts[1])
        except (ValueError, IndexError):
            index = 0
    
    # Search for matching images using FAISS
    results = search_media_fast(description, 'image', limit=100)
    
    # If no results, fallback to all images of this type
    if not results:
        results = [item for item in MEDIA_DATABASE if item['content_type'] == 'image']
        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"No images available in database"
            )
    
    # Apply modulus to index
    final_index = index % len(results)
    selected_image = results[final_index]
    
    # If redirect is true, redirect to the actual image link
    if redirect:
        return RedirectResponse(url=selected_image['link'], status_code=302)
    
    return {
        "success": True,
        "query": description,
        "requested_index": index,
        "actual_index": final_index,
        "total_matches": len(results),
        "result": selected_image
    }


@app.get("/epicsum/media/video/{description:path}")
async def get_video(description: str, redirect: bool = Query(True)):
    """
    Get video(s) based on description using fast semantic search.
    
    Format: /epicsum/media/video/yellow-flower-blooming
    With index: /epicsum/media/video/yellow-flower-blooming___2
    With redirect: /epicsum/media/video/yellow-flower-blooming?redirect=true
    
    Args:
        description: Video description (can include ___<index> at the end)
        redirect: If true, redirects to the actual video link instead of returning JSON
        
    Returns:
        Matching video details or redirect to video URL
    """
    # Parse description and optional index
    index = 0
    if '___' in description:
        parts = description.split('___')
        description = parts[0]
        try:
            index = int(parts[1])
        except (ValueError, IndexError):
            index = 0
    
    # Search for matching videos using FAISS
    results = search_media_fast(description, 'video', limit=100)
    
    # If no results, fallback to all videos of this type
    if not results:
        results = [item for item in MEDIA_DATABASE if item['content_type'] == 'video']
        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"No videos available in database"
            )
    
    # Apply modulus to index
    final_index = index % len(results)
    selected_video = results[final_index]
    
    # If redirect is true, redirect to the actual video link
    if redirect:
        return RedirectResponse(url=selected_video['link'], status_code=302)
    
    return {
        "success": True,
        "query": description,
        "requested_index": index,
        "actual_index": final_index,
        "total_matches": len(results),
        "result": selected_video
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database_loaded": len(MEDIA_DATABASE) > 0,
        "total_items": len(MEDIA_DATABASE),
        "embeddings_loaded": EMBEDDINGS is not None,
        "faiss_ready": FAISS_INDEX is not None,
        "model_loaded": SENTENCE_MODEL is not None
    }


if __name__ == "__main__":
    uvicorn.run(
        "media_service:app",
        host="0.0.0.0",
        port=8082,
        reload=True
    )
