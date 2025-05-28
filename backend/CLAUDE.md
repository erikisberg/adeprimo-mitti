# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mitti Scraper is a content monitoring tool that:
1. Scrapes web content from configured URLs using Firecrawl API (with direct scraping fallback)
2. Detects significant changes compared to previously stored content
3. Analyzes changes using OpenAI's Assistant API on a 1-5 interest scale
4. Stores content and analysis for future comparison
5. Provides a Streamlit UI for configuration and viewing results

## Architecture

- `main.py`: Entry point that initializes and runs the content monitor
- `monitor.py`: Main orchestration class (ContentMonitor) that coordinates the monitoring process
- `scraper.py`: Handles web content scraping using Firecrawl API with fallback to direct scraping
- `analysis.py`: Uses OpenAI Assistant API to analyze content changes
- `comparison.py`: Compares content versions to detect significant changes
- `url_manager.py`: Manages the list of URLs to monitor
- `config.py`: Handles configuration loading and management
- `notifications.py`: Sends notifications (Slack) for significant content changes
- `storage/`: Contains modules for storing content and analysis data
  - `storage/content.py`: Manages storage of scraped content
  - `storage/analysis.py`: Manages storage of analysis results
- `frontend/app.py`: Streamlit UI for configuration and viewing results

## Development Commands

### Setup Environment
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p data/history data/analysis
```

### Running the Application
```bash
# Run the main scraper
python main.py

# Run the frontend (requires Streamlit)
cd frontend
streamlit run app.py
```

### Testing
```bash
# Test OpenAI integration
python test_openai.py

# Test setup
python setup_test.py

# Test scraper
python test_scraper.py

# Run tests with a specific URL
python test_scraper.py --url https://example.com
```

### Configuration

The system is configured via `config.json`, with the following key settings:
- `firecrawl_api_key`: API key for Firecrawl scraping service
- `openai_api_key`: API key for OpenAI
- `openai_assistant_id`: ID of the OpenAI Assistant for content analysis
- `similarity_threshold`: Threshold for detecting significant content changes (0.0-1.0)
- `url_list_path`: Path to the JSON file containing URLs to monitor
- `content_storage_dir`: Directory for storing scraped content
- `analysis_storage_dir`: Directory for storing analysis results
- `notifications`: Settings for notification services (e.g., Slack)

## Code Style Conventions

- **Imports**: Standard library → third-party → local modules
- **Formatting**: 4-space indentation, 100-char line limit
- **Types**: Use type hints (Dict, List, Optional, etc.)
- **Naming**: snake_case for variables/functions, CamelCase for classes
- **Error Handling**: Use try/except with specific exceptions, log errors
- **Docstrings**: Required for all classes/functions ("""multi-line format""")
- **Logging**: Use logger.info/warning/error instead of print statements
- **Environment**: Store credentials in .env, never in code

## Key Implementation Notes

1. The system uses OpenAI's Assistant API for content analysis, which requires:
   - A valid OpenAI API key
   - A configured OpenAI Assistant with specific instructions (see README)

2. Content scraping uses Firecrawl API with fallback to direct requests:
   - Firecrawl provides better content extraction and news item identification
   - Direct scraping is used as a fallback and is more basic

3. The system handles rate limiting for both Firecrawl and OpenAI APIs

4. Analysis results include:
   - Overall content change rating (1-5 scale)
   - Extracted news items with individual ratings when possible
   - Explanation of the analysis

5. Slack notifications can be configured to alert on high-interest content changes