"""
Configuration Management Module
Handles application settings and configuration persistence
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    """Manages application configuration settings"""
    
    DEFAULT_CONFIG = {
        "save_directory": str(Path.home() / "Pictures"),
        "file_prefix": "screenshot",
        "file_format": "png",
        "hotkey_fullscreen": "print_screen",
        "hotkey_region": "ctrl+print_screen",
        "show_preview": True,
        "auto_open_folder": False,
        "window_geometry": "400x300+100+100",
        "timestamp_format": "%Y%m%d_%H%M%S"
    }
    
    def __init__(self, config_file: str = "screenshot_config.json"):
        """
        Initialize configuration manager
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.config = self.DEFAULT_CONFIG.copy()
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Update config with loaded values, keeping defaults for missing keys
                    self.config.update(loaded_config)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config: {e}. Using defaults.")
    
    def save_config(self) -> None:
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except IOError as e:
            print(f"Error saving config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value
        
        Args:
            key: Configuration key
            value: Value to set
        """
        self.config[key] = value
        self.save_config()
    
    def update(self, updates: Dict[str, Any]) -> None:
        """
        Update multiple configuration values
        
        Args:
            updates: Dictionary of updates
        """
        self.config.update(updates)
        self.save_config()
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values"""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save_config()