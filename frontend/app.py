#!/usr/bin/env python3
"""
Streamlit UI for Mitti Scraper
"""

import streamlit as st
import json
import os
import subprocess
import time
from datetime import datetime
import pandas as pd

# Set page config
st.set_page_config(
    page_title="Mitti Scraper",
    page_icon="📰",
    layout="wide"
)

# Utility functions
def load_urls():
    """Load URLs from the urls.json file"""
    try:
        with open('urls.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_urls(urls):
    """Save URLs to the urls.json file"""
    with open('urls.json', 'w') as f:
        json.dump(urls, f, indent=2)

def load_config():
    """Load configuration from config.json"""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_config(config):
    """Save configuration to config.json"""
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)

def run_scraper():
    """Run the scraper script"""
    process = subprocess.Popen(["python", "main.py"], 
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True)
    return process

def get_log_entries(num_lines=100):
    """Get the most recent log entries"""
    try:
        with open('content_monitor.log', 'r') as f:
            lines = f.readlines()
            return lines[-num_lines:]
    except FileNotFoundError:
        return ["No log file found"]

def load_analysis_data():
    """Load analysis data from the analysis directory"""
    analysis_data = []
    try:
        analysis_dir = "data/analysis"
        for filename in os.listdir(analysis_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(analysis_dir, filename), 'r') as f:
                        data = json.load(f)
                        # Extract key info
                        url = data.get('url', 'Unknown')
                        
                        # Try to get analysis text
                        analysis_obj = data.get('analysis', {})
                        analysis_text = ""
                        rating = None
                        
                        if isinstance(analysis_obj, dict):
                            analysis_text = analysis_obj.get('analysis', '')
                            rating = analysis_obj.get('rating')
                        else:
                            analysis_text = str(analysis_obj)
                        
                        # Extract timestamp
                        timestamp = data.get('stored_at', 'Unknown')
                        if timestamp != 'Unknown':
                            try:
                                timestamp = datetime.fromisoformat(timestamp)
                            except ValueError:
                                pass
                        
                        # Add to list
                        analysis_data.append({
                            'url': url,
                            'timestamp': timestamp,
                            'rating': rating,
                            'analysis': analysis_text[:200] + '...' if len(analysis_text) > 200 else analysis_text,
                            'filename': filename
                        })
                except Exception as e:
                    analysis_data.append({
                        'url': filename,
                        'timestamp': 'Error',
                        'rating': None,
                        'analysis': f"Error loading file: {str(e)}",
                        'filename': filename
                    })
                    
        # Sort by timestamp (newest first)
        analysis_data.sort(key=lambda x: x['timestamp'] if isinstance(x['timestamp'], datetime) else datetime.min, reverse=True)
        return analysis_data
    except Exception as e:
        return [{"url": "Error", "timestamp": "Error", "rating": None, "analysis": f"Error loading analysis data: {str(e)}"}]

# Main UI
st.title("Mitti Scraper Dashboard")
st.subheader("Monitor websites for changes and analyze content")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["URLs", "Configuration", "Run & Monitor", "Analysis Results"])

# Tab 1: URL Management
with tab1:
    st.header("Manage URLs to Monitor")
    
    # Load current URLs
    urls = load_urls()
    
    # Display current URLs
    url_data = []
    for url_info in urls:
        url_data.append({
            "Name": url_info.get("name", ""),
            "URL": url_info.get("url", ""),
            "Category": url_info.get("category", "")
        })
    
    # Convert to DataFrame for easier editing
    if url_data:
        df = pd.DataFrame(url_data)
        edited_df = st.data_editor(df, num_rows="dynamic", key="url_editor")
        
        # Save button
        if st.button("Save URLs"):
            # Convert edited DataFrame back to the original format
            new_urls = []
            for _, row in edited_df.iterrows():
                if row["URL"]:  # Only include rows with a URL
                    new_urls.append({
                        "name": row["Name"],
                        "url": row["URL"],
                        "category": row["Category"]
                    })
            save_urls(new_urls)
            st.success("URLs saved successfully!")
    else:
        st.info("No URLs configured. Add some below.")
        
        # Manual URL entry form
        with st.form("new_url_form"):
            name = st.text_input("Name")
            url = st.text_input("URL")
            category = st.text_input("Category")
            
            submitted = st.form_submit_button("Add URL")
            if submitted and url:
                urls.append({
                    "name": name,
                    "url": url,
                    "category": category
                })
                save_urls(urls)
                st.success("URL added! Refresh to see the updated table.")
                st.experimental_rerun()

