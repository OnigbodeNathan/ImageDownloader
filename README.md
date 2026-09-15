# ImageDownloader

A small Python workflow for extracting key points from text and downloading matching images from Pexels.

## Setup

Install dependencies:

```powershell
pip install -r requirements.txt
```

Set the Pexels API key:

```powershell
$env:PEXELS_API_KEY = "PASTE_YOUR_ACTIVE_PEXELS_API_KEY_HERE"
```

Create or copy the key from the Pexels API dashboard. Set it in the same
terminal session used to run `Github1.py`.

## Image Workflow

Extract key points, then download matching images:

```powershell
python run_key_point_extractor.py
python Github1.py
```

You can also provide text directly to `Github1.py`:

```powershell
python Github1.py --query "Mountain photography needs natural light."
```

To use a different extractor output file:

```powershell
python Github1.py --input path\to\extractor_output.json
```

`Github1.py` reads the `key_points` field produced by `run_key_point_extractor.py`.
Each unique key point becomes a Pexels search query, and images are saved under
`pexels_images`.

## Optional Search Tools

The Gemini web-search modules are still available for separate research tasks:

```powershell
python key_point_search_tool.py --input extractor_output.json
```

## Project Files

- `Github1.py`: key-point image downloader and primary workflow
- `key_point_extractor.py`: local key-point extraction logic
- `run_key_point_extractor.py`: interactive extraction CLI
- `test_key_point_extractor.py`: extractor tests
- `web_search_agent.py`: optional Gemini Google Search grounding tools
- `key_point_search_tool.py`: optional batch key-point search CLI
