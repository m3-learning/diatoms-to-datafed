"""
Test script to run the service without package installation.
"""

import sys
import os
from pathlib import Path
import subprocess
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

# Import the necessary modules
from diatoms_to_datafed.config import load_config
from diatoms_to_datafed.orchestrator import Orchestrator

def setup_logging():
    """Set up comprehensive logging to both console and file."""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Get log level from environment or use DEBUG as default
    log_level_str = os.getenv("LOG_LEVEL", "DEBUG")
    numeric_level = getattr(logging, log_level_str.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.DEBUG
    
    # Configure root logger to capture everything
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all logs
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create and configure file handler for all logs
    log_file = log_dir / "diatoms_to_datafed_detailed.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)  # Capture all logs
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Create and configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)  # Use configured level for console
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Log startup information
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized at level {log_level_str}")
    logger.debug("Debug logging is enabled")
    
    return logger

def check_datafed_auth():
    """Check if DataFed is authenticated and provide instructions if not."""
    try:
        # Try to run datafed auth status command
        result = subprocess.run(['datafed', 'auth', 'status'], 
                              capture_output=True, 
                              text=True)
        
        if "Not authenticated" in result.stdout:
            print("\nDataFed authentication required!")
            print("Please run the following commands:")
            print("1. datafed auth login")
            print("2. Enter your DataFed credentials when prompted")
            print("\nAfter authenticating, run this script again.")
            return False
        return True
    except FileNotFoundError:
        print("\nDataFed CLI not found!")
        print("Please install DataFed CLI first:")
        print("pip install datafed")
        return False

def get_env_config():
    """Get configuration from environment variables."""
    config = {
        "watch_directory": os.getenv("WATCH_DIRECTORY"),
        "log_file": os.getenv("LOG_FILE"),
        "datafed": {
            "repo_id": os.getenv("DATAFED_REPO_ID"),
        }
    }
    
    # Validate required settings
    missing = []
    if not config["watch_directory"]:
        missing.append("WATCH_DIRECTORY")
    if not config["log_file"]:
        missing.append("LOG_FILE")
    if not config["datafed"]["repo_id"]:
        missing.append("DATAFED_REPO_ID")
        
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}")
        print("Please check your .env file")
        return None
        
    return config

def main():
    logger = setup_logging()
    logger.info("Starting diatoms-to-datafed test run")
    
    # Check DataFed authentication first
    if not check_datafed_auth():
        return 1
    
    try:
        # Try to get config from environment variables
        config = get_env_config()
        if not config:
            # Fall back to config file if env vars are missing
            logger.info("Falling back to config.yaml for configuration")
            config_path = Path("config.yaml")
            config = load_config(config_path)
        
        # Initialize orchestrator
        orchestrator = Orchestrator(
            watch_directory=config["watch_directory"],
            log_file=config["log_file"],
            datafed_config=config["datafed"]
        )
        
        # Run a single processing cycle
        logger.info("Starting test run...")
        orchestrator.process_new_files()
        logger.info("Test run completed!")
        
    except Exception as e:
        logger.error(f"Error during test run: {e}", exc_info=True)
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main()) 