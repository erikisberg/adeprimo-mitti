# Streamlit Implementation Documentation

## Overview

The Streamlit app (`streamlit_app.py`) provides a web-based dashboard for the Mitti AI news monitoring system. It allows users to run analyses on-demand and view results in real-time.

## Key Features

### 1. **Real-time Analysis Execution**
- Click "Starta analys" button to begin
- Progress bar shows current URL being processed
- Results appear immediately as each site is analyzed
- No need to wait for all sites to complete

### 2. **Three Main Tabs**

#### Tab 1: Dagens analys (Today's Analysis)
- Shows results from the current/latest analysis run
- Each site displayed as a card with:
  - Site name and URL
  - Overall rating (1-5)
  - Analysis status (Analyzed/Error/No changes)
  - Expandable analysis text
  - Individual news items with ratings
- High-rated items (4-5) highlighted with 🔥 icon

#### Tab 2: Historik (History)
- Displays historical analyses from Supabase
- Time range selector (1, 7, or 30 days)
- Summary metrics:
  - Total analyses
  - High-interest count
  - Average rating
- Expandable cards for each historical analysis

#### Tab 3: Om (About)
- Documentation about the system
- Explanation of rating scale
- Configuration information

### 3. **Sidebar Controls**
- **Rating Filter**: Slider to show only items above certain rating
- **Analysis Button**: Primary action to start analysis
- **Progress Indicator**: Shows when analysis is running

## Technical Implementation

### State Management
```python
st.session_state["running"]  # Is analysis currently running
st.session_state["results"]  # Latest analysis results
st.session_state["last_run"] # Timestamp of last run
```

### Caching Strategy
- `@st.cache_resource` for:
  - Supabase client initialization
  - ContentMonitor initialization
- Prevents re-initialization on every interaction

### Data Flow
1. **Without Supabase**: Results stored in session state only
2. **With Supabase**: Results saved to database + session state

### UI Components

#### Analysis Card
```python
def display_analysis_card(result: Dict):
    # Creates a card with:
    # - Site name and URL
    # - Rating metric
    # - Status indicator
    # - Expandable sections
```

#### Progress Tracking
- Uses `st.progress()` for visual feedback
- Updates with each URL processed
- Shows current site being analyzed

### Error Handling
- Gracefully handles missing Supabase config
- Shows clear error messages
- Continues processing even if individual sites fail

## Configuration

### Required Secrets (`.streamlit/secrets.toml`)
```toml
# Optional - app works without these
SUPABASE_URL = "https://xxx.supabase.co"
SUPABASE_KEY = "eyJ..."

# Can override config.json values
# OPENAI_API_KEY = "sk-..."
# FIRECRAWL_API_KEY = "fc-..."
```

### Backend Integration
- Imports backend modules directly
- Uses same configuration as CLI version
- Shares storage directories

## Responsive Design
- Wide layout for desktop viewing
- Mobile-responsive components
- Collapsible sidebar
- Expandable content sections

## Performance Considerations

### Analysis Time
- ~15-30 seconds per URL
- 3-5 minutes for full analysis of 14 sites
- Real-time updates keep user engaged

### Memory Usage
- Results stored in session state
- Historical data loaded on-demand
- Efficient caching of initialized objects

## Future Enhancements

### Planned Features
1. **URL Management UI** - Add/remove/edit monitored sites
2. **Export Functionality** - Download results as CSV/PDF
3. **Scheduling Display** - Show when sites were last checked
4. **Advanced Filtering** - By date, category, source
5. **Batch Operations** - Analyze specific sites only

### Potential Improvements
1. **WebSocket Updates** - Replace polling with real-time updates
2. **Background Jobs** - Run analysis without blocking UI
3. **Multi-user Support** - User accounts and personalized lists
4. **Notifications** - Browser/email alerts for high-rated content
5. **Analytics Dashboard** - Trends and insights over time

## Deployment

### Local Development
```bash
streamlit run streamlit_app.py
```

### Streamlit Cloud
1. Push to GitHub
2. Connect repository to Streamlit Cloud
3. Add secrets in dashboard
4. Deploy (automatic on push)

### Environment
- Works with Python 3.8+
- No OS-specific dependencies
- All paths relative to project root

## Debugging

### Common Issues
1. **"No module named 'backend'"** - Check working directory
2. **Supabase errors** - Verify credentials in secrets
3. **Slow loading** - Normal for full analysis
4. **Memory errors** - Increase Streamlit resource limits

### Logging
- Backend logs appear in terminal
- Frontend errors in browser console
- Streamlit errors shown in UI

## User Experience

### Typical Workflow
1. Open dashboard
2. Adjust rating filter if desired
3. Click "Starta analys"
4. Watch results appear
5. Review high-rated items
6. Check historical trends
7. Export or note interesting findings

### Best Practices
- Run once daily (morning recommended)
- Set rating filter to 3+ for important news
- Review historical tab weekly for patterns
- Export high-rated items for articles