# Tab 2: Configuration
with tab2:
    st.header("Configuration")
    
    # Load current config
    config = load_config()
    
    # Create expandable sections for different config areas
    with st.expander("API Keys", expanded=True):
        firecrawl_api_key = st.text_input("Firecrawl API Key", 
                                          value=config.get("firecrawl_api_key", ""),
                                          type="password")
        openai_api_key = st.text_input("OpenAI API Key", 
                                       value=config.get("openai_api_key", ""),
                                       type="password")
        openai_assistant_id = st.text_input("OpenAI Assistant ID", 
                                           value=config.get("openai_assistant_id", ""))
    
    with st.expander("Slack Notifications"):
        slack_enabled = st.checkbox("Enable Slack Notifications", 
                                   value=config.get("notifications", {}).get("slack", {}).get("enabled", False))
        slack_webhook_url = st.text_input("Slack Webhook URL", 
                                         value=config.get("notifications", {}).get("slack", {}).get("webhook_url", ""),
                                         type="password")
        slack_channel = st.text_input("Slack Channel", 
                                     value=config.get("notifications", {}).get("slack", {}).get("channel", "#content-monitoring"))
        min_rating = st.slider("Minimum Rating to Notify", 1, 5, 
                              value=config.get("notifications", {}).get("slack", {}).get("min_rating_to_notify", 3))
        max_news_age_days = st.slider("Maximum News Age (Days)", 1, 30, 
                                     value=config.get("notifications", {}).get("slack", {}).get("max_news_age_days", 1))
        include_preview = st.checkbox("Include Content Preview", 
                                     value=config.get("notifications", {}).get("slack", {}).get("include_content_preview", True))
    
    with st.expander("Storage Settings"):
        content_storage_dir = st.text_input("Content Storage Directory", 
                                           value=config.get("content_storage_dir", "data/history"))
        analysis_storage_dir = st.text_input("Analysis Storage Directory", 
                                            value=config.get("analysis_storage_dir", "data/analysis"))
    
    with st.expander("Scraping Settings"):
        similarity_threshold = st.slider("Similarity Threshold", 0.0, 1.0, 
                                        value=float(config.get("similarity_threshold", 0.9)),
                                        step=0.01)
        timeout = st.number_input("Scraping Timeout (seconds)", 
                                 value=config.get("scraping", {}).get("timeout", 30))
        max_content_length = st.number_input("Max Content Length", 
                                            value=config.get("scraping", {}).get("max_content_length", 10000))
        user_agent = st.text_input("User Agent", 
                                  value=config.get("scraping", {}).get("user_agent", "Mozilla/5.0"))
        fallback_to_direct = st.checkbox("Fallback to Direct Scraping", 
                                        value=config.get("scraping", {}).get("fallback_to_direct", True))
    
    # Cron Schedule
    with st.expander("Scheduling (for information only - set in render.yaml)"):
        st.info("Scheduling is managed via the render.yaml file for deployment. The default schedule is hourly.")
        st.code("""
# Example render.yaml schedule configuration
services:
  - type: cron
    name: mitti-scraper
    env: python
    schedule: "0 */1 * * *"  # Run hourly
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py
        """)
    
    # Save button
    if st.button("Save Configuration"):
        # Update config with new values
        config = {
            "firecrawl_api_key": firecrawl_api_key,
            "openai_api_key": openai_api_key,
            "openai_assistant_id": openai_assistant_id,
            "url_list_path": "urls.json",
            "content_storage_dir": content_storage_dir,
            "analysis_storage_dir": analysis_storage_dir,
            "similarity_threshold": similarity_threshold,
            "scraping": {
                "timeout": timeout,
                "max_content_length": max_content_length,
                "user_agent": user_agent,
                "fallback_to_direct": fallback_to_direct
            },
            "notifications": {
                "slack": {
                    "enabled": slack_enabled,
                    "webhook_url": slack_webhook_url,
                    "min_rating_to_notify": min_rating,
                    "include_content_preview": include_preview,
                    "max_news_age_days": max_news_age_days,
                    "channel": slack_channel
                }
            }
        }
        save_config(config)
        st.success("Configuration saved successfully!")

