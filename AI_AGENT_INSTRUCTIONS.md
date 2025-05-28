# AI Agent Instructions for Supabase Integration & URL Management

## Project Overview

This is a Swedish news monitoring system built with Streamlit that scrapes news sites, analyzes content changes using OpenAI, and displays results in a dashboard. The system currently works locally but needs Supabase integration for persistence and URL management features.

## Current Implementation

### Architecture
```
streamlit_app.py          # Main Streamlit UI
backend/
  ├── monitor.py         # Orchestrates scraping & analysis
  ├── scraper.py         # Firecrawl API integration
  ├── analysis.py        # OpenAI Assistant integration
  ├── config.json        # Configuration file
  └── urls.json          # List of URLs to monitor
```

### How It Works
1. User clicks "Starta analys" button
2. System scrapes each URL using Firecrawl API
3. Compares with previous content to detect changes
4. If changes detected, analyzes with OpenAI (rates 1-5)
5. Displays results in real-time in the dashboard

## Task 1: Supabase Integration

### Database Schema (already provided in `supabase_schema.sql`)
- `analyses` table: Stores main analysis results
- `news_items` table: Stores individual news items with ratings

### Required Implementation

1. **Update `streamlit_app.py`**:
   - The Supabase client initialization is already there (`init_supabase()`)
   - The `save_to_supabase()` function exists but needs testing
   - The `load_recent_analyses()` function exists for historical view

2. **Environment Configuration**:
   - User needs to add Supabase credentials to `.streamlit/secrets.toml`:
     ```toml
     SUPABASE_URL = "https://xxxxx.supabase.co"
     SUPABASE_KEY = "eyJ..."
     ```

3. **Test Integration**:
   - Ensure data saves after each analysis run
   - Verify historical data loads in "Historik" tab
   - Handle connection errors gracefully

## Task 2: URL Management Feature

### Requirements
Allow users to:
- View current list of monitored URLs
- Add new URLs to monitor
- Remove URLs from monitoring
- Edit URL names/categories
- Persist changes to both local config and Supabase

### Suggested Implementation

1. **Create new Supabase table**:
   ```sql
   CREATE TABLE monitored_urls (
     id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
     url TEXT NOT NULL UNIQUE,
     name TEXT NOT NULL,
     category TEXT,
     active BOOLEAN DEFAULT true,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   ```

2. **Add URL Management Tab in Streamlit**:
   ```python
   # In main() function, add new tab:
   tab1, tab2, tab3, tab4 = st.tabs(["📊 Dagens analys", "📈 Historik", "🔗 URL:er", "ℹ️ Om"])
   
   with tab3:
       st.header("🔗 Hantera URL:er")
       
       # Show current URLs in editable table
       # Add form to add new URL
       # Add delete buttons for each URL
       # Save changes to Supabase AND update local urls.json
   ```

3. **Sync Strategy**:
   - On startup: Load URLs from Supabase if available, fallback to urls.json
   - On changes: Update both Supabase and local urls.json
   - This ensures the app works even if Supabase is down

### Implementation Details

1. **Add URL Form**:
   ```python
   with st.form("add_url"):
       new_url = st.text_input("URL")
       new_name = st.text_input("Namn")
       new_category = st.selectbox("Kategori", ["Kommun", "Sport", "Kultur", "Övrigt"])
       if st.form_submit_button("Lägg till"):
           # Add to Supabase
           # Update local urls.json
           # Refresh URL list
   ```

2. **URL List Display**:
   ```python
   # Use st.data_editor for inline editing
   urls_df = pd.DataFrame(current_urls)
   edited_df = st.data_editor(
       urls_df,
       column_config={
           "url": st.column_config.LinkColumn("URL"),
           "name": st.column_config.TextColumn("Namn"),
           "category": st.column_config.SelectboxColumn("Kategori", options=["Kommun", "Sport", "Kultur", "Övrigt"]),
           "active": st.column_config.CheckboxColumn("Aktiv")
       },
       hide_index=True,
       num_rows="dynamic"
   )
   ```

3. **URL Manager Class** (create `backend/url_database.py`):
   ```python
   class URLDatabase:
       def __init__(self, supabase_client, local_path="backend/urls.json"):
           self.supabase = supabase_client
           self.local_path = local_path
       
       def sync_from_supabase(self):
           """Load URLs from Supabase and update local file"""
       
       def add_url(self, url, name, category):
           """Add URL to both Supabase and local file"""
       
       def remove_url(self, url):
           """Remove URL from both Supabase and local file"""
       
       def update_url(self, old_url, new_data):
           """Update URL in both Supabase and local file"""
   ```

## Task 3: Additional Improvements

1. **Add Export Feature**:
   - Export analysis results as CSV/Excel
   - Export high-rated news items as markdown

2. **Add Filtering**:
   - Filter by date range
   - Filter by category
   - Filter by minimum rating

3. **Add Scheduling Info**:
   - Show when each URL was last analyzed
   - Show next scheduled run time
   - Add manual "analyze single URL" option

## Deployment Considerations

1. **Streamlit Cloud**:
   - Ensure all paths work when deployed
   - Use st.secrets for API keys
   - Consider timeout limits for long-running analyses

2. **Performance**:
   - Cache analysis results
   - Add progress indicators
   - Consider batch processing for many URLs

3. **Error Handling**:
   - Handle API rate limits gracefully
   - Retry failed URLs
   - Show clear error messages to users

## Testing Checklist

- [ ] Supabase connection works
- [ ] Data persists between sessions
- [ ] URL management CRUD operations work
- [ ] Historical data displays correctly
- [ ] Export features work
- [ ] Error states handled gracefully
- [ ] Works on mobile devices
- [ ] Deploys successfully to Streamlit Cloud