# EpicSum Media Service

**Lorem Ipsum for images and videos with semantic search.**

A FastAPI service that returns relevant media (images/videos) based on text descriptions. Perfect for prototyping, mockups, and development when you need placeholder content that actually matches your context.

## Database Stats

- **1,103,270** total media items
- **1,103,170** product images (Amazon)
- **100** videos (Pixabay)

---

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate Database

```bash
python3 create_unified_database.py
```

This creates `unified_media_database.json` (~442 MB) from:
- 140 CSV files in `product-images-dataset/`
- Video metadata in `video-dataset/metadata.json`

---

## Running the Service

### Start Server

```bash
./start_service.sh
```

Or manually:

```bash
python3 media_service.py
```

Service runs on: **http://localhost:8082**

---

## API Specification

### Base URL
```
http://localhost:8082
```

### Endpoints

#### 1. Get Image
```
GET /epicsum/media/image/{description}
```

**Parameters:**
- `description` (path): Search query (words separated by `-` or `_`)
- `redirect` (query): Boolean, default `true`
  - `true`: Redirects to image URL (302)
  - `false`: Returns JSON response

**With Index:**
```
GET /epicsum/media/image/{description}___<index>
```
- Index uses modulus: `index % total_results`

**Examples:**
```bash
# Redirect to image (default)
curl "http://localhost:8082/epicsum/media/image/tshirt-collar"

# Get JSON response
curl "http://localhost:8082/epicsum/media/image/tshirt-collar?redirect=false"

# Get specific result (3rd match)
curl "http://localhost:8082/epicsum/media/image/blue-jeans___2"

# Large index with modulus (150 % 100 = 50)
curl "http://localhost:8082/epicsum/media/image/watch___150"
```

#### 2. Get Video
```
GET /epicsum/media/video/{description}
```

Same parameters and behavior as images.

**Examples:**
```bash
# Redirect to video
curl "http://localhost:8082/epicsum/media/video/flower-blooming"

# Get JSON response
curl "http://localhost:8082/epicsum/media/video/sunset-city?redirect=false"

# Get 2nd match
curl "http://localhost:8082/epicsum/media/video/flower___1"
```

#### 3. Service Info
```
GET /
```

Returns service information and database stats.

#### 4. Health Check
```
GET /health
```

Returns service health status.

---

## Response Format

### JSON Response (redirect=false)

```json
{
  "success": true,
  "query": "tshirt-collar",
  "requested_index": 0,
  "actual_index": 0,
  "total_matches": 100,
  "result": {
    "content_type": "image",
    "title": "Product Name",
    "description": "Product Description",
    "link": "https://m.media-amazon.com/images/...",
    "meta": {
      "category": "clothing",
      "sub_category": "T-shirts"
    }
  }
}
```

### Redirect Response (redirect=true, default)

HTTP 302 redirect to the media URL.

---

## Search Algorithm

### Text Normalization
1. Convert to lowercase
2. Replace `-` and `_` with spaces
3. Remove extra whitespace

### Similarity Scoring

**Word Overlap (70% weight):**
```
score = (matching_words / query_words)
```

**Sequence Similarity (30% weight):**
```
score = SequenceMatcher(query, target).ratio()
```

**Final Score:**
```
combined_score = (word_overlap * 0.7) + (sequence_similarity * 0.3)
```

### Search Fields

**Images:**
- Title
- Description
- Category (0.5x weight)
- Sub-category (0.5x weight)

**Videos:**
- Title
- Description

### Result Handling

- Returns top 100 matches sorted by relevance
- If no matches found: falls back to all items of that type
- Index selection: `results[index % len(results)]`

---

## Database Format

### Image Entry
```json
{
  "content_type": "image",
  "title": "Product Name",
  "description": "Product Name",
  "link": "https://m.media-amazon.com/images/...",
  "meta": {
    "category": "main_category",
    "sub_category": "sub_category"
  }
}
```

### Video Entry
```json
{
  "content_type": "video",
  "title": "Video keywords",
  "description": "Video description",
  "link": "http://194.238.23.194/epicsum/videos/filename.mp4",
  "meta": {}
}
```

---

## Configuration

### Change Port

Edit `media_service.py`:
```python
uvicorn.run("media_service:app", host="0.0.0.0", port=YOUR_PORT, reload=True)
```

### Change Video Base URL

Edit `create_unified_database.py`:
```python
VIDEO_BASE_URL = "http://your-server.com/path/"
```

---

## Files

| File | Description |
|------|-------------|
| `media_service.py` | FastAPI service (main) |
| `create_unified_database.py` | Database generator |
| `unified_media_database.json` | Main database (gitignored) |
| `start_service.sh` | Service launcher script |
| `requirements.txt` | Python dependencies |

---

## Use Cases

**Development & Prototyping:**
- Need a "blue t-shirt" image for your e-commerce mockup? → Get a relevant product image
- Building a video gallery? → Search "sunset city" and get matching videos
- Testing UI with realistic content? → Semantic search finds contextually appropriate media

**Like Lorem Ipsum, but smart:**
- Lorem Ipsum gives you text → EpicSum gives you images/videos
- Lorem Ipsum is random → EpicSum matches your description
- Lorem Ipsum is Latin → EpicSum understands English queries

## Notes

- Default behavior: redirects directly to media URL
- No 404 errors: always returns a result (graceful fallback)
- Duplicates exist: same product may appear with different categories (better search coverage)
- Database loads once on startup (~1-2 seconds)

---

## Examples

```bash
# Start service
./start_service.sh

# Search for t-shirt (redirects to image)
curl "http://localhost:8082/epicsum/media/image/tshirt"

# Search for watch, get 5th result
curl "http://localhost:8082/epicsum/media/image/watch___4"

# Search for flower video (get JSON)
curl "http://localhost:8082/epicsum/media/video/flower?redirect=false"

# Check health
curl "http://localhost:8082/health"
```
