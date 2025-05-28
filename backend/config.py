"""
Configuration management for Mitti Scraper - Updated to also use Streamlit secrets
"""

import os
import json
from typing import Dict, Any

from utils import logger

# Try to import streamlit for secrets
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

class ConfigManager:
    """Handles configuration management for the application."""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize with configuration file path."""
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load configuration from file and/or Streamlit secrets."""
        config = {}
        
        # First try to load from Streamlit secrets if available
        if HAS_STREAMLIT:
            # Map Streamlit secrets to config keys
            secrets_mapping = {
                "OPENAI_API_KEY": "openai_api_key",
                "OPENAI_ASSISTANT_ID": "openai_assistant_id",
                "FIRECRAWL_API_KEY": "firecrawl_api_key",
                "SLACK_WEBHOOK_URL": "slack_webhook_url",
                "RESEND_API_KEY": "resend_api_key",
                "RESEND_AUDIENCE_ID": "resend_audience_id"
            }
            
            for secret_key, config_key in secrets_mapping.items():
                if hasattr(st, 'secrets') and secret_key in st.secrets:
                    if config_key in config and '.' in config_key:
                        # Handle nested config like notifications.slack.webhook_url
                        parts = config_key.split('.')
                        if len(parts) == 2:
                            if parts[0] not in config:
                                config[parts[0]] = {}
                            config[parts[0]][parts[1]] = st.secrets[secret_key]
                        elif len(parts) == 3:
                            if parts[0] not in config:
                                config[parts[0]] = {}
                            if parts[1] not in config[parts[0]]:
                                config[parts[0]][parts[1]] = {}
                            config[parts[0]][parts[1]][parts[2]] = st.secrets[secret_key]
                    else:
                        # Simple top-level config
                        config[config_key] = st.secrets[secret_key]
                        logger.info(f"Using {config_key} from Streamlit secrets")
            
            # Get other config values that don't have direct mapping
            if hasattr(st, 'secrets') and "URL_LIST_PATH" in st.secrets:
                config["url_list_path"] = st.secrets["URL_LIST_PATH"]
            if hasattr(st, 'secrets') and "SIMILARITY_THRESHOLD" in st.secrets:
                config["similarity_threshold"] = float(st.secrets["SIMILARITY_THRESHOLD"])
        
        # Then try to load from file and merge
        try:
            with open(self.config_path, 'r') as f:
                file_config = json.load(f)
                # Merge file config with secrets (secrets take precedence)
                for key, value in file_config.items():
                    if key not in config:  # Only add if not already from secrets
                        config[key] = value
                logger.info(f"Configuration loaded from {self.config_path}")
        except FileNotFoundError:
            logger.warning(f"Configuration file not found: {self.config_path}")
            if not HAS_STREAMLIT or not config:
                # Only raise if we don't have Streamlit secrets or no config was loaded
                logger.error("No configuration source available!")
                raise
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in configuration file: {self.config_path}")
            if not HAS_STREAMLIT or not config:
                # Only raise if we don't have Streamlit secrets or no config was loaded
                raise
        
        # Log what we're using (without exposing full keys)
        if config.get("openai_api_key"):
            key = config["openai_api_key"]
            logger.info(f"Using OpenAI API key: {key[:8]}...{key[-8:]}")
        
        return config
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)