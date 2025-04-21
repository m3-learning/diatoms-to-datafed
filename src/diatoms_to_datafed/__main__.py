"""
Main entry point for the application.
"""

import logging
import sys
from pathlib import Path

from .config import load_config
from .orchestrator import Orchestrator

def setup_logging(config: dict) -> None:
    """
    Set up logging configuration.
    
    Args:
        config: Dictionary containing logging configuration
    """
    logging_config = config["logging"]
    level = getattr(logging, logging_config["level"])
    
    # Create logs directory if it doesn't exist
    log_file = Path(logging_config["file"])
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=level,
        format=logging_config["format"],
        filename=logging_config["file"]
    )

def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code
    """
    try:
        # Load configuration
        config_path = Path("config.yaml")  # TODO: Make configurable
        config = load_config(config_path)
        
        # Set up logging
        setup_logging(config)
        logger = logging.getLogger(__name__)
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
        logging.error(f"Fatal error: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main()) 