# Mitti AI News Monitoring System

A Swedish news monitoring system built with Streamlit that scrapes news sites, analyzes content changes using OpenAI, and displays results in a dashboard. The system includes Supabase integration for data persistence and URL management features.

## Features

- **Web Scraping**: Monitors configured websites for content changes using Firecrawl API
- **AI Analysis**: Analyzes new content with OpenAI to rate importance (1-5 scale)
- **Real-time Dashboard**: Shows analysis results in an intuitive Streamlit interface
- **Supabase Integration**: Stores analysis history and URL configurations in Supabase
- **URL Management**: User-friendly interface to add, edit, and remove monitored URLs
- **Email Notifications**: Sends summaries of important content via Resend
- **Slack Notifications**: Posts important content updates to Slack

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd mitti-scraper
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. API Keys and Configuration

Copy the template configuration files and add your API keys:

```bash
cp backend/config.template.json backend/config.json
cp .streamlit/secrets.template.toml .streamlit/secrets.toml
```

Then edit the files with your actual API keys:

1. **Firecrawl API Key**: For web scraping
2. **OpenAI API Key**: For content analysis
3. **OpenAI Assistant ID**: For the specific assistant model
4. **Supabase URL and Key**: For data persistence
5. **Resend API Key** (optional): For email notifications
6. **Slack Webhook URL** (optional): For Slack notifications

### 5. Supabase Setup

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Follow the instructions in `SUPABASE_SETUP_INSTRUCTIONS.md` to set up the database schema
3. Update your `.streamlit/secrets.toml` file with your Supabase credentials

### 6. Running the Application

```bash
streamlit run streamlit_app.py
```

## Using the Dashboard

The Streamlit dashboard provides four main tabs:

### 1. Today's Analysis

- Click "Start Analysis" in the sidebar to run a new analysis
- Results appear in real-time as each site is processed
- Expandable cards show detailed analysis for each site
- Filter news items by minimum rating using the slider

### 2. History

- View historical analyses stored in Supabase
- Select time period (1, 7, or 30 days)
- See summary metrics and detailed analysis history

### 3. URL Management

- View, add, edit, and remove monitored URLs
- Sync URLs between local file and Supabase
- Edit URL properties in the interactive table

### 4. About

- Information about the system
- Explanation of the rating scale
- Technical details and configuration status

## Rating Scale

The system uses a 1-5 rating scale:

- **1/5**: Routine information with no news value
- **2/5**: Low-priority news with limited interest
- **3/5**: Standard news with some general interest
- **4/5**: Important news with high general interest
- **5/5**: Very important news with significant general interest

## Deployment Considerations

- **Streamlit Cloud**: Set secrets in the Streamlit Cloud dashboard
- **Scheduled Runs**: Consider using a scheduler (e.g., cron) for regular monitoring
- **Data Storage**: Be aware of Supabase free tier limits for database storage

## Troubleshooting

- **API Key Issues**: Verify all API keys are correct in `config.json`
- **Supabase Connection**: Check Supabase URL and key in `.streamlit/secrets.toml`
- **Missing Tables**: Run the SQL setup script from `SUPABASE_SETUP_INSTRUCTIONS.md`
- **Web Scraping Failures**: Some sites may block scraping; check Firecrawl settings

## File Structure

```
mitti-scraper/
├── backend/
│   ├── analysis.py         # OpenAI integration
│   ├── config.json         # Configuration
│   ├── config.template.json # Template configuration
│   ├── monitor.py          # Core monitoring logic
│   ├── scraper.py          # Web scraping
│   ├── url_database.py     # URL management with Supabase
│   └── urls.json           # URL list
├── .streamlit/
│   ├── secrets.toml        # Streamlit secrets (not in git)
│   └── secrets.template.toml # Template for secrets
├── data/                   # Local data storage (not in git)
├── streamlit_app.py        # Streamlit dashboard
├── supabase_schema.sql     # Database schema for Supabase
└── SUPABASE_SETUP_INSTRUCTIONS.md  # Supabase setup guide
```

## License

MIT License

## Credits

- **OpenAI** for the AI analysis capabilities
- **Streamlit** for the dashboard framework
- **Supabase** for database and authentication
- **Firecrawl** for web scraping capabilities 