"""
Configuration management for Mitti Scraper
"""

import os
import json
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from utils import logger

class ConfigManager:
    """Handles configuration management for the application."""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize with configuration file path."""
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load configuration from file."""
        config = {}
        
        # Try to load from file
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            logger.warning(f"Configuration file not found: {self.config_path}. Will use environment variables.")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in configuration file: {self.config_path}")
            raise
        
        # Override with environment variables if available
        env_mappings = {
            "FIRECRAWL_API_KEY": "firecrawl_api_key",
            "OPENAI_API_KEY": "openai_api_key",
            "OPENAI_ASSISTANT_ID": "openai_assistant_id",
            "SIMILARITY_THRESHOLD": "similarity_threshold"
        }
        
        for env_var, config_key in env_mappings.items():
            env_value = os.environ.get(env_var)
            if env_value:
                # Convert to appropriate type for specific keys
                if config_key == "similarity_threshold":
                    try:
                        config[config_key] = float(env_value)
                    except ValueError:
                        logger.warning(f"Invalid value for {env_var}: {env_value}. Using default.")
                else:
                    config[config_key] = env_value
        
        return config
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)