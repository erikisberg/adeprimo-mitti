"""
Configuration management for Mitti Scraper - Fixed to ignore environment variables
"""

import os
import json
from typing import Dict, Any

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
                logger.info(f"Configuration loaded from {self.config_path}")
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            raise
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in configuration file: {self.config_path}")
            raise
        
        # Log what we're using (without exposing full keys)
        if config.get("openai_api_key"):
            key = config["openai_api_key"]
            logger.info(f"Using OpenAI API key from config.json: {key[:8]}...{key[-8:]}")
        
        return config
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)