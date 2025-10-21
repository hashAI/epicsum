# e-picsum: Contextually relevant Placeholder Images for your website development

**Lorem Ipsum for images and videos with ultra-fast semantic search.**

A FastAPI service that returns relevant media based on text descriptions. Perfect for prototyping and development when you need placeholder content that matches your context.

## 🚀 Performance

- **~250ms** average response time
- **551,685** items indexed with FAISS + Sentence Transformers
- **28x faster** than traditional text matching
- **0% broken URLs** (malformed Amazon CDN paths fixed)

---

## Quick Start

```bash
# 1. Clone and install
git clone <repo-url>
cd epicsum
pip install -r requirements.txt

# 2. Start service (auto-assembles embeddings on first run)
./start_service.sh
```

Service runs on: **http://localhost:8082**

**First run:** ~60 seconds (assembles chunks + loads embeddings)  
**Subsequent runs:** ~40 seconds (just loads embeddings)

---

## Usage Examples

```bash
# Get image (default: index=0, size=720, redirect=true)
curl "http://localhost:8082/epicsum/media/image/laptop"

# Get JSON response
curl "http://localhost:8082/epicsum/media/image/laptop?redirect=false"

# Get specific result by index
curl "http://localhost:8082/epicsum/media/image/laptop?index=2"

# Get specific size (160, 320, 480, 720, 1000, 1500)
curl "http://localhost:8082/epicsum/media/image/laptop?size=1500"

# Combine parameters
curl "http://localhost:8082/epicsum/media/image/laptop?index=3&size=480&redirect=false"

# Get video
curl "http://localhost:8082/epicsum/media/video/sunset?index=1"

# Health check
curl "http://localhost:8082/health"
```

---

## API Endpoints

### Get Image
```
GET /epicsum/media/image/{description}
```

**Query Parameters:**
- `index` (int, default: `0`) - Result index (0-based)
- `size` (int, default: `720`) - Image size in pixels (160, 320, 480, 720, 1000, 1500)
- `redirect` (bool, default: `true`) - Redirect to media URL or return JSON

**Examples:**
```bash
GET /epicsum/media/image/laptop                           # Default: index=0, size=720
GET /epicsum/media/image/laptop?index=2                   # Second result, 720px
GET /epicsum/media/image/laptop?size=1500                 # First result, 1500px
GET /epicsum/media/image/laptop?index=3&size=480          # Fourth result, 480px
GET /epicsum/media/image/laptop?redirect=false            # Return JSON
```

**Example Response (redirect=false):**
```json
{
  "success": true,
  "query": "laptop",
  "index": 0,
  "size": 720,
  "total_matches": 100,
  "result": {
    "content_type": "image",
    "title": "Lenovo IdeaPad Slim 3",
    "link": "https://m.media-amazon.com/images/I/xxxxx._AC_UL720_.jpg",
    "meta": {
      "category": "tv, audio & cameras",
      "sub_category": "All Electronics"
    }
  }
}
```

### Get Video
```
GET /epicsum/media/video/{description}
```

**Query Parameters:**
- `index` (int, default: `0`) - Result index (0-based)
- `redirect` (bool, default: `true`) - Redirect to video URL or return JSON

**Examples:**
```bash
GET /epicsum/media/video/sunset                           # Default: index=0
GET /epicsum/media/video/sunset?index=2                   # Third result
GET /epicsum/media/video/sunset?redirect=false            # Return JSON
```

---

## How It Works

### Semantic Search with FAISS
1. **Pre-computed embeddings:** All 551k items encoded as 384-dim vectors
2. **FAISS index:** Fast similarity search (O(log n))
3. **Query process:** Encode query → Search index → Return top matches

### File Structure
```
# Committed to git
embeddings_index.json       # 7.3 MB (at root - committed directly)
embeddings_chunks/          # Chunks <100MB
├── embeddings.npy.part_*   # 9 chunks (~95MB each, 808MB total)
├── database.json.part_*    # 3 chunks (~95MB each, 215MB total)
└── *.sha256                # Checksums for verification

# Auto-assembled files (gitignored)
embeddings.npy              # 808 MB (assembled from chunks)
unified_media_database.json # 215 MB (assembled from chunks)
```

