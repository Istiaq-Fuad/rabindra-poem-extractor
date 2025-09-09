# Bangla Poem Scraper (Rabindra Rachanabali)

Scrapes poems from https://rabindra-rachanabali.nltr.org while preserving original formatting and Bengali text structure.

## Prerequisites

- uv (Python package/dependency manager): https://docs.astral.sh/uv/
- Python (uv can manage Python automatically; Python 3.11+ recommended)

Install uv:

- macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Windows (PowerShell): `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`

Verify: `uv --version`

## Setup

From the project root:

```bash
# Initialize the project and install dependencies from pyproject.toml
uv sync
```

This sets up the project with a virtual environment managed automatically by uv.

## Run

```bash
# Run the scraper (uv handles venv creation/activation automatically)
uv run main.py
```

Output files will be written under `output/` (auto-created).

## Codebase overview

### Core Files

- **`poem_scraper.py`** — Main scraper module containing:

  - `RabindraPoetryParser` — Handles poem content parsing with proper formatting:
    - Preserves spacing and indentation using `&nbsp;` detection
    - Handles both `<p>` tag and `<br>` tag poem structures
    - Maintains Bengali text formatting integrity
    - Processes multi-page poems with pagination support
  - `RabindraPoetryaScraper` — Main scraper class with:
    - Networking layer (requests session with proper headers)
    - Collection discovery and poem link extraction
    - Multi-page poem content aggregation
    - Polite crawling with configurable delays
    - Save utilities for both JSON and text formats

- **`main.py`** — Entry point that:
  - Instantiates the scraper
  - Runs a test scrape on collection 1
  - Contains commented code for full site scraping
  - Saves output in both JSON and text formats

### Output Structure

- **`output/`** — Generated output folder containing:
  - `rabindra_poems_test.json` — Test poems in JSON format with metadata
  - `rabindra_poems_test.txt` — Test poems in plain text with formatting markers

### Project Configuration

- **`pyproject.toml`** — Project dependencies and metadata (managed by uv)
- **`uv.lock`** — Dependency lock file for reproducible builds

## Features

### Smart Text Processing

- **Spacing Preservation**: Accurately preserves indentation and spacing using `&nbsp;` entity detection
- **Multi-format Support**: Handles both paragraph-based and line-break-based poem structures
- **Bengali Text Integrity**: Maintains proper Bengali character encoding and formatting
- **Pagination Handling**: Automatically follows "পরবর্তী" (Next) links for multi-page poems

### Output Formats

- **JSON**: Structured data with metadata (title, URL, collection ID, page count)
- **Text**: Clean text format with `<start_poem>`, `<end_poem>`, and `<stanza>` markers

### Respectful Scraping

- Configurable delays between requests (default: 1 second between poems, 0.5 seconds between pages)
- Proper User-Agent headers
- Error handling and graceful failure recovery

## Configuration

### Basic Usage

```python
# Default configuration
scraper = RabindraPoetryaScraper()

# Test single collection
test_poems = scraper.scrape_collection(1)
```

### Advanced Configuration

```python
# Custom base URL (if needed)
scraper = RabindraPoetryaScraper(base_url="https://custom-url.com")

# Scrape specific collection range
all_poems = scraper.scrape_all_collections(start_subcatid=1, end_subcatid=10)

# Save with custom filenames
scraper.save_poems(poems, "custom_output.json")
scraper.save_poems_text(poems, "custom_output.txt")
```

### Targeting Specific Collections

Edit `main.py` to:

- Test specific collections: `scraper.scrape_collection(collection_id)`
- Scrape collection ranges: `scraper.scrape_all_collections(start_subcatid=X, end_subcatid=Y)`
- Enable full site scraping: uncomment the full scrape section

## Data Structure

### JSON Output Format

```json
{
  "title": "কবিতার নাম",
  "url": "https://rabindra-rachanabali.nltr.org/node/XXXX",
  "collection_id": 1,
  "content": "কবিতার বিষয়বস্তু...",
  "total_pages": 1
}
```

### Text Output Format

```
<start_poem>
কবিতার প্রথম লাইন<line>
দ্বিতীয় লাইন<line>
<stanza>
নতুন স্তবক<line>
<end_poem>
```

## Responsible Scraping

- **Be respectful**: Keep delays reasonable, avoid overwhelming the site
- **Educational purpose**: This project is intended for research and educational use
- **Rate limiting**: Built-in delays prevent server overload
- **Error handling**: Graceful failure ensures partial results aren't lost

## Troubleshooting

### Common Issues

- **Empty results**: Check if the website structure has changed
- **Encoding issues**: Ensure your terminal supports UTF-8 for Bengali text
- **Network errors**: Check internet connection and site availability

### Debugging

- Enable verbose output by checking console messages
- Inspect `output/` folder for partial results
- Test with single collection first before full scraping

## Contributing

When modifying the scraper:

1. Test with a small collection first
2. Verify Bengali text formatting is preserved
3. Check both JSON and text output formats
4. Ensure proper error handling for network issues

## License

This project is for educational and research purposes. Please respect the original website's terms of service and copyright policies.
