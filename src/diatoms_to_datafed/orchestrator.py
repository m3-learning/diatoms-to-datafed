"""
Main orchestrator module that coordinates all components of the system.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import schedule
import time
from datetime import datetime

from .microscope import MicroscopeInterface
from .datafed import DataFedManager

logger = logging.getLogger(__name__)

class Orchestrator:
    """Coordinates all components of the system."""
    
    def __init__(
        self,
        watch_directory: str,
        log_file: str,
        datafed_config: Dict[str, Any]
    ):
        """
        Initialize the orchestrator with all required components.
        
        Args:
            watch_directory: Directory to watch for new files
            log_file: Path to the log file
            datafed_config: Configuration for DataFed
        """
        self.microscope = MicroscopeInterface(watch_directory, log_file)
        self.datafed = DataFedManager(datafed_config)
        
    def process_new_files(self) -> None:
        """Process all new files in the watch directory."""
        try:
            new_files = self.microscope.get_new_files()
            if not new_files:
                logger.info("No new files to process")
                return
                
            logger.info(f"Found {len(new_files)} new files to process")
            
            for file_path in new_files:
                try:
                    # Extract metadata
                    metadata = self._extract_metadata(file_path)
                    
                    # Create data record in DataFed
                    data_id = self.datafed.create_data_record(
                        title=file_path.name,
                        metadata=metadata
                    )
                    if not data_id:
                        logger.error(f"Failed to create data record for {file_path}")
                        continue
                        
                    # Upload data to DataFed
                    task_id = self.datafed.upload_data(data_id, file_path)
                    if not task_id:
                        logger.error(f"Failed to upload {file_path}")
                        continue
                        
                    # Mark file as processed
                    self.microscope.mark_file_processed(file_path)
                    logger.info(f"Successfully processed {file_path}")
                    
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in process_new_files: {e}")
            
    def _extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from the file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary containing metadata
        """
        return {
            "source": str(file_path),
            "size": file_path.stat().st_size,
            "timestamp": file_path.stat().st_mtime,
            "processed_at": datetime.now().isoformat()
        }
        
    def run_daily_job(self) -> None:
        """Run the daily processing job at midnight."""
        schedule.every().day.at("00:00").do(self.process_new_files)
        
        logger.info("Starting daily job scheduler")
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying 