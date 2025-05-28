"""
Mitti AI - News Monitoring Dashboard
A Streamlit app for monitoring Swedish news sites with AI analysis
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Optional
import time

# Import backend modules
import sys
sys.path.append('backend')

from config import ConfigManager
from monitor import ContentMonitor
from url_database import URLDatabase
from supabase import create_client, Client

# Page config
st.set_page_config(
    page_title="Mitti AI - Nyhetsövervakning",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Supabase client
@st.cache_resource
def init_supabase() -> Optional[Client]:
    """Initialize Supabase client."""
    supabase_url = st.secrets.get("SUPABASE_URL", "")
    supabase_key = st.secrets.get("SUPABASE_KEY", "")
    
    if supabase_url and supabase_key:
        try:
            client = create_client(supabase_url, supabase_key)
            st.success("✅ Connected to Supabase!")
            return client
        except Exception as e:
            st.error(f"Error connecting to Supabase: {str(e)}")
            return None
    return None

# Initialize URL database
@st.cache_resource
def init_url_db(_supabase: Optional[Client] = None):
    """Initialize URL database with Supabase connection if available."""
    return URLDatabase(_supabase, "backend/urls.json")

# Initialize monitor
@st.cache_resource
def init_monitor(_supabase: Optional[Client] = None):
    """Initialize the content monitor."""
    return ContentMonitor("backend/config.json", _supabase)

def save_to_supabase(supabase: Client, results: List[Dict]):
    """Save analysis results to Supabase."""
    try:
        # Prepare data for insertion
        for result in results:
            if result.get("status") == "analyzed":
                analysis = result.get("analysis", {})
                
                # Save main analysis
                analysis_data = {
                    "url": result.get("url"),
                    "site_name": result.get("name"),
                    "overall_rating": int(analysis.get("rating", 0)) if analysis.get("rating") else None,
                    "analysis_text": analysis.get("analysis", ""),
                    "analyzed_at": datetime.now().isoformat(),
                    "changes_detected": result.get("changes_detected", False)
                }
                
                response = supabase.table("analyses").insert(analysis_data).execute()
                analysis_id = response.data[0]["id"]
                
                # Save individual news items
                news_items = analysis.get("extracted_news", [])
                for item in news_items:
                    news_data = {
                        "analysis_id": analysis_id,
                        "title": item.get("title", ""),
                        "date": item.get("date"),
                        "rating": int(item.get("rating", 0)) if item.get("rating") else None,
                        "content": item.get("snippet", "")
                    }
                    supabase.table("news_items").insert(news_data).execute()
                    
    except Exception as e:
        st.error(f"Error saving to Supabase: {str(e)}")

def load_recent_analyses(supabase: Client, days: int = 7) -> pd.DataFrame:
    """Load recent analyses from Supabase."""
    try:
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        response = supabase.table("analyses")\
            .select("*, news_items(*)")\
            .gte("analyzed_at", since)\
            .order("analyzed_at", desc=True)\
            .execute()
            
        return response.data
    except Exception as e:
        st.error(f"Error loading from Supabase: {str(e)}")
        return []

def display_analysis_card(result: Dict):
    """Display a single analysis result as a card."""
    with st.container():
        col1, col2, col3 = st.columns([6, 2, 2])
        
        with col1:
            st.subheader(f"📰 {result.get('name', 'Unknown')}")
            st.caption(f"🔗 {result.get('url', '')}")
        
        with col2:
            if result.get("status") == "analyzed":
                analysis = result.get("analysis", {})
                rating = analysis.get("rating", "N/A")
                if rating and rating != "N/A":
                    st.metric("Betyg", f"{rating}/5")
        
        with col3:
            status = result.get("status", "unknown")
            if status == "analyzed":
                st.success("✅ Analyserad")
            elif status == "error":
                st.error("❌ Fel")
            else:
                st.info("ℹ️ Ingen ändring")
        
        if result.get("status") == "analyzed":
            analysis = result.get("analysis", {})
            
            # Show analysis text
            with st.expander("Visa analys", expanded=False):
                st.write(analysis.get("analysis", "Ingen analys tillgänglig"))
            
            # Show news items
            news_items = analysis.get("extracted_news", [])
            if news_items:
                st.markdown("**Nyheter:**")
                for item in news_items:
                    rating = item.get("rating")
                    if rating is not None and int(rating) >= st.session_state.get("min_rating", 1):
                        cols = st.columns([8, 1])
                        with cols[0]:
                            st.markdown(f"• **{item.get('title', 'Untitled')}**")
                            if item.get('date'):
                                st.caption(f"📅 {item.get('date')}")
                        with cols[1]:
                            if rating:
                                if int(rating) >= 4:
                                    st.markdown(f"🔥 **{rating}/5**")
                                else:
                                    st.markdown(f"⭐ {rating}/5")
        
        st.divider()

def manage_urls_tab(url_db):
    """Display and manage URLs."""
    st.header("🔗 Hantera URL:er")
    
    # Get current URLs
    urls = url_db.get_urls()
    
    # Add new URL form
    with st.expander("➕ Lägg till ny URL", expanded=False):
        with st.form("add_url_form"):
            new_url = st.text_input("URL", placeholder="https://exempel.se/nyheter")
            new_name = st.text_input("Namn", placeholder="Exempel Nyheter")
            new_category = st.selectbox("Kategori", [
                "municipality", "housing", "sports", "culture", "police", "community", "other"
            ])
            
            col1, col2 = st.columns([1, 3])
            with col1:
                submit = st.form_submit_button("Lägg till", use_container_width=True)
            
            if submit:
                if not new_url or not new_name:
                    st.error("Både URL och namn måste anges")
                else:
                    success = url_db.add_url(new_url, new_name, new_category)
                    if success:
                        st.success(f"URL tillagd: {new_name}")
                        # Force reload URLs
                        urls = url_db.get_urls()
                    else:
                        st.error("Kunde inte lägga till URL")
    
    # Convert to DataFrame for display
    if urls:
        df = pd.DataFrame(urls)
        df = df[["name", "url", "category"]]  # Ensure consistent columns and order
        
        # Create editable dataframe
        st.subheader("Befintliga URL:er")
        
        edited_df = st.data_editor(
            df,
            column_config={
                "name": st.column_config.TextColumn("Namn"),
                "url": st.column_config.LinkColumn("URL"),
                "category": st.column_config.SelectboxColumn(
                    "Kategori", 
                    options=["municipality", "housing", "sports", "culture", "police", "community", "other"]
                ),
            },
            hide_index=True,
            num_rows="dynamic",
            key="url_editor"
        )
        
        # Check for changes in the dataframe
        if not df.equals(edited_df):
            st.info("⚠️ Du har gjort ändringar som inte är sparade än.")
            if st.button("Spara ändringar", key="save_url_changes"):
                try:
                    # Find changes
                    for i, row in edited_df.iterrows():
                        old_url = df.iloc[i]["url"] if i < len(df) else None
                        new_data = {
                            "url": row["url"],
                            "name": row["name"],
                            "category": row["category"]
                        }
                        
                        if old_url and old_url != row["url"]:
                            # URL was changed
                            url_db.update_url(old_url, new_data)
                        elif old_url is None:
                            # New row added
                            url_db.add_url(row["url"], row["name"], row["category"])
                    
                    # Check for deletions
                    for i, row in df.iterrows():
                        if i >= len(edited_df) or not any(edited_df["url"] == row["url"]):
                            # Row was deleted
                            url_db.remove_url(row["url"])
                    
                    st.success("Ändringar sparade!")
                    # Force reload URLs
                    urls = url_db.get_urls()
                except Exception as e:
                    st.error(f"Fel vid sparande: {str(e)}")
        
        # Sync options
        st.subheader("Synkronisering")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Synka från lokal fil till Supabase", key="sync_to_supabase"):
                success = url_db.sync_to_supabase()
                if success:
                    st.success("Synkat till Supabase!")
                else:
                    st.error("Kunde inte synka till Supabase")
        with col2:
            if st.button("Synka från Supabase till lokal fil", key="sync_from_supabase"):
                success = url_db.sync_from_supabase()
                if success:
                    st.success("Synkat från Supabase!")
                else:
                    st.error("Kunde inte synka från Supabase")
    else:
        st.warning("Inga URL:er hittades")

def main():
    """Main function to run the Streamlit app."""
    try:
        # Try to initialize Supabase
        supabase = init_supabase()
        st.session_state["supabase_initialized"] = True
    except Exception as e:
        supabase = None
        st.session_state["supabase_initialized"] = False
        if "supabase_error_shown" not in st.session_state:
            st.error(f"Failed to initialize Supabase: {e}")
            st.session_state["supabase_error_shown"] = True

    # Initialize databases and monitor
    monitor = init_monitor(_supabase=supabase)
    url_db = init_url_db(_supabase=supabase)
    
    # Header
    st.title("🤖 Mitti AI - Nyhetsövervakning")
    st.markdown("Övervaka och analysera svenska nyhetssajter med AI")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Inställningar")
        
        min_rating = st.slider(
            "Lägsta betyg att visa",
            min_value=1,
            max_value=5,
            value=1,
            help="Visa endast nyheter med detta betyg eller högre"
        )
        st.session_state["min_rating"] = min_rating
        
        st.divider()
        
        # Analysis controls
        st.header("🔄 Kör analys")
        
        if st.button("🚀 Starta analys", type="primary", use_container_width=True):
            st.session_state["running"] = True
            st.session_state["results"] = []
        
        if st.session_state.get("running", False):
            st.info("⏳ Analysen körs...")
            st.progress(0.0)
    
    # Main content area
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dagens analys", "📈 Historik", "🔗 URL:er", "ℹ️ Om"])
    
    with tab1:
        if st.session_state.get("running", False):
            # Run analysis
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_container = st.container()
            
            try:
                urls = monitor.url_manager.get_urls()
                total_urls = len(urls)
                results = []
                
                for i, url_info in enumerate(urls):
                    progress = (i + 1) / total_urls
                    progress_bar.progress(progress)
                    status_text.text(f"Analyserar {i+1}/{total_urls}: {url_info.get('name', url_info.get('url'))}")
                    
                    # Run analysis
                    result = monitor.monitor_url(url_info)
                    results.append(result)
                    
                    # Display result immediately
                    with results_container:
                        display_analysis_card(result)
                
                # Save to Supabase is now handled in the ContentMonitor class
                
                # Update session state
                st.session_state["results"] = results
                st.session_state["running"] = False
                st.session_state["last_run"] = datetime.now()
                
                # Summary
                analyzed_count = len([r for r in results if r.get("status") == "analyzed"])
                high_interest_count = sum(
                    len([item for item in r.get("analysis", {}).get("extracted_news", []) 
                         if item.get("rating") is not None and int(item.get("rating", 0)) >= 3])
                    for r in results if r.get("status") == "analyzed"
                )
                
                st.success(f"""
                ✅ Analys klar! 
                - {analyzed_count} sajter analyserade
                - {high_interest_count} högintressanta nyheter (betyg 3+)
                """)
                
            except Exception as e:
                st.error(f"Fel under analys: {str(e)}")
                st.session_state["running"] = False
        
        elif st.session_state.get("results"):
            # Display saved results
            st.info(f"Senaste analys: {st.session_state.get('last_run', 'Unknown').strftime('%Y-%m-%d %H:%M') if isinstance(st.session_state.get('last_run'), datetime) else 'Unknown'}")
            
            for result in st.session_state.get("results", []):
                display_analysis_card(result)
        else:
            st.info("👈 Klicka på 'Starta analys' i sidopanelen för att börja")
    
    with tab2:
        st.header("📈 Historisk data")
        
        if supabase:
            # Time range selector
            time_range = st.radio("Tidsperiod", [1, 7, 30], format_func=lambda x: f"{x} {'dag' if x == 1 else 'dagar'}", horizontal=True)
            
            # Load historical data
            with st.spinner("Laddar historisk data..."):
                historical_data = load_recent_analyses(supabase, time_range)
            
            if historical_data:
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                
                total_analyses = len(historical_data)
                with col1:
                    st.metric("Totalt antal analyser", total_analyses)
                
                # Count high interest items (rating >= 3)
                high_interest_count = 0
                for analysis in historical_data:
                    news_items = analysis.get("news_items", [])
                    high_interest_count += len([item for item in news_items if item.get("rating") is not None and int(item.get("rating", 0)) >= 3])
                
                with col2:
                    st.metric("Högintressanta nyheter", high_interest_count)
                
                # Calculate average rating
                total_ratings = 0
                rating_count = 0
                for analysis in historical_data:
                    if analysis.get("overall_rating"):
                        total_ratings += analysis.get("overall_rating", 0)
                        rating_count += 1
                
                avg_rating = total_ratings / rating_count if rating_count > 0 else 0
                
                with col3:
                    st.metric("Genomsnittligt betyg", f"{avg_rating:.1f}/5")
                
                # Display historical analyses
                st.subheader("Tidigare analyser")
                
                for analysis in historical_data:
                    with st.expander(f"{analysis.get('site_name')} - {analysis.get('analyzed_at')[:10]}", expanded=False):
                        st.write(f"**URL:** {analysis.get('url')}")
                        st.write(f"**Betyg:** {analysis.get('overall_rating')}/5")
                        st.write(f"**Analys:**")
                        st.write(analysis.get('analysis_text', 'Ingen analys tillgänglig'))
                        
                        # Show news items
                        news_items = analysis.get("news_items", [])
                        if news_items:
                            st.write("**Nyheter:**")
                            for item in news_items:
                                rating = item.get("rating")
                                if rating is not None and int(rating) >= st.session_state.get("min_rating", 1):
                                    cols = st.columns([8, 1])
                                    with cols[0]:
                                        st.write(f"• **{item.get('title', 'Untitled')}**")
                                        if item.get('date'):
                                            st.caption(f"📅 {item.get('date')}")
                                    with cols[1]:
                                        if rating:
                                            if rating >= 4:
                                                st.write(f"🔥 **{rating}/5**")
                                            else:
                                                st.write(f"⭐ {rating}/5")
            else:
                st.info("Ingen historisk data hittad för den valda tidsperioden")
        else:
            st.warning("⚠️ Supabase-anslutning saknas. Historisk data är inte tillgänglig.")
            st.info("För att aktivera historik, konfigurera Supabase-anslutningen i .streamlit/secrets.toml")
    
    with tab3:
        manage_urls_tab(url_db)
    
    with tab4:
        st.header("ℹ️ Om Mitti AI")
        
        st.write("""
        **Mitti AI** är ett verktyg för att övervaka och analysera svenska nyhetssajter med AI.
        
        ### Hur det fungerar
        1. Verktyget besöker varje URL i listan
        2. Jämför innehållet med föregående besök
        3. Om ändringar hittas, analyseras de med OpenAI
        4. Resultaten visas i realtid i dashboarden
        
        ### Betygsskala
        - **1/5**: Rutininformation utan nyhetsvärde
        - **2/5**: Lågprioriterad nyhet med begränsat intresse
        - **3/5**: Standardnyhet med visst allmänintresse
        - **4/5**: Viktig nyhet med högt allmänintresse
        - **5/5**: Mycket viktig nyhet med stort allmänintresse
        
        ### Teknisk information
        - **OpenAI API**: Används för innehållsanalys
        - **Firecrawl API**: Används för webbskrapning
        - **Supabase**: Datalagring för analyser och URL:er
        - **Streamlit**: Webbgränssnitt
        """)
        
        # Check for missing API keys
        try:
            config = ConfigManager("backend/config.json")
            
            missing_keys = []
            if not config.get("firecrawl_api_key") or config.get("firecrawl_api_key").startswith("your_"):
                missing_keys.append("Firecrawl API key")
            
            if not config.get("openai_api_key") or config.get("openai_api_key").startswith("your_"):
                missing_keys.append("OpenAI API key")
            
            if not config.get("openai_assistant_id") or config.get("openai_assistant_id").startswith("your_"):
                missing_keys.append("OpenAI Assistant ID")
            
            if missing_keys:
                st.warning(f"⚠️ Saknade API-nycklar: {', '.join(missing_keys)}")
                st.info("Uppdatera backend/config.json med dina API-nycklar för att aktivera alla funktioner.")
        except Exception as e:
            st.error(f"Fel vid kontroll av konfiguration: {str(e)}")

if __name__ == "__main__":
    # Initialize session state if needed
    if "running" not in st.session_state:
        st.session_state["running"] = False
    
    if "results" not in st.session_state:
        st.session_state["results"] = []
    
    if "min_rating" not in st.session_state:
        st.session_state["min_rating"] = 1
    
    main()