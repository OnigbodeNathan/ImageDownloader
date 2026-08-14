# Example Outputs & Expected Results

## Backend Server Startup

### Terminal 1 Output
```
Starting Google Search Backend Server
Host: 127.0.0.1:5000
API Key configured: True
CX configured: True
Download directory: C:\Users\ntane\Documents\Projects\ImageDownloader\downloaded_media
Cache directory: C:\Users\ntane\Documents\Projects\ImageDownloader\search_cache
 * Running on http://127.0.0.1:5000 (Press CTRL+C to quit)
```

---

## Key Point Extraction

### Run Command
```powershell
python run_key_point_extractor.py
```

### Terminal 2 Input Example
```
Enter text to extract key points from (press Enter on an empty line to finish):
I saw a brown cat playing with a white dog in the park. Both animals were happy.
[Enter]
[Enter]
```

### Expected Output
```
Extracted key points:
1. cat
2. dog
3. animals
4. park
5. brown
6. white
7. playing

Results saved to: extractor_output.json
Use with key_point_search_tool: python key_point_search_tool.py --input extractor_output.json --backend-url http://localhost:5000
```

### Generated extractor_output.json
```json
[
  {
    "source": "extracted_text",
    "image_path": "extracted_text",
    "key_points": [
      "cat",
      "dog", 
      "animals",
      "park",
      "brown",
      "white",
      "playing"
    ],
    "image_name": "",
    "metadata": {}
  }
]
```

---

## Web Search Operation

### Run Command
```powershell
python key_point_search_tool.py --input extractor_output.json --backend-url http://localhost:5000
```

### Expected Terminal Output
```
=== Backend Setup ===
  - Backend URL: http://localhost:5000
  - ✓ Backend server is running

=== Loading extractor output ===
  - Loaded 1 extractor records
  - Grouped into 1 unique image groups

=== Collated search execution ===
  - Total unique images to process: 1
  - Search type: web
  - Processing image: extracted_text

=== Searching for result: extracted_text ===
  - Key points collected: 7
  - Running web search #1 for key point: cat
  - Found 5 results for query 'cat'
  - Running web search #2 for key point: dog
  - Found 5 results for query 'dog'
  - Running web search #3 for key point: animals
  - Found 5 results for query 'animals'
  - Running web search #4 for key point: park
  - Found 5 results for query 'park'
  - Running web search #5 for key point: brown
  - Found 5 results for query 'brown'
  - Running web search #6 for key point: white
  - Found 5 results for query 'white'
  - Running web search #7 for key point: playing
  - Found 5 results for query 'playing'

=== Search summary ===
  - extracted_text | 'cat' -> 5 matches
  - extracted_text | 'dog' -> 5 matches
  - extracted_text | 'animals' -> 5 matches
  - extracted_text | 'park' -> 5 results
  - extracted_text | 'brown' -> 5 results
  - extracted_text | 'white' -> 5 results
  - extracted_text | 'playing' -> 5 results
  - Processed images: 1
  - Processed records: 1
  - Executed queries: 7

=== Result JSON preview ===
{
  "extracted_text": [
    {
      "source": "extracted_text",
      "image_path": "extracted_text",
      "searches": [
        {
          "query": "cat",
          "matches": [
            {
              "title": "Cat - Wikipedia",
              "url": "https://en.wikipedia.org/wiki/Cat",
              "snippet": "The cat (Felis catus) is a small carnivorous mammal...",
              "score": 1.0,
              "index": 0
            },
            {
              "title": "Cats: facts, care, behavior, and more",
              "url": "https://www.nationalgeographic.com/animals/mammals/facts/cats/",
              "snippet": "Cats are carnivorous mammals that are often kept as...",
              "score": 0.9,
              "index": 1
            }
          ]
        }
      ]
    }
  ]
}
```

---

## Image Search with Downloads

### Run Command
```powershell
python key_point_search_tool.py --input extractor_output.json --backend-url http://localhost:5000 --search-type image --download-images
```

### Expected Terminal Output
```
=== Backend Setup ===
  - Backend URL: http://localhost:5000
  - ✓ Backend server is running

=== Loading extractor output ===
  - Loaded 1 extractor records
  - Grouped into 1 unique image groups

=== Collated search execution ===
  - Total unique images to process: 1
  - Search type: image
  - Image downloading: enabled
  - Processing image: extracted_text

=== Searching for result: extracted_text ===
  - Key points collected: 7
  - Running image search #1 for key point: cat
  - Found 5 results for query 'cat'
  - Running image search #2 for key point: dog
  - Found 5 results for query 'dog'
  [... more searches ...]

=== Result JSON preview ===
{
  "extracted_text": [
    {
      "source": "extracted_text",
      "image_path": "extracted_text",
      "searches": [
        {
          "query": "cat",
          "matches": [
            {
              "title": "Orange Cat",
              "url": "https://example.com/image1.jpg",
              "image_url": "https://example.com/image1.jpg",
              "snippet": "Beautiful orange tabby cat",
              "score": 1.0,
              "index": 0,
              "downloaded": true,
              "file_path": "C:\\...\\downloaded_media\\cat_image1.jpg"
            }
          ]
        }
      ]
    }
  ]
}
```

### Downloaded Files Created
```
downloaded_media/
├── cat_image1.jpg (2.45MB)
├── cat_image2.jpg (1.87MB)
├── dog_photo1.jpg (3.22MB)
├── dog_photo2.jpg (2.15MB)
└── ...
```