### Why Chunks?
- Git doesn't allow files >100MB
- Only large files chunked: `embeddings.npy` (808MB), `unified_media_database.json` (215MB)
- `embeddings_index.json` (7.3MB) committed directly at root
- Chunks auto-assemble on first run
- No Git LFS needed

---

## Scripts

### `start_service.sh` - Start Service
```bash
./start_service.sh
```
- Auto-assembles chunks if needed (first run)
- Starts FastAPI service on port 8082

### `setup.sh` - Generate from Scratch
```bash
./setup.sh
```
- Generates database from CSV files (~3 min)
- Generates embeddings with sentence-transformers (~17 min)
- Auto-creates chunks for Git
- Only needed if: no chunks, dataset changed, or embeddings corrupted

### `split_embeddings.sh` - Create Chunks
```bash
./split_embeddings.sh
```
- Splits large files into <100MB chunks
- Run after regenerating embeddings
- Creates `embeddings_chunks/` directory

### `assemble_embeddings.sh` - Restore Files
```bash
./assemble_embeddings.sh
```
- Reassembles files from chunks
- Auto-run by `start_service.sh`
- Verifies checksums

---

## Development Workflow

### First Time Setup
```bash
git clone <repo-url>
pip install -r requirements.txt
./start_service.sh              # That's it!
```

### Daily Development
```bash
./start_service.sh              # Just start
# Make code changes
# Service auto-reloads (uvicorn --reload)
```

### After Dataset Changes
```bash
./setup.sh                      # Regenerate
./split_embeddings.sh           # Create new chunks
git add embeddings_chunks/
git commit -m "Update embeddings"
git push
```

---

## Database Stats

- **551,685** total items
- **551,585** product images (Amazon, 139 categories)
- **100** videos (Pixabay)
- **Search fields:** title, description, category, sub-category

---

## Technical Details

**Stack:**
- FastAPI + Uvicorn
- Sentence Transformers (all-MiniLM-L6-v2)
- FAISS (IndexFlatIP)
- NumPy

**Performance:**
- Query encoding: ~10ms
- FAISS search: ~50ms
- Network/JSON: ~190ms
- **Total: ~250ms**

**Memory:** ~1.5 GB (embeddings + FAISS index)

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
| `start_service.sh` | Start service (auto-assembles chunks) |
| `setup.sh` | Generate database + embeddings from scratch |
| `split_embeddings.sh` | Split large files into chunks |
| `assemble_embeddings.sh` | Reassemble files from chunks |
| `media_service.py` | FastAPI service with FAISS |
| `generate_embeddings.py` | Create vector embeddings |
| `create_unified_database.py` | Generate database from CSVs |
| `embeddings_chunks/` | Pre-split files <100MB (committed) |
| `product-images-dataset/` | 139 CSV files with product data |
| `video-dataset/` | Video metadata |

---

## Troubleshooting

**"Port 8082 already in use"**
- Script auto-kills existing process
- Or manually: `lsof -ti:8082 | xargs kill -9`

**"Files not found"**
- Run `./setup.sh` to generate from scratch
- Or ensure `embeddings_chunks/` directory exists

**"Checksum mismatch"**
```bash
git pull origin main          # Re-download chunks
./assemble_embeddings.sh      # Reassemble
```

**Slow first request**
- Normal! Model loads on first request (~5 seconds)
- Subsequent requests: ~250ms

---

## Notes

- **Default behavior:** Redirects to media URL
- **No 404 errors:** Always returns a result (graceful fallback)
- **Startup time:** 
  - First run: ~60 seconds (assembles chunks + loads embeddings)
  - Subsequent runs: ~40 seconds (just loads embeddings)
- **Clean URLs:** All malformed Amazon CDN URLs fixed automatically
- **Semantic search:** Understands context, not just keywords
- **Chunk size:** 15 files (~1 GB total), all under 100MB
- **No Git LFS required:** Uses standard Git
- **Dynamic image sizing:** Amazon CDN supports 160-1500px (default: 720px)
- **Query parameters:** Clean RESTful API with index & size params

---

## License & Credits

- **Product images:** Amazon product dataset
- **Videos:** Pixabay
- **Embeddings model:** sentence-transformers/all-MiniLM-L6-v2
