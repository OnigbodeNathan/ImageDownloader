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

## Google Images

The interface can also search Google Images and download the returned image
files locally. It uses Google's official Custom Search JSON API rather than
scraping the Google Images web page.

Create the two required Google values in Google Cloud:

1. Create or select a Google Cloud project.
2. Enable **Custom Search API** for that project.
3. Create an API key under **APIs & Services > Credentials**.
4. Create a Programmable Search Engine at
	[programmablesearchengine.google.com](https://programmablesearchengine.google.com/).
5. Configure the engine to search the web, then copy its **Search engine ID**.

In `interface.py`, enable **Google Images** and enter both values. You can
also set them before launching the interface:

```powershell
$env:GOOGLE_API_KEY = "PASTE_YOUR_GOOGLE_API_KEY_HERE"
$env:GOOGLE_SEARCH_ENGINE_ID = "PASTE_YOUR_SEARCH_ENGINE_ID_HERE"
python interface.py
```

Google allows up to 10 image results per API request. The application searches
once per extracted key point and downloads the original result URL into
`google_images\<query>`. Some source sites reject automated downloads or serve
non-image content; those individual results are logged and skipped. Google API
quotas and terms apply, and the application does not bypass hotlinking or
copyright restrictions.

## Image Workflow

For a small desktop interface that connects extraction, optional Gemini research,
and Pexels downloading in one place, run:

```powershell
python interface.py
```

The API keys can be entered in the interface or supplied through environment
variables. Images are saved under `pexels_images`.

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
- `google_image_search.py`: Google Custom Search image lookup and downloads
- `run_key_point_extractor.py`: interactive extraction CLI
- `test_key_point_extractor.py`: extractor tests
- `web_search_agent.py`: optional Gemini Google Search grounding tools
- `key_point_search_tool.py`: optional batch key-point search CLI
