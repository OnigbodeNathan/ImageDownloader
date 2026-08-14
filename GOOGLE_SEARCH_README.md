# Google Search Integration for Key Point Extractor

This system combines key point extraction with internet search capabilities using Google Custom Search API.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Run Key Point Extractor                                 │
│ Outputs: JSON with extracted key points                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ Key Point Search Tool (key_point_search_tool.py)        │
│ - Sends searches to backend                             │
│ - Orchestrates search operations                        │
│ - Manages cache and downloads                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼ (HTTP Requests)
┌─────────────────────────────────────────────────────────┐
│ Google Search Backend (google_search_backend.py)        │
│ - Stores API keys securely (environment variables)      │
│ - Rate limiting (2 requests/minute)                     │
│ - Ad filtering                                          │
│ - Image downloading (max 30MB per file)                 │
│ - Result caching                                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼ (HTTPS)
        Google Custom Search API
```

## Prerequisites

1. **Python 3.10+**
2. **Google Custom Search API credentials:**
   - API Key: https://console.cloud.google.com/
   - Custom Search Engine ID (cx): https://programmablesearchengine.google.com/

3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

## Setup

### 1. Get Google API Credentials

**API Key:**
1. Go to https://console.cloud.google.com/
2. Create a new project (or use existing)
3. Enable "Custom Search API"
4. Create an API key (Credentials > Create Credentials > API Key)

**Custom Search Engine ID (cx):**
1. Go to https://programmablesearchengine.google.com/
2. Create a new search engine
3. Copy the "Search engine ID" (this is your cx)

### 2. Set Environment Variables

**Windows PowerShell:**
```powershell
$env:GOOGLE_API_KEY = "your_actual_api_key_here"
$env:GOOGLE_CX = "your_actual_cx_id_here"
```

**Windows Command Prompt:**
```cmd
set GOOGLE_API_KEY=your_actual_api_key_here
set GOOGLE_CX=your_actual_cx_id_here
```

## Usage

### Step 1: Start Backend Server (Terminal 1)

```powershell
# Set environment variables
$env:GOOGLE_API_KEY = "your_api_key"
$env:GOOGLE_CX = "your_cx_id"

