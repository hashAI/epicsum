#!/usr/bin/env python3
"""
Script to create a unified database for both product images and videos.
"""

import csv
import json
import re
from pathlib import Path
from urllib.parse import quote


def clean_image_url(url):
    """
    Clean malformed Amazon image URLs.
    
    Removes the /W/IMAGERENDERING_XXXXXX-TX/images pattern from URLs.
    Example:
        https://m.media-amazon.com/images/W/IMAGERENDERING_521856-T2/images/I/71cv73eEBWL._AC_UL320_.jpg
        -> https://m.media-amazon.com/images/I/71cv73eEBWL._AC_UL320_.jpg
    
    Args:
        url: Original image URL
        
    Returns:
        Cleaned URL
    """
    if not url:
        return url
    
    # Pattern to match: /W/IMAGERENDERING_XXXXXX-TX/images
    pattern = r'/W/IMAGERENDERING_[^/]+-[^/]+/images'
    cleaned_url = re.sub(pattern, '', url)
    
    return cleaned_url


def process_product_images(csv_dir):
    """
    Process product image CSV files and convert to unified format.
    
    Returns:
        List of image entries in unified format
    """
    images = []
    csv_dir_path = Path(csv_dir)
    csv_files = sorted(csv_dir_path.glob('*.csv'))
    
    print(f"Processing {len(csv_files)} product image CSV files...")
    
    for csv_file in csv_files:
        print(f"  Processing: {csv_file.name}")
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    name = row.get('name', '').strip()
                    main_category = row.get('main_category', '').strip()
                    sub_category = row.get('sub_category', '').strip()
                    image_url = row.get('image', '').strip()
                    
                    if name and image_url:  # Only include if we have name and image
                        # Clean the image URL to fix malformed Amazon URLs
                        cleaned_url = clean_image_url(image_url)
                        
                        entry = {
                            'content_type': 'image',
                            'title': name,
                            'description': name,
                            'link': cleaned_url,
                            'meta': {
                                'category': main_category,
                                'sub_category': sub_category
                            }
                        }
                        images.append(entry)
                        
        except Exception as e:
            print(f"    Error processing {csv_file.name}: {e}")
            continue
    
    return images


def process_videos(metadata_file, base_url):
    """
    Process video metadata and convert to unified format.
    
    Args:
        metadata_file: Path to video metadata JSON file
        base_url: Base URL for video files (e.g., http://194.238.23.194/epicsum/)
        
    Returns:
        List of video entries in unified format
    """
    videos = []
    
    print(f"\nProcessing video metadata...")
    
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        for item in metadata:
            text = item.get('text', '').strip()
            handwritten_description = item.get('handwritten_description', '').strip()
            file_name = item.get('file_name', '').strip()
            
            if file_name and handwritten_description:
                # Extract just the filename from the path (e.g., "videos/file.mp4" -> "file.mp4")
                video_filename = file_name.split('/')[-1]
                # URL encode the filename for the link
                encoded_filename = quote(video_filename)
                video_link = f"{base_url}{encoded_filename}"
                
                entry = {
                    'content_type': 'video',
                    'title': text if text else handwritten_description,
                    'description': handwritten_description,
                    'link': video_link,
                    'meta': {}
                }
                videos.append(entry)
                
    except Exception as e:
        print(f"  Error processing video metadata: {e}")
    
    return videos


def create_unified_database(
    csv_dir, 
    video_metadata_file, 
    video_base_url,
    output_file
):
    """
    Create unified database combining images and videos.
    """
    print("=" * 60)
    print("Creating Unified Media Database")
    print("=" * 60)
    
    # Process images
    images = process_product_images(csv_dir)
    print(f"✓ Processed {len(images)} product images")
    
    # Process videos
    videos = process_videos(video_metadata_file, video_base_url)
    print(f"✓ Processed {len(videos)} videos")
    
    # Combine all media
    all_media = images + videos
    
    print(f"\n{'=' * 60}")
    print(f"Total media items: {len(all_media)}")
    print(f"  - Images: {len(images)}")
    print(f"  - Videos: {len(videos)}")
    print(f"{'=' * 60}")
    
    # Write to JSON file
    print(f"\nWriting to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_media, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Successfully created {output_file}")
    
    return len(images), len(videos)


if __name__ == "__main__":
    # Configuration
    CSV_DIRECTORY = "product-images-dataset"
    VIDEO_METADATA_FILE = "video-dataset/metadata.json"
    VIDEO_BASE_URL = "http://194.238.23.194/epicsum/videos/"
    OUTPUT_FILE = "unified_media_database.json"
    
    # Create unified database
    create_unified_database(
        CSV_DIRECTORY,
        VIDEO_METADATA_FILE,
        VIDEO_BASE_URL,
        OUTPUT_FILE
    )

