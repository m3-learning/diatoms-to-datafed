"""
Main entry point for the application.
"""

import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from .config import load_config
from .orchestrator import Orchestrator

def setup_logging(config: dict) -> logging.Logger:
    """
    Set up comprehensive logging to both console and file.
    
    Args:
        config: Dictionary containing logging configuration
    
    Returns:
        Logger instance
    """
    # Create logs directory if it doesn't exist
    log_file = Path(config["logging"]["file"])
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Get log level
    log_level_str = config["logging"]["level"]
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
        config["logging"]["format"] + ' - %(filename)s:%(lineno)d'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # File handler for normal logs
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # File handler for debug logs
    debug_log_file = log_file.parent / "debug.log"
    debug_file_handler = logging.FileHandler(debug_log_file)
    debug_file_handler.setLevel(logging.DEBUG)
    debug_file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(debug_file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Get logger for this module
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized at level {log_level_str}")
    logger.debug("Debug logging is enabled")
    
    return logger

def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code
    """
    try:
        # Load configuration
        config_path = Path(os.getenv("CONFIG_FILE", "config.yaml"))
        config = load_config(config_path)
        
        # Set up logging
        logger = setup_logging(config)
        logger.info("Starting diatoms-to-datafed service")
        
        # Initialize orchestrator
        orchestrator = Orchestrator(
            watch_directory=config["watch_directory"],
            log_file=config["log_file"],
            datafed_config=config["datafed"]
        )
        
        # Start daily job
        logger.info("Starting daily job scheduler")
        orchestrator.run_daily_job()
        
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main()) 