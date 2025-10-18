#!/usr/bin/env python3
"""
FastAPI service for serving images and videos based on search descriptions.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import re
from difflib import SequenceMatcher
import uvicorn


app = FastAPI(
    title="EpicSum Media Service",
    description="API for retrieving images and videos based on descriptions",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global database
MEDIA_DATABASE: List[Dict[str, Any]] = []


def load_database(db_path: str = "unified_media_database.json"):
    """Load the unified media database."""
    global MEDIA_DATABASE
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            MEDIA_DATABASE = json.load(f)
        print(f"✓ Loaded {len(MEDIA_DATABASE)} media items")
        
        # Count by type
        images = sum(1 for item in MEDIA_DATABASE if item['content_type'] == 'image')
        videos = sum(1 for item in MEDIA_DATABASE if item['content_type'] == 'video')
        print(f"  - Images: {images}")
        print(f"  - Videos: {videos}")
    except Exception as e:
        print(f"Error loading database: {e}")
        MEDIA_DATABASE = []


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    # Convert to lowercase and replace hyphens with spaces
    text = text.lower().replace('-', ' ').replace('_', ' ')
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text


def calculate_similarity(query: str, target: str) -> float:
    """
    Calculate similarity score between query and target text.
    Uses a combination of substring matching and sequence matching.
    """
    query_norm = normalize_text(query)
    target_norm = normalize_text(target)
    
    # Check for exact substring match
    if query_norm in target_norm:
        return 1.0
    
    # Split into words for word-level matching
    query_words = set(query_norm.split())
    target_words = set(target_norm.split())
    
    if not query_words:
        return 0.0
    
    # Calculate word overlap score
    common_words = query_words & target_words
    word_overlap_score = len(common_words) / len(query_words)
    
    # Calculate sequence similarity score
    sequence_score = SequenceMatcher(None, query_norm, target_norm).ratio()
    
    # Combine scores (weighted average)
    combined_score = (word_overlap_score * 0.7) + (sequence_score * 0.3)
    
    return combined_score


def search_media(
    query: str, 
    content_type: str, 
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Search for media items matching the query.
    
    Args:
        query: Search query string
        content_type: Type of content ('image' or 'video')
        limit: Maximum number of results to return
        
    Returns:
        List of matching media items sorted by relevance
    """
    if not MEDIA_DATABASE:
        return []
    
    # Filter by content type
    filtered_items = [
        item for item in MEDIA_DATABASE 
        if item['content_type'] == content_type
    ]
    
    if not filtered_items:
        return []
    
    # Calculate similarity scores
    scored_items = []
    for item in filtered_items:
        # Search in both title and description
        title_score = calculate_similarity(query, item.get('title', ''))
        desc_score = calculate_similarity(query, item.get('description', ''))
        
        # Also search in category/subcategory for images
        meta_score = 0.0
        if content_type == 'image' and item.get('meta'):
            category = item['meta'].get('category', '')
            sub_category = item['meta'].get('sub_category', '')
            meta_score = max(
                calculate_similarity(query, category),
                calculate_similarity(query, sub_category)
            ) * 0.5  # Lower weight for category matches
        
        # Use the best score
        best_score = max(title_score, desc_score, meta_score)
        
        if best_score > 0:
            scored_items.append((best_score, item))
    
    # Sort by score (descending) and limit results
    scored_items.sort(key=lambda x: x[0], reverse=True)
    results = [item for score, item in scored_items[:limit]]
    
    return results


@app.on_event("startup")
async def startup_event():
    """Load database on startup."""
    load_database()


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "EpicSum Media Service",
        "version": "1.0.0",
        "endpoints": {
            "images": "/epicsum/media/image/{description}",
            "videos": "/epicsum/media/video/{description}",
            "with_index": "/epicsum/media/image/{description}___<index>"
        },
        "database_stats": {
            "total_items": len(MEDIA_DATABASE),
            "images": sum(1 for item in MEDIA_DATABASE if item['content_type'] == 'image'),
            "videos": sum(1 for item in MEDIA_DATABASE if item['content_type'] == 'video')
        }
    }


@app.get("/epicsum/media/image/{description:path}")
async def get_image(description: str, redirect: bool = Query(True)):
    """
    Get image(s) based on description.
    
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
    
    # Search for matching images
    results = search_media(description, 'image', limit=100)
    
    # If no results, fallback to all images of this type
    if not results:
        results = [item for item in MEDIA_DATABASE if item['content_type'] == 'image']
        if not results:
            # Ultimate fallback - shouldn't happen but just in case
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
    Get video(s) based on description.
    
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
    
    # Search for matching videos
    results = search_media(description, 'video', limit=100)
    
    # If no results, fallback to all videos of this type
    if not results:
        results = [item for item in MEDIA_DATABASE if item['content_type'] == 'video']
        if not results:
            # Ultimate fallback - shouldn't happen but just in case
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
        "total_items": len(MEDIA_DATABASE)
    }


if __name__ == "__main__":
    uvicorn.run(
        "media_service:app",
        host="0.0.0.0",
        port=8082,
        reload=True
    )

