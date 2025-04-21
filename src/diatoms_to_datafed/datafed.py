"""
Module for handling DataFed repository operations using the official DataFed API.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datafed.CommandLib import API

logger = logging.getLogger(__name__)

class DataFedManager:
    """Manages DataFed operations using the official API."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the DataFed manager.
        
        Args:
            config: Dictionary containing DataFed configuration
        """
        self.api = API()
        self.repo_id = config.get("repo_id", "default")
        
    def create_data_record(
        self,
        title: str,
        metadata: Dict[str, Any],
        parent_id: str = "root",
        alias: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Create a new data record in DataFed.
        
        Args:
            title: Title of the record
            metadata: Dictionary containing metadata
            parent_id: ID of parent collection
            alias: Optional alias for the record
            description: Optional description
            tags: Optional list of tags
            
        Returns:
            Data ID if successful, None otherwise
        """
        try:
            response = self.api.dataCreate(
                title=title,
                alias=alias,
                description=description,
                tags=tags,
                metadata=metadata,
                parent_id=parent_id,
                repo_id=self.repo_id
            )
            return response.data_id
        except Exception as e:
            logger.error(f"Failed to create data record: {e}")
            return None
            
    def upload_data(self, data_id: str, file_path: Path) -> Optional[str]:
        """
        Upload data to a DataFed record.
        
        Args:
            data_id: ID of the data record
            file_path: Path to the file to upload
            
        Returns:
            Task ID if successful, None otherwise
        """
        try:
            response = self.api.dataPut(
                data_id=data_id,
                file_path=str(file_path)
            )
            return response.task_id
        except Exception as e:
            logger.error(f"Failed to upload data: {e}")
            return None
            
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a task.
        
        Args:
            task_id: ID of the task to check
            
        Returns:
            Dictionary containing task status information
        """
        try:
            response = self.api.taskView(task_id=task_id)
            return {
                "status": response.status,
                "bytes_transferred": response.bytes_transferred,
                "total_bytes": response.total_bytes,
                "error": response.error if hasattr(response, "error") else None
            }
        except Exception as e:
            logger.error(f"Failed to get task status: {e}")
            return None 