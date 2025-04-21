"""
Module for handling microscope computer interface and file detection.
"""

import os
import logging
from pathlib import Path
from typing import Optional, List
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class MicroscopeInterface:
    """Interface for microscope computer operations."""
    
    def __init__(self, watch_directory: str, log_file: str):
        """
        Initialize the microscope interface.
        
        Args:
            watch_directory: Directory to watch for new files
            log_file: Path to the log file
        """
        self.watch_directory = Path(watch_directory)
        self.log_file = Path(log_file)
        self._ensure_log_file()
        
        if not self.watch_directory.exists():
            raise ValueError(f"Watch directory {watch_directory} does not exist")
    
    def _ensure_log_file(self) -> None:
        """Ensure the log file exists and is properly formatted."""
        if not self.log_file.exists():
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_file, 'w') as f:
                json.dump({"processed_files": []}, f)
    
    def _load_processed_files(self) -> List[str]:
        """Load the list of processed files from the log."""
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
                return data.get("processed_files", [])
        except Exception as e:
            logger.error(f"Failed to load processed files: {e}")
            return []
    
    def _save_processed_file(self, file_path: str) -> None:
        """Save a processed file to the log."""
        try:
            processed_files = self._load_processed_files()
            processed_files.append({
                "path": file_path,
                "processed_at": datetime.now().isoformat()
            })
            
            with open(self.log_file, 'w') as f:
                json.dump({"processed_files": processed_files}, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save processed file: {e}")
    
    def get_new_files(self) -> List[Path]:
        """
        Get new files that haven't been processed yet.
        
        Returns:
            List of paths to new files
        """
        processed_files = self._load_processed_files()
        processed_paths = {item["path"] for item in processed_files}
        
        new_files = []
        for file_path in self.watch_directory.rglob("*"):
            if file_path.is_file() and str(file_path) not in processed_paths:
                new_files.append(file_path)
                
        return new_files
    
    def mark_file_processed(self, file_path: Path) -> None:
        """
        Mark a file as processed in the log.
        
        Args:
            file_path: Path to the processed file
        """
        self._save_processed_file(str(file_path)) 