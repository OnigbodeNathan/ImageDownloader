# Quick Start Guide

## 5-Minute Setup

### 1. Get Google API Credentials (2 min)

**API Key:**
- Go to https://console.cloud.google.com/
- Create project → Enable "Custom Search API" → Create API Key
- Copy the key

**Search Engine ID (cx):**
- Go to https://programmablesearchengine.google.com/
- Create engine → Copy "Search engine ID"

### 2. Install Dependencies (1 min)

```powershell
cd c:\Users\ntane\Documents\Projects\ImageDownloader
pip install -r requirements.txt
```

### 3. Terminal 1 - Start Backend (1 min)

```powershell
cd c:\Users\ntane\Documents\Projects\ImageDownloader
$env:GOOGLE_API_KEY = "paste_your_key_here"
$env:GOOGLE_CX = "paste_your_cx_here"
python google_search_backend.py --port 5000
```

You should see:
```
Starting Google Search Backend Server
Host: 127.0.0.1:5000
API Key configured: True
CX configured: True
```

### 4. Terminal 2 - Run Searches (1 min)

**Extract key points:**
```powershell
cd c:\Users\ntane\Documents\Projects\ImageDownloader
python run_key_point_extractor.py
```
Enter text, press Enter twice → Saves to `extractor_output.json`

**Search for key points:**
```powershell
# Web search
python key_point_search_tool.py --input extractor_output.json --backend-url http://localhost:5000

# Image search with downloads
python key_point_search_tool.py --input extractor_output.json --backend-url http://localhost:5000 --search-type image --download-images
```

## Common Commands

```powershell
# List cached results
python key_point_search_tool.py --backend-url http://localhost:5000 --list-cache

# Clear cache
python key_point_search_tool.py --backend-url http://localhost:5000 --clear-cache

# List downloaded images
python key_point_search_tool.py --backend-url http://localhost:5000 --list-downloads

# Delete downloaded images
python key_point_search_tool.py --backend-url http://localhost:5000 --clear-downloads

# Skip cache and search fresh
python key_point_search_tool.py --input extractor_output.json --backend-url http://localhost:5000 --skip-cache
```

## Features Summary

✅ **Integrated Google Search** - Web and image search via API
✅ **API Key Protection** - Keys stored on backend only
✅ **Rate Limiting** - 2 requests/min automatic throttling
✅ **Ad Filtering** - Blocks shopping/ads automatically
✅ **Image Downloads** - Up to 30MB files with safety checks
✅ **Result Caching** - Persistent cache between runs
✅ **Cache Management** - View, delete, or clear anytime
✅ **Download Management** - Track and delete media files

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Backend not running | Terminal 1 still needs to be running `google_search_backend.py` |
| API key not working | Verify env vars: `echo $env:GOOGLE_API_KEY` |
| Rate limited | Wait 1 minute, backend auto-retries |
| Files not downloading | Check `downloaded_media/` folder exists and is writable |
| Stale results | Use `--skip-cache` to fetch fresh data |

See `GOOGLE_SEARCH_README.md` for detailed documentation.
