# Workflow & Usage Guide

## Complete Workflow

### Phase 1: Setup (One-time)

```
1. Get Google API Credentials
   ├─ API Key from Google Cloud Console
   └─ CX ID from Programmable Search Engine

2. Install Dependencies
   └─ pip install -r requirements.txt

3. Set Environment Variables
   ├─ GOOGLE_API_KEY=...
   └─ GOOGLE_CX=...
```

### Phase 2: Extract & Search (Repeatable)

```
Terminal 1: Backend Server
│
├─ python google_search_backend.py --port 5000
│  ├─ Loads GOOGLE_API_KEY from env
│  ├─ Loads GOOGLE_CX from env
│  ├─ Creates: downloaded_media/
│  ├─ Creates: search_cache/
│  └─ Ready on http://127.0.0.1:5000
│
└─ Server running... (keep this terminal open)

Terminal 2: Extract & Search
│
├─ Step 1: Extract Key Points
│  ├─ python run_key_point_extractor.py
│  ├─ Enter text → [Enter twice]
│  └─ Creates: extractor_output.json
│
├─ Step 2: Search (Web)
│  ├─ python key_point_search_tool.py \
│  │   --input extractor_output.json \
│  │   --backend-url http://localhost:5000
│  └─ Outputs: Search results JSON
│
├─ Step 3: Search (Images)
│  ├─ python key_point_search_tool.py \
│  │   --input extractor_output.json \
│  │   --backend-url http://localhost:5000 \
│  │   --search-type image \
│  │   --download-images
│  └─ Downloads images to downloaded_media/
│
└─ Step 4: Manage Cache/Downloads
   ├─ --list-cache / --clear-cache
   ├─ --list-downloads / --clear-downloads
   └─ --skip-cache (for fresh searches)
```

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ User Input: Text about images                                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │ run_key_point_extractor │
        │ extract_key_points()   │
        └────────────┬───────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │ extractor_output.json  │
        │ [                      │
        │   {"key_points": [    │
        │     "cat", "dog", ... │
        │   ]}                   │
        │ ]                      │
        └────────────┬───────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
    Web Search            Image Search
    (default)            (--search-type image)
        │                         │
        ├─ Query: "cat"           ├─ Query: "cat"
        ├─ Query: "dog"           ├─ Query: "dog"
        └─ Query: "..."           └─ Query: "..."
        │                         │
        │                    (--download-images)
        │                         │
        ├─ Cache check            ├─ Cache check
        │  (search_cache/)        │  (search_cache/)
        │                         │
        ├─ Request → Backend      ├─ Request → Backend
        │                         │
        ▼                         ▼
┌──────────────────────────────────────────────┐
│   google_search_backend.py                   │
│                                              │
│  ├─ Rate Limiter (2 req/min)                │
│  │  └─ Wait if needed                       │
│  │                                          │
│  ├─ Check Cache                             │
│  │  └─ Return if found (search_cache/)      │
│  │                                          │
│  ├─ Filter Ads                              │
│  │  └─ Block: ads, shopping, ...            │
│  │                                          │
│  ├─ Google API Call                         │
│  │  └─ HTTPS → api.google.com               │
│  │                                          │
│  ├─ Download Images (if requested)          │
│  │  ├─ Check size < 30MB                    │
│  │  ├─ Save to downloaded_media/            │
│  │  └─ Report errors                        │
│  │                                          │
│  └─ Cache Results                           │
│     └─ Save to search_cache/                │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────┐
    │ Results JSON             │
    │ ├─ title                 │
    │ ├─ url                   │
    │ ├─ snippet               │
    │ ├─ score                 │
    │ ├─ downloaded (images)   │
    │ └─ file_path (images)    │
    └──────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────┐
    │ User Review              │
    │                          │
    │ Options:                 │
    │ ├─ View results          │
    │ ├─ View downloads        │
    │ ├─ Clear cache           │
    │ ├─ Delete downloads      │
    │ ├─ Search again          │
    │ ├─ Search with fresh API │
    │ └─ Skip cache next time  │
    └──────────────────────────┘
```

## Example Commands

### Setup (One Time)

```powershell
# Terminal 1: Install dependencies
pip install -r requirements.txt

# Set API credentials
$env:GOOGLE_API_KEY = "AIzaSyC..."  # Your API key
$env:GOOGLE_CX = "d99a2c6..."       # Your CX ID

# Start backend server
python google_search_backend.py --port 5000
```

### Extraction (Terminal 2)

```powershell
# Run extractor
python run_key_point_extractor.py

# Input:
#   Enter text to extract key points from (press Enter on an empty line to finish):
#   I saw a brown cat and a white dog in the park yesterday. The cat was ...
#   [Enter]
#   
#   [Enter]

# Output: extractor_output.json created
```

### Web Search

```powershell
# Simple web search
python key_point_search_tool.py \
  --input extractor_output.json \
  --backend-url http://localhost:5000

# Output: Search results with URLs and snippets
```

### Image Search with Downloads

```powershell
# Search and download images
python key_point_search_tool.py \
  --input extractor_output.json \
  --backend-url http://localhost:5000 \
  --search-type image \
  --download-images

# Output: 
# - Search results in JSON
# - Images downloaded to downloaded_media/
```

### Cache Management

```powershell
# View all cached searches
python key_point_search_tool.py \
  --backend-url http://localhost:5000 \
  --list-cache

# Output:
#   [web] cat (5 results) - 2024-08-13T10:30:45
#   [web] dog (5 results) - 2024-08-13T10:31:02
#   [image] cat (5 results) - 2024-08-13T10:31:15
#   ...

