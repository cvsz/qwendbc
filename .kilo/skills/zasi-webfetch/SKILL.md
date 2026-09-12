---
name: webfetch
description: >
  Fetch, parse, scrape, and extract structured technical content, documentation,
  APIs, and schemas from any live URL or web resource for the ZASI superintelligence
  operating system without browser overhead.
---

# WebFetch Skill for ZASI

High-throughput, clean markdown and JSON extraction from any web source.

## Usage Modes

1. **Jina Reader HTTP Endpoint**:
   ```bash
   curl -s "https://r.jina.ai/<TARGET_URL>"
   ```

2. **Python Fallback Extractor (Built-in)**:
   ```python
   import urllib.request
   import json

   req = urllib.request.Request(
       url,
       headers={"User-Agent": "ZASI-WebFetch/32.0.0 (Omniversal Agent)"}
   )
   with urllib.request.urlopen(req, timeout=10) as resp:
       content = resp.read().decode('utf-8')
   ```

3. **Direct HTML Extraction with Stripping**:
   Used to retrieve live API definitions, arXiv papers, and upstream RFC specs.