# Tab 3: Run & Monitor
with tab3:
    st.header("Run Scraper & Monitor Logs")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("Run Scraper Now", type="primary"):
            with st.spinner("Running scraper..."):
                process = run_scraper()
                stdout, stderr = process.communicate()
                
                if process.returncode == 0:
                    st.success("Scraper completed successfully!")
                else:
                    st.error(f"Scraper failed with return code {process.returncode}")
                    st.error(stderr)
    
    with col2:
        auto_refresh = st.checkbox("Auto-refresh logs", value=False)
        if auto_refresh:
            st.warning("Auto-refresh will reload the logs every 10 seconds. This may increase server load.")
    
    # Log display
    st.subheader("Logs")
    log_container = st.container()
    
    with log_container:
        log_entries = get_log_entries()
        st.code("".join(log_entries), language="log")
    
    # Set up auto-refresh
    if auto_refresh:
        # This will rerun the script every 10 seconds
        time.sleep(10)
        st.experimental_rerun()

# Tab 4: Analysis Results
with tab4:
    st.header("Analysis Results")
    
    analysis_data = load_analysis_data()
    
    if analysis_data:
        # Convert to DataFrame
        df = pd.DataFrame(analysis_data)
        
        # Format the timestamp column
        try:
            df['formatted_time'] = df['timestamp'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if isinstance(x, datetime) else str(x))
        except:
            df['formatted_time'] = df['timestamp']
        
        # Select columns to display
        display_df = df[['url', 'formatted_time', 'rating', 'analysis']]
        display_df.columns = ['URL', 'Timestamp', 'Rating', 'Analysis']
        
        # Display the table
        st.dataframe(display_df, hide_index=True)
        
        # Show details for a selected entry
        st.subheader("View Full Analysis")
        
        selected_file = st.selectbox("Select an analysis file to view", 
                                    options=df['filename'].tolist(),
                                    format_func=lambda x: f"{x} - {df[df['filename'] == x]['formatted_time'].iloc[0]}")
        
        if selected_file:
            try:
                with open(os.path.join("data/analysis", selected_file), 'r') as f:
                    data = json.load(f)
                    
                # Extract analysis text
                analysis_obj = data.get('analysis', {})
                if isinstance(analysis_obj, dict):
                    analysis_text = analysis_obj.get('analysis', '')
                    rating = analysis_obj.get('rating')
                    st.info(f"Rating: {rating}")
                else:
                    analysis_text = str(analysis_obj)
                
                st.text_area("Full Analysis", value=analysis_text, height=400)
                
                # Display news items if available
                if isinstance(analysis_obj, dict) and 'news_items' in analysis_obj:
                    news_items = analysis_obj.get('news_items', [])
                    if news_items:
                        st.subheader("News Items")
                        for i, item in enumerate(news_items):
                            with st.expander(f"{item.get('title', f'Item {i+1}')}"):
                                st.write(f"URL: {item.get('url', 'N/A')}")
                                st.write(f"Date: {item.get('date', 'N/A')}")
                                st.write(f"Rating: {item.get('rating', 'N/A')}")
                                st.write(f"Snippet: {item.get('snippet', 'N/A')}")
            except Exception as e:
                st.error(f"Error loading analysis file: {str(e)}")
    else:
        st.info("No analysis data found. Run the scraper to generate analysis.")

# Footer
st.markdown("---")
st.caption("Mitti Scraper - A web content monitoring tool for local news")