# Delete specific cache
python key_point_search_tool.py \
  --backend-url http://localhost:5000 \
  --delete-cache web "cat"

# Clear ALL cache
python key_point_search_tool.py \
  --backend-url http://localhost:5000 \
  --clear-cache
```

### Download Management

```powershell
# View all downloads
python key_point_search_tool.py \
  --backend-url http://localhost:5000 \
  --list-downloads

# Output:
#   cat_image123.jpg (2.45MB)
#   cat_image456.jpg (1.87MB)
#   dog_photo789.jpg (3.22MB)
#   Total size: 7.54MB

# Delete ALL downloads
python key_point_search_tool.py \
  --backend-url http://localhost:5000 \
  --clear-downloads

# Output: Deleted 3 files. Freed 7.54MB
```

## Decision Trees

### Which Search Type?

```
Do you want to search for images?
│
├─ NO: Use default web search
│  └─ python key_point_search_tool.py --input data.json
│
└─ YES: Use image search
   │
   ├─ Don't download: --search-type image
   │  └─ Just get URLs and metadata
   │
   └─ Download images: --search-type image --download-images
      └─ Get URLs + download files locally
```

### Cache Strategy

```
Do you want to use cached results?
│
├─ YES (Default): Faster, saves API quota
│  └─ python key_point_search_tool.py --input data.json
│     (will use cache if available)
│
└─ NO: Get fresh data from API
   ├─ Use --skip-cache flag
   │  └─ python key_point_search_tool.py --input data.json --skip-cache
   │
   └─ Or delete cache first
      └─ python key_point_search_tool.py --clear-cache
```

### Storage Management

```
Running out of space?
│
├─ Check downloads: --list-downloads
│  └─ See how much space images use
│
├─ Delete downloads: --clear-downloads
│  └─ Free up space (see MB freed)
│
├─ Check cache: --list-cache
│  └─ See how many searches cached
│
└─ Clear cache: --clear-cache
   └─ Frees search_cache/ directory
```

## File Locations

```
ImageDownloader/
│
├─ Executables:
│  ├─ google_search_backend.py      ← Start this first
│  ├─ key_point_search_tool.py       ← Then run this
│  ├─ run_key_point_extractor.py     ← Or this for extraction
│  └─ requirements.txt               ← pip install this
│
├─ Generated Files:
│  ├─ extractor_output.json          ← Created by extractor
│  ├─ search_results.json            ← Created by search tool
│  │
│  ├─ downloaded_media/              ← Images from searches
│  │  ├─ cat_image123.jpg
│  │  ├─ dog_photo456.jpg
│  │  └─ ...
│  │
│  └─ search_cache/                  ← Cached search results
│     ├─ web_cat.json
│     ├─ web_dog.json
│     ├─ image_cat.json
│     └─ ...
│
└─ Documentation:
   ├─ QUICKSTART.md                  ← Start here!
   ├─ GOOGLE_SEARCH_README.md        ← Full guide
   ├─ IMPLEMENTATION_SUMMARY.md      ← What was built
   └─ WORKFLOW.md                    ← This file
```

## Troubleshooting Flow

```
Something went wrong?
│
├─ Backend errors:
│  │
│  ├─ "Backend not running" 
│  │  └─ Run: python google_search_backend.py --port 5000
│  │
│  ├─ "API key not configured"
│  │  └─ Check: echo $env:GOOGLE_API_KEY
│  │
│  └─ "Connection refused"
│     └─ Make sure backend is on http://127.0.0.1:5000
│
├─ Search errors:
│  │
│  ├─ "Rate limited (429)"
│  │  └─ Wait 1 minute, backend auto-retries
│  │
│  ├─ "No results found"
│  │  └─ Try different search terms
│  │
│  └─ "Cache is stale"
│     └─ Use --skip-cache flag
│
├─ Download errors:
│  │
│  ├─ "File too large"
│  │  └─ Size > 30MB, image skipped
│  │
│  ├─ "Download failed"
│  │  └─ Check internet connection
│  │
│  └─ "No permission"
│     └─ Check downloaded_media/ permissions
│
└─ API errors:
   │
   ├─ Check Google API Console
   │  └─ Verify API is enabled and key is valid
   │
   ├─ Check quota: 100/day free tier
   │  └─ Reset daily at midnight UTC
   │
   └─ Check CX ID is correct
      └─ Verify at programmablesearchengine.google.com
```

## Tips & Tricks

### Speed Up Searches
- Use cache (don't use `--skip-cache`)
- Cache results automatically for reuse

### Save API Quota
- Run searches once, then review cache
- Use `--list-cache` instead of re-searching

### Manage Storage
- Check download size: `--list-downloads`
- Delete old downloads: `--clear-downloads`

### Batch Processing
- Process multiple records at once
- Only pay API quota once per unique search term

### Testing
- Do a small search first (1-2 terms)
- Review results before bulk processing
- Use `--max-results 1` to limit records

## Performance Benchmarks

| Operation | Time | Notes |
|-----------|------|-------|
| Backend startup | 1-2s | Flask server start |
| Cached search | <100ms | Instant from disk |
| API search | 1-3s | Depends on API |
| Rate limit wait | 30s | 2 req/min enforced |
| Image download | 2-10s | Depends on file size |

## Quota Management

- **Free tier**: 100 searches/day
- **Rate limit**: 2 searches/minute (30s between requests)
- **Cache hits**: Don't count against quota
- **Reset time**: Daily at midnight UTC