# Start backend
python google_search_backend.py --port 5000
```

Expected output:
```
Starting Google Search Backend Server
Host: 127.0.0.1:5000
API Key configured: True
CX configured: True
Download directory: C:\Users\ntane\Documents\Projects\ImageDownloader\downloaded_media
Cache directory: C:\Users\ntane\Documents\Projects\ImageDownloader\search_cache
```

### Step 2: Extract Key Points (Terminal 2)

```powershell
python run_key_point_extractor.py
```

Follow prompts to enter text, then it saves to `extractor_output.json`

### Step 3: Search Key Points (Terminal 2)

#### Web Search Only
```powershell
python key_point_search_tool.py --input extractor_output.json --backend-url http://localhost:5000
```

#### Image Search with Downloads
```powershell
python key_point_search_tool.py --input extractor_output.json --backend-url http://localhost:5000 --search-type image --download-images
```

#### Skip Cached Results (Fresh Search)
```powershell
python key_point_search_tool.py --input extractor_output.json --backend-url http://localhost:5000 --skip-cache
```

### Cache Management

**List all cached searches:**
```powershell
python key_point_search_tool.py --backend-url http://localhost:5000 --list-cache
```

**Delete specific cached result:**
```powershell
python key_point_search_tool.py --backend-url http://localhost:5000 --delete-cache web "cat"
python key_point_search_tool.py --backend-url http://localhost:5000 --delete-cache image "dog"
```

**Clear all cache:**
```powershell
python key_point_search_tool.py --backend-url http://localhost:5000 --clear-cache
```

### Download Management

**List all downloaded images:**
```powershell
python key_point_search_tool.py --backend-url http://localhost:5000 --list-downloads
```

**Delete all downloaded media (with size info):**
```powershell
python key_point_search_tool.py --backend-url http://localhost:5000 --clear-downloads
```

## Features

### Rate Limiting
- **2 requests per minute** enforced automatically
- Prevents API throttling/blocking
- Backend queues requests intelligently

### Ad Filtering
- Automatically filters out:
  - Shopping sites (Amazon, eBay, AliExpress)
  - Ad networks
  - Promotional links

### Image Downloading
- **Max file size: 30MB per image**
- Files organized by query (safe naming)
- Skipped on size violations
- Auto-resumed with error reporting

### Result Caching
- All searches cached locally
- Cache survives between runs
- User controls when to refresh
- Dramatically speeds up repeated searches

### API Key Protection
- API key **never exposed** to client scripts
- All API calls go through secure backend
- Keys stored only in environment variables

## Output Files

### Directories Created
- `downloaded_media/` - Downloaded images organized by query
- `search_cache/` - Cached search results (JSON)

### Search Results JSON
```json
{
  "image_name.jpg": [
    {
      "source": "image_name.jpg",
      "image_path": "image_name.jpg",
      "searches": [
        {
          "query": "cat",
          "matches": [
            {
              "title": "Cat - Wikipedia",
              "url": "https://...",
              "snippet": "The cat is a small carnivorous...",
              "score": 1.0,
              "index": 0,
              "downloaded": true,
              "file_path": "downloaded_media/cat_image123.jpg"
            }
          ]
        }
      ]
    }
  ]
}
```

## Troubleshooting

### "Backend server is not running"
- Make sure Terminal 1 is running `google_search_backend.py`
- Check port 5000 is not in use: `netstat -ano | findstr :5000`

### "API Key not configured"
- Verify environment variables are set correctly
- Test with: `echo $env:GOOGLE_API_KEY`

### Rate Limiting Errors (429)
- Backend automatically retries with delays
- Try again in a minute if you hit quota limits
- Google Free tier: 100 searches/day

### Images Not Downloading
- Check file size (must be < 30MB)
- Verify `downloaded_media` folder has write permissions
- Check internet connection

### Cache Issues
- Clear cache with `--clear-cache` if results are stale
- Check `search_cache/` folder size

## API Endpoints (Backend Reference)

### Web Search
```
POST /search
Body: {"query": "...", "num_results": 5, "skip_cache": false}
Returns: {"results": [...], "cached": true/false}
```

### Image Search
```
POST /image-search
Body: {"query": "...", "num_results": 5, "download": true, "skip_cache": false}
Returns: {"results": [...], "cached": true/false}
```

### Cache Management
```
GET /cache                              - List all caches
DELETE /cache                           - Clear all caches
DELETE /cache/{type}/{query}            - Delete specific cache
```

### Download Management
```
GET /downloaded-media                   - List files
DELETE /downloaded-media                - Delete all files
```

### Health Check
```
GET /health
Returns: {"status": "ok", "api_configured": true, "timestamp": "..."}
```

## Performance Tips

1. **Reuse cache:** Don't use `--skip-cache` unless needed
2. **Batch searches:** Process multiple records at once
3. **Limit results:** Keep `num_results` reasonable (5-10)
4. **Monitor quota:** Free tier Google API = 100 searches/day

## Limits & Quotas

| Limit | Value |
|-------|-------|
| Requests/minute | 2 |
| File size (downloads) | 30MB |
| Typical API quota | 100/day (free tier) |
| Search results | 1-10 per query |

## File Structure

```
ImageDownloader/
├── google_search_backend.py        # Backend server (stores API key)
├── key_point_search_tool.py        # Search orchestrator (uses backend)
├── key_point_extractor.py          # Key point extraction
├── run_key_point_extractor.py      # Extraction runner
├── test_key_point_extractor.py     # Tests
├── requirements.txt                # Python dependencies
├── downloaded_media/               # Downloaded images
├── search_cache/                   # Cached search results
└── README.md                       # This file
```

## Security Notes

✅ **Safe:**
- API keys stored only on backend server (environment variables)
- Client scripts never see API keys
- All API calls authenticated server-side

⚠️ **Keep Secure:**
- Never commit API keys to version control
- Use `.gitignore` to exclude env files
- Restrict backend server to localhost (default)

## Future Enhancements

- [ ] Remote backend deployment (with authentication)
- [ ] Elasticsearch integration for faster local searches
- [ ] Custom filtering rules
- [ ] Database storage for persistent results
- [ ] Web UI dashboard
- [ ] Batch download management
