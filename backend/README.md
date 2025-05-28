# Content Monitoring POC

This proof-of-concept script monitors web content from a list of URLs, detects significant changes, and analyzes those changes using OpenAI's Assistant API.

## Features

- Efficiently scrapes web content using the Firecrawl API for individual URLs (with direct scraping fallback)
- Detects significant changes by comparing with previously stored content
- Analyzes content changes using OpenAI Assistant on a 1-5 interest scale
- Stores content and analysis results locally for future comparison

## Setup Instructions

### 1. Set Up Virtual Environment and Install Dependencies

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Create Directories

Ensure the following directories exist:
- `data/history` - For storing scraped content
- `data/analysis` - For storing analysis results

```bash
mkdir -p data/history data/analysis
```

### 3. Configure OpenAI Assistant

1. Log in to your OpenAI account at https://platform.openai.com/
2. Navigate to the Assistants section
3. Create a new Assistant with the following configuration:

   - Name: Content Analyzer
   - Instructions: 
   ```
   You are a content analysis assistant that evaluates web content based on newsworthiness, relevance, and importance. 
   
   Rate content on a scale of 1-5, where:
   1 = Not interesting (routine updates)
   2 = Slightly interesting
   3 = Moderately interesting
   4 = Very interesting (significant development)
   5 = Extremely interesting (major development)
   
   For each analysis, provide:
   1. Your numerical rating (1-5)
   2. A brief explanation for your rating (2-3 sentences)
   
   Consider factors such as:
   - Is this information new or significant?
   - Does it represent a major change or development?
   - Would this information be valuable to someone monitoring this topic?
   - Is this a routine update or a significant announcement?
   ```
   
   - Model: gpt-4 or gpt-3.5-turbo (depending on your needs and account access)
   - No need to add any knowledge retrieval
   
4. After creating the assistant, copy the Assistant ID for configuration

### 4. Update Configuration

Edit the `config.json` file and update the following fields:

- `firecrawl_api_key`: Your Firecrawl API key (batch scraping requires a paid account)
- `openai_api_key`: Your OpenAI API key
- `openai_assistant_id`: The ID of the OpenAI Assistant you created

### 5. Configure URLs

Edit the `urls.json` file to include the websites you want to monitor. Each entry should include:
- `name`: A friendly name for the URL
- `url`: The actual URL to monitor
- `category` (optional): A category for grouping URLs

## Running the Script

To run the script:

```bash
python main.py
```

The script will:
1. Load the configuration and URL list
2. Scrape content from each URL
3. Compare with previously stored content
4. If significant changes are detected, send the content to OpenAI for analysis
5. Store results for future comparison
6. Display a summary of results

## Converting to a Scheduled Task

To run this script on a schedule:

### On Linux/macOS (using cron):

```bash
# Edit crontab
crontab -e

# Add a line to run the script daily at 8:00 AM
0 8 * * * cd /path/to/script && python main.py >> cron.log 2>&1
```

### On Windows (using Task Scheduler):

1. Open Task Scheduler
2. Create a new Basic Task
3. Set the trigger (e.g., daily)
4. Set the action to "Start a program"
5. Program/script: `python`
6. Add arguments: `main.py`
7. Start in: `C:\path\to\script`

## Future Improvements

- Add email notifications for high-interest content
- Implement a web interface for viewing results
- Add more sophisticated content comparison algorithms
- Integrate with messaging platforms (Slack, Teams, etc.)
- Create a database backend for better data storage