---

## Cache Listing

### Run Command
```powershell
python key_point_search_tool.py --backend-url http://localhost:5000 --list-cache
```

### Expected Output
```
=== Backend Setup ===
  - Backend URL: http://localhost:5000
  - ✓ Backend server is running

=== Cached Search Results ===
  - [web] cat (5 results) - 2024-08-13T10:30:45.123456
  - [web] dog (5 results) - 2024-08-13T10:31:02.456789
  - [web] animals (5 results) - 2024-08-13T10:31:19.789012
  - [image] cat (5 results) - 2024-08-13T10:32:45.234567
  - [image] dog (5 results) - 2024-08-13T10:33:02.567890
```

### Generated Cache Files
```
search_cache/
├── web_cat.json
├── web_dog.json
├── web_animals.json
├── image_cat.json
└── image_dog.json
```

---

## Cache Clearing

### Run Command
```powershell
python key_point_search_tool.py --backend-url http://localhost:5000 --clear-cache
```

### Expected Output
```
=== Backend Setup ===
  - Backend URL: http://localhost:5000
  - ✓ Backend server is running

=== Clearing Cache ===
  - ✓ All cached results cleared
```

---

## Delete Specific Cache

### Run Command
```powershell
python key_point_search_tool.py --backend-url http://localhost:5000 --delete-cache web "cat"
```

### Expected Output
```
=== Backend Setup ===
  - Backend URL: http://localhost:5000
  - ✓ Backend server is running

=== Deleting Cache Entry ===
  - ✓ Deleted cache for [web] cat
```

---

## List Downloaded Media

### Run Command
```powershell
python key_point_search_tool.py --backend-url http://localhost:5000 --list-downloads
```

### Expected Output
```
=== Backend Setup ===
  - Backend URL: http://localhost:5000
  - ✓ Backend server is running

=== Downloaded Media Files ===
  - cat_image1.jpg (2.45MB)
  - cat_image2.jpg (1.87MB)
  - dog_photo1.jpg (3.22MB)
  - dog_photo2.jpg (2.15MB)
  - dog_photo3.jpg (2.98MB)
  - animals_pic1.jpg (1.56MB)
  - Total size: 14.18MB
```

---

## Clear All Downloads

### Run Command
```powershell
python key_point_search_tool.py --backend-url http://localhost:5000 --clear-downloads
```

### Expected Output
```
=== Backend Setup ===
  - Backend URL: http://localhost:5000
  - ✓ Backend server is running

=== Clearing Downloads ===
  - ✓ All downloaded files cleared
```

### Backend Log
```
Backend processing...
 * POST /downloaded-media HTTP/1.1" 200 -
```

---

## Error Examples

### Backend Not Running
```
❌ Backend server is not running or not accessible
Start it with: python google_search_backend.py --port 5000
```

### API Key Not Configured
```
{
  "error": "Google API credentials not configured",
  "hint": "Set GOOGLE_API_KEY and GOOGLE_CX environment variables"
}
```

### Rate Limited (Auto-Retry)
```
  - Rate limited. Waiting 45 seconds...
  [Backend automatically retries after delay]
```

### File Too Large
```
{
  "downloaded": false,
  "download_error": "File too large: 45.23MB (max: 30MB)",
  "url": "https://example.com/large-image.jpg"
}
```

---

## Cache File Example (web_cat.json)
```json
{
  "query": "cat",
  "cached_at": "2024-08-13T10:30:45.123456",
  "results": [
    {
      "title": "Cat - Wikipedia",
      "url": "https://en.wikipedia.org/wiki/Cat",
      "snippet": "The cat (Felis catus) is a small carnivorous mammal...",
      "score": 1.0,
      "index": 0
    },
    {
      "title": "Cats: facts, care, behavior, and more",
      "url": "https://www.nationalgeographic.com/animals/mammals/facts/cats/",
      "snippet": "Cats are carnivorous mammals that are often kept as...",
      "score": 0.9,
      "index": 1
    }
  ]
}
```

---

## Success Indicators

✅ **Backend Running**: See "API Key configured: True" and "CX configured: True"
✅ **Extraction Working**: extractor_output.json created with key points
✅ **Search Successful**: 5+ results returned per query
✅ **Caching Working**: search_cache/ directory has JSON files
✅ **Downloads Working**: downloaded_media/ directory has image files
✅ **Management Working**: Commands execute with ✓ success indicators

---

## File System After Full Run

```
ImageDownloader/
├── google_search_backend.py
├── key_point_search_tool.py
├── run_key_point_extractor.py
├── key_point_extractor.py
├── requirements.txt
├── README.md
├── QUICKSTART.md
├── WORKFLOW.md
├── GOOGLE_SEARCH_README.md
├── IMPLEMENTATION_SUMMARY.md
├── IMPLEMENTATION_COMPLETE.md
│
├── extractor_output.json (Created)
│
├── downloaded_media/ (Created)
│  ├── cat_image1.jpg
│  ├── cat_image2.jpg
│  ├── dog_photo1.jpg
│  └── ...
│
└── search_cache/ (Created)
   ├── web_cat.json
   ├── web_dog.json
   ├── image_cat.json
   └── ...
```

---

**All outputs follow the expected format and behavior as demonstrated above.**
