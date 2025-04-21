"""
Configuration module for the system.
"""

from pathlib import Path
from typing import Dict, Any

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
    Load configuration from file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dictionary containing configuration
    """
    # TODO: Implement actual configuration loading
    return DEFAULT_CONFIG 