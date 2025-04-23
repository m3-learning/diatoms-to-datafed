"""
Configuration module for the system.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default configuration
DEFAULT_CONFIG: Dict[str, Any] = {
    "watch_directory": "/path/to/watch",
    "log_file": "logs/processed_files.json",
    "datafed": {
        "repo_id": "repository-id",
        "parent_collection": "root",
        "default_tags": ["microscope", "volume"]
    },
    "logging": {
        "level": "INFO",
        "file": "logs/diatoms_to_datafed.log",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }
}

def load_config(config_path: Path) -> Dict[str, Any]:
    """
    Load configuration from file and environment variables.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dictionary containing configuration
    """
    # Load from YAML file
    config = DEFAULT_CONFIG.copy()
    if config_path.exists():
        with open(config_path, 'r') as f:
            yaml_config = yaml.safe_load(f)
            if yaml_config:
                config.update(yaml_config)
    
    # Override with environment variables
    config = _apply_env_vars(config)
    
    return config

def _apply_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply environment variables to override configuration.
    
    Args:
        config: Current configuration dictionary
        
    Returns:
        Updated configuration dictionary
    """
    # Top level variables
    if os.getenv("WATCH_DIRECTORY"):
        config["watch_directory"] = os.getenv("WATCH_DIRECTORY")
    
    if os.getenv("LOG_FILE"):
        config["log_file"] = os.getenv("LOG_FILE")
    
    # DataFed configuration
    if os.getenv("DATAFED_REPO_ID"):
        config["datafed"]["repo_id"] = os.getenv("DATAFED_REPO_ID")
    
    if os.getenv("DATAFED_PARENT_COLLECTION"):
        config["datafed"]["parent_collection"] = os.getenv("DATAFED_PARENT_COLLECTION")
    
    # Logging configuration
    if os.getenv("LOG_LEVEL"):
        config["logging"]["level"] = os.getenv("LOG_LEVEL")
    
    if os.getenv("LOG_CONSOLE_LEVEL"):
        config["logging"]["console_level"] = os.getenv("LOG_CONSOLE_LEVEL")
    
    if os.getenv("LOG_FORMAT"):
        config["logging"]["format"] = os.getenv("LOG_FORMAT")
    
    if os.getenv("LOG_MAX_SIZE"):
        try:
            config["logging"]["max_size"] = int(os.getenv("LOG_MAX_SIZE", "0"))
        except ValueError:
            pass
    
    if os.getenv("LOG_BACKUP_COUNT"):
        try:
            config["logging"]["backup_count"] = int(os.getenv("LOG_BACKUP_COUNT", "0"))
        except ValueError:
            pass
    
    return config

def save_config(config: Dict[str, Any], config_path: Path) -> None:
    """
    Save configuration to YAML file.
    
    Args:
        config: Configuration dictionary
        config_path: Path to save configuration file
    """
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False) 