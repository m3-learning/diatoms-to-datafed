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
    """Set up basic logging configuration."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
        
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

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
        logger.error(f"Error during test run: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main()) 